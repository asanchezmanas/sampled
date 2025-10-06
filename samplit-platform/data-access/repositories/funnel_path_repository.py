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
