# orchestration/services/ads_optimizer_service.py

import logging
import numpy as np
from typing import Dict, Any, List
from data_access.database import DatabaseManager
from engine.state.encryption import get_encryptor

logger = logging.getLogger(__name__)

class AdsOptimizerService:
    """
    Servicio de optimización de ADS
    Versión simplificada para MVP
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.encryptor = get_encryptor()
    
    async def optimize_campaign(self, campaign: Dict):
        """Optimizar una campaña"""
        
        campaign_id = campaign['id']
        logger.info(f"Optimizing campaign: {campaign['name']}")
        
        # 1. Get creatives
        creatives = await self.get_campaign_creatives(campaign_id)
        
        if not creatives:
            logger.warning(f"No creatives found for campaign {campaign_id}")
            return
        
        # 2. Update algorithm states
        for creative in creatives:
            await self.update_creative_state(creative, campaign)
        
        # 3. Make decisions
        await self.make_optimization_decisions(campaign, creatives)
    
    async def get_campaign_creatives(self, campaign_id: str) -> List[Dict]:
        """Obtener creatives de campaña"""
        
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM ad_creatives
                WHERE campaign_id = $1
                """,
                campaign_id
            )
        
        creatives = []
        for row in rows:
            creative = dict(row)
            
            # Decrypt algorithm state
            if creative['algorithm_state']:
                creative['algorithm_state_decrypted'] = (
                    self.encryptor.decrypt_state(creative['algorithm_state'])
                )
            else:
                creative['algorithm_state_decrypted'] = {
                    'success_count': 1,
                    'failure_count': 1,
                    'samples': 0
                }
            
            creatives.append(creative)
        
        return creatives
    
    async def update_creative_state(self, creative: Dict, campaign: Dict):
        """Actualizar estado del algoritmo para un creative"""
        
        state = creative['algorithm_state_decrypted']
        
        # Update Thompson Sampling parameters
        # success = conversions, failures = impressions - conversions
        new_successes = creative['conversions']
        new_failures = creative['impressions'] - creative['conversions']
        
        state['success_count'] = 1 + new_successes  # Prior + observed
        state['failure_count'] = 1 + new_failures
        state['samples'] = creative['impressions']
        
        # Encrypt and save
        encrypted = self.encryptor.encrypt_state(state)
        
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE ad_creatives
                SET algorithm_state = $1
                WHERE id = $2
                """,
                encrypted,
                creative['id']
            )
    
    async def make_optimization_decisions(
        self,
        campaign: Dict,
        creatives: List[Dict]
    ):
        """Tomar decisiones de optimización"""
        
        # Check if we have enough data
        total_samples = sum(c['impressions'] for c in creatives)
        min_samples = campaign['min_samples_per_creative'] * len(creatives)
        
        if total_samples < min_samples:
            logger.info(f"Not enough data: {total_samples}/{min_samples} samples")
            return
        
        # Calculate Thompson Sampling probabilities
        probabilities = self.calculate_probabilities(creatives)
        
        logger.info(f"Thompson probabilities: {probabilities}")
        
        # Find best creative
        best_id = max(probabilities, key=probabilities.get)
        best_prob = probabilities[best_id]
        
        # Decision: Pause losers if clear winner
        if best_prob > campaign['confidence_threshold']:
            if campaign['auto_pause_losers']:
                for creative_id, prob in probabilities.items():
                    if prob < 0.05 and creative_id != best_id:
                        await self.pause_creative(creative_id, campaign)
        
        # Decision: Scale winner
        if campaign['auto_scale_winners']:
            if best_prob > 0.7:
                await self.scale_winner_budget(best_id, campaign)
    
    def calculate_probabilities(self, creatives: List[Dict]) -> Dict[str, float]:
        """Calcular Thompson Sampling probabilities"""
        
        samples = 10000
        creative_samples = {}
        
        # Sample from Beta distribution
        for creative in creatives:
            state = creative['algorithm_state_decrypted']
            alpha = state['success_count']
            beta = state['failure_count']
            
            creative_samples[creative['id']] = np.random.beta(alpha, beta, samples)
        
        # Count how often each is best
        probabilities = {}
        for creative_id in creative_samples:
            is_best = sum(
                1 for i in range(samples)
                if creative_samples[creative_id][i] == max(
                    creative_samples[cid][i] for cid in creative_samples
                )
            )
            probabilities[creative_id] = is_best / samples
        
        return probabilities
    
    async def pause_creative(self, creative_id: str, campaign: Dict):
        """Pausar creative underperformer"""
        
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE ad_creatives SET status = 'paused' WHERE id = $1",
                creative_id
            )
        
        logger.info(f"Paused creative: {creative_id}")
    
    async def scale_winner_budget(self, creative_id: str, campaign: Dict):
        """Escalar presupuesto del winner"""
        
        current_budget = campaign['daily_budget']
        new_budget = current_budget * 1.5
        max_budget = campaign['original_daily_budget'] * 3
        
        new_budget = min(new_budget, max_budget)
        
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE ad_campaigns
                SET daily_budget = $1
                WHERE id = $2
                """,
                new_budget,
                campaign['id']
            )
        
        logger.info(f"Scaled budget: ${current_budget} → ${new_budget}")
