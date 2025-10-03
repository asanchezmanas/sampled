# backend/database-old.py
import os
import asyncpg
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from utils import Logger

class DatabaseManager:
    """
    PostgreSQL database manager for MVP
    Simple but robust with proper connection pooling
    """
    
    def __init__(self):
        self.logger = Logger()
        self.pool = None
        self.database_url = os.environ.get("DATABASE_URL")
        
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
    
    async def initialize(self):
        """Initialize connection pool and create tables"""
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                max_queries=50000,
                max_inactive_connection_lifetime=300,
                command_timeout=60
            )
            
            # Create tables if they don't exist
            await self._create_tables()
            
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.logger.info("Database connection pool closed")
    
    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            self.logger.error(f"Database health check failed: {str(e)}")
            return False
    
    async def _create_tables(self):
        """Create all necessary tables"""
        
        schema = """
        -- Enable UUID extension
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Experiments table
        CREATE TABLE IF NOT EXISTS experiments (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'draft',
            config JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            started_at TIMESTAMP WITH TIME ZONE,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            CONSTRAINT valid_status CHECK (status IN ('draft', 'active', 'paused', 'completed'))
        );
        
        -- Arms table
        CREATE TABLE IF NOT EXISTS arms (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            content JSONB DEFAULT '{}',
            is_active BOOLEAN DEFAULT true,
            
            -- Thompson Sampling parameters
            alpha DECIMAL(10,4) DEFAULT 1.0,
            beta DECIMAL(10,4) DEFAULT 1.0,
            
            -- Cached metrics for performance
            assignments INTEGER DEFAULT 0,
            conversions INTEGER DEFAULT 0,
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            UNIQUE(experiment_id, name)
        );
        
        -- User assignments table
        CREATE TABLE IF NOT EXISTS assignments (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
            arm_id UUID NOT NULL REFERENCES arms(id) ON DELETE CASCADE,
            user_id VARCHAR(255) NOT NULL,
            session_id VARCHAR(255),
            context JSONB DEFAULT '{}',
            assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            converted_at TIMESTAMP WITH TIME ZONE,
            conversion_value DECIMAL(10,2) DEFAULT 0,
            
            -- Prevent duplicate assignments
            UNIQUE(experiment_id, user_id)
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_experiments_user_id ON experiments(user_id);
        CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);
        CREATE INDEX IF NOT EXISTS idx_arms_experiment_id ON arms(experiment_id);
        CREATE INDEX IF NOT EXISTS idx_assignments_experiment_user ON assignments(experiment_id, user_id);
        CREATE INDEX IF NOT EXISTS idx_assignments_converted ON assignments(converted_at) WHERE converted_at IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_assignments_arm_id ON assignments(arm_id);
        
        -- Updated timestamp triggers
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        DROP TRIGGER IF EXISTS update_experiments_updated_at ON experiments;
        CREATE TRIGGER update_experiments_updated_at 
            BEFORE UPDATE ON experiments 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            
        DROP TRIGGER IF EXISTS update_arms_updated_at ON arms;
        CREATE TRIGGER update_arms_updated_at 
            BEFORE UPDATE ON arms 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(schema)
        
        self.logger.info("Database tables created/verified")
    
    # ===== USER OPERATIONS =====
    
    async def create_user(self, email: str, password_hash: str, name: str) -> str:
        """Create new user"""
        async with self.pool.acquire() as conn:
            user_id = await conn.fetchval(
                """
                INSERT INTO users (email, password_hash, name) 
                VALUES ($1, $2, $3) 
                RETURNING id
                """,
                email, password_hash, name
            )
        return str(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, password_hash, name, created_at FROM users WHERE email = $1",
                email
            )
        return dict(row) if row else None
    
    # ===== EXPERIMENT OPERATIONS =====
    
    async def create_experiment(
        self, 
        user_id: str, 
        name: str, 
        description: str = None,
        config: Dict[str, Any] = None
    ) -> str:
        """Create new experiment"""
        async with self.pool.acquire() as conn:
            experiment_id = await conn.fetchval(
                """
                INSERT INTO experiments (user_id, name, description, config) 
                VALUES ($1, $2, $3, $4) 
                RETURNING id
                """,
                user_id, name, description, json.dumps(config or {})
            )
        return str(experiment_id)
    
    async def get_user_experiments(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all experiments for user with basic stats"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    e.id,
                    e.name,
                    e.description,
                    e.status,
                    e.created_at,
                    e.started_at,
                    COUNT(a.id) as arms_count,
                    COALESCE(SUM(a.assignments), 0) as total_users,
                    CASE 
                        WHEN COALESCE(SUM(a.assignments), 0) > 0 
                        THEN COALESCE(SUM(a.conversions), 0)::FLOAT / COALESCE(SUM(a.assignments), 1)::FLOAT
                        ELSE 0
                    END as conversion_rate
                FROM experiments e
                LEFT JOIN arms a ON e.id = a.experiment_id
                WHERE e.user_id = $1
                GROUP BY e.id, e.name, e.description, e.status, e.created_at, e.started_at
                ORDER BY e.created_at DESC
                """,
                user_id
            )
        
        return [dict(row) for row in rows]
    
    async def get_experiment_with_arms(self, experiment_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment with all arms"""
        async with self.pool.acquire() as conn:
            # Get experiment
            exp_row = await conn.fetchrow(
                """
                SELECT id, name, description, status, created_at, started_at, config
                FROM experiments 
                WHERE id = $1 AND user_id = $2
                """,
                experiment_id, user_id
            )
            
            if not exp_row:
                return None
            
            # Get arms
            arm_rows = await conn.fetch(
                """
                SELECT 
                    id, name, description, content, is_active,
                    alpha, beta, assignments, conversions,
                    CASE 
                        WHEN assignments > 0 
                        THEN conversions::FLOAT / assignments::FLOAT
                        ELSE 0
                    END as conversion_rate
                FROM arms 
                WHERE experiment_id = $1
                ORDER BY created_at
                """,
                experiment_id
            )
            
            experiment = dict(exp_row)
            experiment['arms'] = [dict(row) for row in arm_rows]
            
            return experiment
    
    async def get_experiment_public(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment for public API (no user restriction)"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, status, config FROM experiments WHERE id = $1",
                experiment_id
            )
        return dict(row) if row else None
    
    async def update_experiment_status(self, experiment_id: str, user_id: str, status: str) -> None:
        """Update experiment status"""
        async with self.pool.acquire() as conn:
            started_at = datetime.now(timezone.utc) if status == 'active' else None
            
            await conn.execute(
                """
                UPDATE experiments 
                SET status = $1, started_at = COALESCE(started_at, $2)
                WHERE id = $3 AND user_id = $4
                """,
                status, started_at, experiment_id, user_id
            )
    
    async def get_active_experiments_for_domain(self, domain: str = None) -> List[Dict[str, Any]]:
        """Get active experiments for GTM integration"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name, config
                FROM experiments 
                WHERE status = 'active'
                ORDER BY created_at DESC
                LIMIT 100
                """
            )
        return [dict(row) for row in rows]
    
    # ===== ARM OPERATIONS =====
    
    async def create_arm(
        self, 
        experiment_id: str, 
        name: str, 
        description: str = None,
        content: Dict[str, Any] = None
    ) -> str:
        """Create new arm"""
        async with self.pool.acquire() as conn:
            arm_id = await conn.fetchval(
                """
                INSERT INTO arms (experiment_id, name, description, content) 
                VALUES ($1, $2, $3, $4) 
                RETURNING id
                """,
                experiment_id, name, description, json.dumps(content or {})
            )
        return str(arm_id)
    
    async def get_experiment_arms_with_stats(self, experiment_id: str) -> List[Dict[str, Any]]:
        """Get arms with Thompson Sampling stats"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    id, name, description, content, is_active,
                    alpha, beta, assignments, conversions,
                    CASE 
                        WHEN assignments > 0 
                        THEN conversions::FLOAT / assignments::FLOAT
                        ELSE 0
                    END as conversion_rate
                FROM arms 
                WHERE experiment_id = $1 AND is_active = true
                ORDER BY created_at
                """,
                experiment_id
            )
        return [dict(row) for row in rows]
    
    async def get_arm_content(self, arm_id: str) -> Dict[str, Any]:
        """Get arm content"""
        async with self.pool.acquire() as conn:
            content = await conn.fetchval(
                "SELECT content FROM arms WHERE id = $1",
                arm_id
            )
        return content or {}
    
    async def increment_arm_assignments(self, arm_id: str) -> None:
        """Increment assignment count"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE arms SET assignments = assignments + 1 WHERE id = $1",
                arm_id
            )
    
    async def increment_arm_conversions(self, arm_id: str) -> None:
        """Increment conversion count"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE arms SET conversions = conversions + 1 WHERE id = $1",
                arm_id
            )
    
    async def increment_arm_alpha(self, arm_id: str) -> None:
        """Increment alpha (Thompson Sampling success)"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE arms SET alpha = alpha + 1 WHERE id = $1",
                arm_id
            )
    
    async def increment_arm_beta(self, arm_id: str) -> None:
        """Increment beta (Thompson Sampling failure)"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE arms SET beta = beta + 1 WHERE id = $1",
                arm_id
            )
    
    # ===== ASSIGNMENT OPERATIONS =====
    
    async def get_user_assignment(self, experiment_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get existing assignment for user"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, arm_id, assigned_at, converted_at, conversion_value
                FROM assignments 
                WHERE experiment_id = $1 AND user_id = $2
                """,
                experiment_id, user_id
            )
        return dict(row) if row else None
    
    async def create_assignment(
        self, 
        experiment_id: str, 
        arm_id: str, 
        user_id: str,
        session_id: str = None,
        context: Dict[str, Any] = None
    ) -> str:
        """Create new assignment"""
        async with self.pool.acquire() as conn:
            assignment_id = await conn.fetchval(
                """
                INSERT INTO assignments (experiment_id, arm_id, user_id, session_id, context) 
                VALUES ($1, $2, $3, $4, $5) 
                RETURNING id
                """,
                experiment_id, arm_id, user_id, session_id, json.dumps(context or {})
            )
        return str(assignment_id)
    
    async def record_conversion(
        self, 
        assignment_id: str, 
        conversion_value: float = 1.0,
        metadata: Dict[str, Any] = None
    ) -> None:
        """Record conversion for assignment"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE assignments 
                SET converted_at = NOW(), conversion_value = $2
                WHERE id = $1 AND converted_at IS NULL
                """,
                assignment_id, conversion_value
            )
    
    # ===== ANALYTICS OPERATIONS =====
    
    async def get_experiment_analytics(self, experiment_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive experiment analytics"""
        async with self.pool.acquire() as conn:
            # Get experiment basic info
            exp_row = await conn.fetchrow(
                """
                SELECT id, name, description, status, created_at, started_at, config
                FROM experiments 
                WHERE id = $1 AND user_id = $2
                """,
                experiment_id, user_id
            )
            
            if not exp_row:
                return None
            
            # Get arms with detailed statistics
            arm_rows = await conn.fetch(
                """
                SELECT 
                    a.id,
                    a.name,
                    a.description,
                    a.content,
                    a.alpha,
                    a.beta,
                    a.assignments,
                    a.conversions,
                    CASE 
                        WHEN a.assignments > 0 
                        THEN a.conversions::FLOAT / a.assignments::FLOAT
                        ELSE 0
                    END as conversion_rate,
                    
                    -- Time-based metrics
                    COUNT(CASE WHEN ass.converted_at IS NOT NULL THEN 1 END) as actual_conversions,
                    AVG(CASE WHEN ass.converted_at IS NOT NULL THEN ass.conversion_value END) as avg_conversion_value,
                    
                    -- Recent performance (last 24 hours)
                    COUNT(CASE WHEN ass.assigned_at > NOW() - INTERVAL '24 hours' THEN 1 END) as assignments_24h,
                    COUNT(CASE WHEN ass.converted_at > NOW() - INTERVAL '24 hours' THEN 1 END) as conversions_24h
                    
                FROM arms a
                LEFT JOIN assignments ass ON a.id = ass.arm_id
                WHERE a.experiment_id = $1
                GROUP BY a.id, a.name, a.description, a.content, a.alpha, a.beta, a.assignments, a.conversions
                ORDER BY a.created_at
                """,
                experiment_id
            )
            
            experiment = dict(exp_row)
            experiment['arms'] = [dict(row) for row in arm_rows]
            
            return experiment
    
    # ===== UTILITY OPERATIONS =====
    
    async def cleanup_old_assignments(self, days: int = 90) -> int:
        """Clean up old assignments for GDPR compliance"""
        async with self.pool.acquire() as conn:
            deleted_count = await conn.fetchval(
                """
                DELETE FROM assignments 
                WHERE assigned_at < NOW() - INTERVAL '%s days'
                RETURNING (SELECT COUNT(*) FROM assignments 
                          WHERE assigned_at < NOW() - INTERVAL '%s days')
                """,
                days, days
            )
        
        self.logger.info(f"Cleaned up {deleted_count} old assignments")
        return deleted_count or 0
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow(
                """
                SELECT 
                    (SELECT COUNT(*) FROM users) as total_users,
                    (SELECT COUNT(*) FROM experiments) as total_experiments,
                    (SELECT COUNT(*) FROM experiments WHERE status = 'active') as active_experiments,
                    (SELECT COUNT(*) FROM arms) as total_arms,
                    (SELECT COUNT(*) FROM assignments) as total_assignments,
                    (SELECT COUNT(*) FROM assignments WHERE converted_at IS NOT NULL) as total_conversions
                """
            )
        
        return dict(stats) if stats else {}
