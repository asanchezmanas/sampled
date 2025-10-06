# data-access/repositories/funnel_path_repository.py

import hashlib
from typing import List, Dict, Any, Optional
from .base_repository import BaseRepository

class FunnelPathRepository(BaseRepository):
    """
    Repository for funnel path performance
    
    ⚠️  CRITICAL: This stores our competitive advantage
    
    We store which COMBINATIONS of variants work best,
    which is our secret sauce for funnel optimization.
    """
    
    def _hash_path(self, variant_ids: List[str]) -> str:
        """
        Create hash of path for privacy
        
        We don't want variant IDs visible in plaintext
        """
        path_string = "->".join(sorted(variant_ids))
        return hashlib.sha256(path_string.encode()).hexdigest()
    
    async def get_or_create_path_performance(self,
                                            funnel_id: str,
                                            variant_path: List[str]) -> Dict[str, Any]:
        """
        Get performance data for specific path
        
        Args:
            variant_path: ["variant1_id", "variant2_id", "variant3_id"]
        
        Returns:
            Performance data with decrypted state
        """
        
        path_hash = self._hash_path(variant_path)
        
        async with self.db.acquire() as conn:
            # Check if exists
            row = await conn.fetchrow(
                """
                SELECT 
                    id, path_hash, path_data,
                    attempts, conversions, conversion_rate,
                    optimization_state, last_seen
                FROM funnel_path_performance
                WHERE funnel_id = $
                WHERE funnel_id = $1 AND path_hash = $2
                """,
                funnel_id,
                path_hash
            )
            
            if row:
                # Decrypt path data
                decrypted_path = self.encryptor.decrypt_path_data(row['path_data'])
                
                # Decrypt optimization state
                if row['optimization_state']:
                    opt_state = self._decrypt_algorithm_state(row['optimization_state'])
                else:
                    opt_state = self._initialize_path_state()
                
                return {
                    'id': str(row['id']),
                    'path': decrypted_path,
                    'attempts': row['attempts'],
                    'conversions': row['conversions'],
                    'conversion_rate': float(row['conversion_rate']),
                    'optimization_state': opt_state,
                    'last_seen': row['last_seen']
                }
            
            # Create new path entry
            encrypted_path = self.encryptor.encrypt_path_data(variant_path)
            initial_state = self._initialize_path_state()
            encrypted_state = self._encrypt_algorithm_state(initial_state)
            
            path_id = await conn.fetchval(
                """
                INSERT INTO funnel_path_performance (
                    funnel_id, path_hash, path_data, 
                    optimization_state
                ) VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                funnel_id,
                path_hash,
                encrypted_path,
                encrypted_state
            )
            
            return {
                'id': str(path_id),
                'path': variant_path,
                'attempts': 0,
                'conversions': 0,
                'conversion_rate': 0.0,
                'optimization_state': initial_state
            }
    
    def _initialize_path_state(self) -> Dict[str, Any]:
        """
        Initialize algorithm state for new path
        
        This is Thompson Sampling state pero ofuscado
        """
        return {
            'success_count': 1,  # Prior (no llamarlo "alpha")
            'failure_count': 1,  # Prior (no llamarlo "beta")
            'samples': 0,
            'last_updated': None
        }
    
    async def update_path_performance(self,
                                     path_id: str,
                                     converted: bool,
                                     new_optimization_state: Dict[str, Any]) -> None:
        """
        Update path performance after completion
        
        This is called when a user completes (or abandons) a funnel
        """
        
        # Encrypt new state
        encrypted_state = self._encrypt_algorithm_state(new_optimization_state)
        
        async with self.db.acquire() as conn:
            if converted:
                await conn.execute(
                    """
                    UPDATE funnel_path_performance
                    SET 
                        attempts = attempts + 1,
                        conversions = conversions + 1,
                        conversion_rate = (conversions + 1)::DECIMAL / (attempts + 1)::DECIMAL,
                        optimization_state = $1,
                        last_seen = NOW()
                    WHERE id = $2
                    """,
                    encrypted_state,
                    path_id
                )
            else:
                await conn.execute(
                    """
                    UPDATE funnel_path_performance
                    SET 
                        attempts = attempts + 1,
                        conversion_rate = conversions::DECIMAL / (attempts + 1)::DECIMAL,
                        optimization_state = $1,
                        last_seen = NOW()
                    WHERE id = $2
                    """,
                    encrypted_state,
                    path_id
                )
    
    async def get_top_performing_paths(self,
                                      funnel_id: str,
                                      min_samples: int = 10,
                                      limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing paths for funnel
        
        Returns decrypted paths sorted by performance
        """
        
        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    id, path_data, 
                    attempts, conversions, conversion_rate,
                    last_seen
                FROM funnel_path_performance
                WHERE 
                    funnel_id = $1 
                    AND attempts >= $2
                ORDER BY conversion_rate DESC, attempts DESC
                LIMIT $3
                """,
                funnel_id,
                min_samples,
                limit
            )
        
        results = []
        for row in rows:
            # Decrypt path
            decrypted_path = self.encryptor.decrypt_path_data(row['path_data'])
            
            results.append({
                'path': decrypted_path,
                'attempts': row['attempts'],
                'conversions': row['conversions'],
                'conversion_rate': float(row['conversion_rate']),
                'last_seen': row['last_seen']
            })
        
        return results
    
    async def get_path_statistics(self, funnel_id: str) -> Dict[str, Any]:
        """
        Get aggregate statistics for funnel paths
        
        Public-safe statistics (no algorithm details)
        """
        
        async with self.db.acquire() as conn:
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_paths,
                    SUM(attempts) as total_attempts,
                    SUM(conversions) as total_conversions,
                    AVG(conversion_rate) as avg_conversion_rate,
                    MAX(conversion_rate) as best_conversion_rate
                FROM funnel_path_performance
                WHERE funnel_id = $1
                """,
                funnel_id
            )
        
        return dict(stats) if stats else {}
