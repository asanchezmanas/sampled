
# data-access/database.py

import os
import asyncpg
from typing import Optional
from contextlib import asynccontextmanager

class DatabaseManager:
    """
    Supabase/PostgreSQL connection manager
    
    Handles:
    - Connection pooling
    - Service role access (for encrypted state)
    - Row Level Security bypass where needed
    """
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        
        # Supabase connection strings
        self.database_url = os.environ.get("SUPABASE_DB_URL")
        self.service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.database_url:
            raise ValueError("SUPABASE_DB_URL not set")
    
    async def initialize(self):
        """Initialize connection pool"""
        
        # Parse Supabase URL
        if "supabase.co" in self.database_url:
            if self.database_url.startswith("postgres://"):
                self.database_url = self.database_url.replace(
                    "postgres://", 
                    "postgresql://", 
                    1
                )
        
        # Create pool
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10,
            max_queries=50000,
            max_inactive_connection_lifetime=300,
            command_timeout=60,
            ssl='require' if 'supabase.co' in self.database_url else None,
            server_settings={
                # Use service role to bypass RLS for backend operations
                'request.jwt.claims': '{"role":"service_role"}',
            }
        )
        
        print("✅ Database pool initialized")
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            print("✅ Database pool closed")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool"""
        async with self.pool.acquire() as connection:
            yield connection
    
    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            print(f"❌ Database health check failed: {e}")
            return False

# Global instance
_db_manager: Optional[DatabaseManager] = None

async def get_database() -> DatabaseManager:
    """Get database manager singleton"""
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
    
    return _db_manager
