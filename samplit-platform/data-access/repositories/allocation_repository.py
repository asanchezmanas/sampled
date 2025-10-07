# data-access/repositories/allocation_repository.py

from typing import Optional, Dict, Any, List
from .base_repository import BaseRepository
import json
from datetime import datetime, timezone

class AllocationRepository(BaseRepository):
    """Repository for user allocations"""
    
    async def get_allocation(
        self, 
        experiment_id: str, 
        user_identifier: str
    ) -> Optional[Dict[str, Any]]:
        """Get existing allocation for user"""
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    id, experiment_id, variant_id, user_identifier,
                    session_id, context, allocated_at, converted_at,
                    conversion_value, metadata
                FROM allocations 
                WHERE experiment_id = $1 AND user_identifier = $2
                """,
                experiment_id, user_identifier
            )
        
        if not row:
            return None
        
        allocation = dict(row)
        
        # Parse JSON fields
        if allocation.get('context'):
            if isinstance(allocation['context'], str):
                allocation['context'] = json.loads(allocation['context'])
        
        if allocation.get('metadata'):
            if isinstance(allocation['metadata'], str):
                allocation['metadata'] = json.loads(allocation['metadata'])
        
        return allocation
    
    async def create_allocation(
        self,
        experiment_id: str,
        variant_id: str,
        user_identifier: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create new allocation"""
        async with self.db.acquire() as conn:
            allocation_id = await conn.fetchval(
                """
                INSERT INTO allocations 
                (experiment_id, variant_id, user_identifier, session_id, context)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                experiment_id,
                variant_id,
                user_identifier,
                session_id,
                json.dumps(context or {})
            )
        
        return str(allocation_id)
    
    async def record_conversion(
        self,
        allocation_id: str,
        conversion_value: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record conversion for allocation"""
        async with self.db.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE allocations 
                SET 
                    converted_at = NOW(),
                    conversion_value = $2,
                    metadata = COALESCE(metadata, '{}'::jsonb) || $3::jsonb
                WHERE id = $1 AND converted_at IS NULL
                """,
                allocation_id,
                conversion_value,
                json.dumps(metadata or {})
            )
        
        return result == 'UPDATE 1'
    
    async def get_experiment_allocations(
        self,
        experiment_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get recent allocations for experiment"""
        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    a.id, a.variant_id, a.user_identifier,
                    a.allocated_at, a.converted_at, a.conversion_value,
                    v.name as variant_name
                FROM allocations a
                JOIN variants v ON a.variant_id = v.id
                WHERE a.experiment_id = $1
                ORDER BY a.allocated_at DESC
                LIMIT $2 OFFSET $3
                """,
                experiment_id, limit, offset
            )
        
        return [dict(row) for row in rows]
    
    async def get_conversion_timeline(
        self,
        experiment_id: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get conversion timeline for last N hours"""
        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    DATE_TRUNC('hour', allocated_at) as hour,
                    COUNT(*) as allocations,
                    COUNT(converted_at) as conversions,
                    CASE 
                        WHEN COUNT(*) > 0 
                        THEN COUNT(converted_at)::FLOAT / COUNT(*)::FLOAT
                        ELSE 0
                    END as conversion_rate
                FROM allocations
                WHERE 
                    experiment_id = $1 
                    AND allocated_at >= NOW() - INTERVAL '1 hour' * $2
                GROUP BY DATE_TRUNC('hour', allocated_at)
                ORDER BY hour DESC
                """,
                experiment_id, hours
            )
        
        return [dict(row) for row in rows]
    
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get allocation by ID"""
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM allocations WHERE id = $1",
                id
            )
        
        return dict(row) if row else None
    
    async def create(self, data: Dict[str, Any]) -> str:
        """Generic create (for base class)"""
        return await self.create_allocation(
            experiment_id=data['experiment_id'],
            variant_id=data['variant_id'],
            user_identifier=data['user_identifier'],
            session_id=data.get('session_id'),
            context=data.get('context')
        )
    
    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """Update allocation"""
        if 'conversion_value' in data:
            return await self.record_conversion(
                allocation_id=id,
                conversion_value=data['conversion_value'],
                metadata=data.get('metadata')
            )
        return False
