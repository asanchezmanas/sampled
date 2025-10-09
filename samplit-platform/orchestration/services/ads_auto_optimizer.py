# orchestration/services/ads_auto_optimizer.py

import asyncio
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AdsAutoOptimizer:
    """
    Servicio que corre continuamente optimizando ads
    
    Workflow:
    1. Cada X horas, pull métricas de Meta/Google
    2. Actualizar estados del algoritmo Thompson Sampling
    3. Tomar decisiones:
       - Pausar underperformers
       - Aumentar presupuesto a winners
       - Crear nuevas variantes si es necesario
    """
    
    def __init__(
        self,
        db: DatabaseManager,
        meta_integration: MetaAdsIntegration,
        google_integration: GoogleAdsIntegration
    ):
        self.db = db
        self.meta = meta_integration
        self.google = google_integration
        self.optimizer = OptimizerFactory.create(
            OptimizationStrategy.ADAPTIVE
        )
        self.running = False
    
    async def start(self):
        """Iniciar loop de optimización"""
        self.running = True
        logger.info("🤖 Ads Auto Optimizer started")
        
        while self.running:
            try:
                await self.optimization_cycle()
                
                # Esperar 1 hora antes del próximo ciclo
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Optimization cycle failed: {e}", exc_info=True)
                await asyncio.sleep(300)  # Retry en 5 min
    
    async def optimization_cycle(self):
        """Un ciclo completo de optimización"""
        logger.info("Starting optimization cycle...")
        
        # Obtener campañas activas
        campaigns = await self.db.get_active_ad_campaigns()
        
        for campaign in campaigns:
            try:
                await self.optimize_campaign(campaign)
            except Exception as e:
                logger.error(
                    f"Failed to optimize campaign {campaign['id']}: {e}"
                )
        
        logger.info(f"Optimization cycle completed. {len(campaigns)} campaigns processed.")
    
    async def optimize_campaign(self, campaign: Dict):
        """Optimizar una campaña específica"""
        campaign_id = campaign['id']
        platform = campaign['platform']
        
        logger.info(f"Optimizing campaign {campaign_id} on {platform}")
        
        # 1. Pull latest metrics
        creatives = await self.db.get_campaign_creatives(campaign_id)
        
        for creative in creatives:
            # Get metrics from platform
            if platform == 'meta':
                metrics = await self.meta.get_ad_insights(
                    creative['platform_ad_id']
                )
            elif platform == 'google':
                metrics = await self.google.get_ad_performance(
                    creative['platform_ad_id']
                )
            else:
                continue
            
            # 2. Update algorithm state
            # Calculate reward based on campaign objective
            reward = self._calculate_reward(
                metrics=metrics,
                objective=campaign['campaign_objective']
            )
            
            await self.optimizer.update(
                option_id=creative['id'],
                reward=reward,
                context={}
            )
            
            # 3. Update DB with new metrics
            await self.db.update_creative_metrics(
                creative_id=creative['id'],
                metrics=metrics
            )
        
        # 4. Make optimization decisions
        await self.make_optimization_decisions(campaign, creatives)
    
    def _calculate_reward(
        self,
        metrics: Dict,
        objective: str
    ) -> float:
        """
        Calcular reward basado en el objetivo de campaña
        
        Objectives:
        - 'conversions': reward = conversions / impressions
        - 'traffic': reward = clicks / impressions (CTR)
        - 'awareness': reward = impressions (normalized)
        """
        
        if objective == 'conversions':
            conversions = metrics.get('conversions', 0)
            impressions = metrics.get('impressions', 1)
            return conversions / impressions if impressions > 0 else 0
        
        elif objective == 'traffic':
            clicks = metrics.get('clicks', 0)
            impressions = metrics.get('impressions', 1)
            return clicks / impressions if impressions > 0 else 0
        
        elif objective == 'awareness':
            # Normalize impressions to 0-1 range
            impressions = metrics.get('impressions', 0)
            return min(impressions / 10000, 1.0)
        
        else:
            # Default: CTR
            clicks = metrics.get('clicks', 0)
            impressions = metrics.get('impressions', 1)
            return clicks / impressions if impressions > 0 else 0
    
    async def make_optimization_decisions(
        self,
        campaign: Dict,
        creatives: List[Dict]
    ):
        """
        Tomar decisiones de optimización
        
        Reglas:
        1. Si un creative tiene >500 impressions y CTR < 0.5%, pausarlo
        2. Si un creative tiene CTR > 2% y conversiones, darle más budget
        3. Si todos los creatives tienen <100 impressions, mantener
        """
        
        if not creatives:
            return
        
        # Calcular métricas agregadas
        total_impressions = sum(c.get('impressions', 0) for c in creatives)
        
        if total_impressions < 500:
            # Aún muy temprano para optimizar
            logger.info(f"Campaign {campaign['id']}: Not enough data yet")
            return
        
        # Identificar winners y losers
        winners = []
        losers = []
        
        for creative in creatives:
            impressions = creative.get('impressions', 0)
            ctr = creative.get('ctr', 0)
            conversions = creative.get('conversions', 0)
            
            # Underperformer
            if impressions > 500 and ctr < 0.005:  # <0.5% CTR
                losers.append(creative)
            
            # Winner
            elif impressions > 100 and ctr > 0.02:  # >2% CTR
                winners.append(creative)
        
        # Ejecutar acciones
        for loser in losers:
            logger.info(f"Pausing underperformer: {loser['id']}")
            await self._pause_creative(campaign['platform'], loser)
        
        for winner in winners:
            logger.info(f"Boosting winner: {winner['id']}")
            await self._boost_creative_budget(campaign['platform'], winner)
    
    async def _pause_creative(self, platform: str, creative: Dict):
        """Pausar creative underperformer"""
        if platform == 'meta':
            await self.meta.pause_ad(creative['platform_ad_id'])
        elif platform == 'google':
            await self.google.update_ad_status(
                creative['platform_ad_id'],
                'PAUSED'
            )
        
        # Update DB
        await self.db.update_creative_status(creative['id'], 'paused')
    
    async def _boost_creative_budget(self, platform: str, creative: Dict):
        """Aumentar presupuesto de creative winner"""
        # Get current adset budget
        current_budget = await self.db.get_creative_budget(creative['id'])
        
        # Increase by 20%
        new_budget = int(current_budget * 1.2)
        
        if platform == 'meta':
            await self.meta.update_ad_budget(
                creative['platform_adset_id'],
                new_budget
            )
        # Google Ads usa automated bidding, no manual budget per ad
        
        # Update DB
        await self.db.update_creative_budget(creative['id'], new_budget)
    
    def stop(self):
        """Detener el optimizer"""
        self.running = False
        logger.info("🛑 Ads Auto Optimizer stopped")
