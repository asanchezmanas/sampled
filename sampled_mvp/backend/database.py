# backend/database.py
import os
import asyncpg
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from utils import Logger

class DatabaseManager:
    """
    PostgreSQL Database Manager para Supabase
    Versión UNIFICADA - soporta Fase 1 y Fase 2 con métodos consolidados
    """
    
    def __init__(self):
        self.logger = Logger()
        self.pool = None
        self.database_url = os.environ.get("DATABASE_URL")
        
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Asegurar formato correcto para Supabase
        if "supabase.co" in self.database_url:
            if self.database_url.startswith("postgres://"):
                self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)
    
    async def initialize(self):
        """Initialize connection pool and create tables"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=5,
                max_queries=50000,
                max_inactive_connection_lifetime=300,
                command_timeout=60,
                ssl='require' if 'supabase.co' in self.database_url else None
            )
            
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
        """Create all tables - Schema unificado"""
        
        schema = """
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        
        -- Users
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Experiments (unificado - soporta ambas fases)
        CREATE TABLE IF NOT EXISTS experiments (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'draft',
            
            -- Configuración unificada (JSONB flexible)
            config JSONB DEFAULT '{}',
            
            -- Campos específicos comunes
            url VARCHAR(500),
            
            created_at TIMESTAMPTZ DEFAULT NOW(),
            started_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            
            CONSTRAINT valid_status CHECK (status IN ('draft', 'active', 'paused', 'completed'))
        );
        
        -- Arms (Fase 1 - variantes tradicionales)
        CREATE TABLE IF NOT EXISTS arms (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            content JSONB DEFAULT '{}',
            is_active BOOLEAN DEFAULT true,
            
            -- Thompson Sampling
            alpha DECIMAL(10,4) DEFAULT 1.0,
            beta DECIMAL(10,4) DEFAULT 1.0,
            assignments INTEGER DEFAULT 0,
            conversions INTEGER DEFAULT 0,
            
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            
            UNIQUE(experiment_id, name)
        );
        
        -- Assignments
        CREATE TABLE IF NOT EXISTS assignments (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
            arm_id UUID REFERENCES arms(id) ON DELETE CASCADE,
            user_id VARCHAR(255) NOT NULL,
            session_id VARCHAR(255),
            context JSONB DEFAULT '{}',
            assigned_at TIMESTAMPTZ DEFAULT NOW(),
            converted_at TIMESTAMPTZ,
            conversion_value DECIMAL(10,2) DEFAULT 0,
            
            UNIQUE(experiment_id, user_id)
        );
        
        -- Elements (Fase 2 - elementos individuales)
        CREATE TABLE IF NOT EXISTS experiment_elements (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
            element_order INTEGER NOT NULL DEFAULT 0,
            
            -- Selector
            selector_config JSONB NOT NULL,  -- Almacena toda la config del selector
            
            -- Tipo y contenido
            element_type VARCHAR(20) NOT NULL DEFAULT 'text',
            original_content JSONB NOT NULL DEFAULT '{}',
            variants JSONB NOT NULL DEFAULT '[]',
            
            -- Estabilidad
            stability_score INTEGER DEFAULT 50,
            stability_info JSONB DEFAULT '{}',
            
            -- Posición para preview
            position JSONB,
            
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            
            UNIQUE(experiment_id, element_order)
        );
        
        -- Targeting rules
        CREATE TABLE IF NOT EXISTS targeting_rules (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
            rules_config JSONB NOT NULL DEFAULT '{}',  -- Almacena toda la config
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Session analytics (Fase 2)
        CREATE TABLE IF NOT EXISTS session_analytics (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_id VARCHAR(255) NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
            
            variant_assignments JSONB DEFAULT '{}',
            metrics JSONB DEFAULT '{}',  -- page_load_time, time_on_page, scroll_depth
            device_info JSONB,
            
            session_start TIMESTAMPTZ DEFAULT NOW(),
            last_activity TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Element interactions
        CREATE TABLE IF NOT EXISTS element_interactions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_analytics_id UUID NOT NULL REFERENCES session_analytics(id) ON DELETE CASCADE,
            element_id UUID REFERENCES experiment_elements(id) ON DELETE CASCADE,
            
            interaction_type VARCHAR(50) NOT NULL,
            interaction_data JSONB DEFAULT '{}',  -- coordinates, metadata
            
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Micro conversions
        CREATE TABLE IF NOT EXISTS micro_conversions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_analytics_id UUID NOT NULL REFERENCES session_analytics(id) ON DELETE CASCADE,
            
            conversion_type VARCHAR(50) NOT NULL,
            value DECIMAL(10,2) DEFAULT 1.0,
            metadata JSONB DEFAULT '{}',
            
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Previews
        CREATE TABLE IF NOT EXISTS experiment_previews (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            
            preview_config JSONB NOT NULL DEFAULT '{}',  -- variant_selections, viewport
            screenshot_url VARCHAR(500),
            
            created_at TIMESTAMPTZ DEFAULT NOW(),
            expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '7 days'
        );
        
        -- Page analysis cache
        CREATE TABLE IF NOT EXISTS page_analysis (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            
            url VARCHAR(500) NOT NULL,
            analysis_data JSONB NOT NULL DEFAULT '{}',  -- title, elements, recommendations
            
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Índices
        CREATE INDEX IF NOT EXISTS idx_experiments_user_id ON experiments(user_id);
        CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);
        CREATE INDEX IF NOT EXISTS idx_arms_experiment_id ON arms(experiment_id);
        CREATE INDEX IF NOT EXISTS idx_assignments_exp_user ON assignments(experiment_id, user_id);
        CREATE INDEX IF NOT EXISTS idx_elements_experiment ON experiment_elements(experiment_id);
        CREATE INDEX IF NOT EXISTS idx_session_analytics_exp ON session_analytics(experiment_id);
        CREATE INDEX IF NOT EXISTS idx_interactions_session ON element_interactions(session_analytics_id);
        
        -- Triggers
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
        
        self.logger.info("Database schema created successfully")
    
    # ===== USER OPERATIONS =====
    
    async def create_user(self, email: str, password_hash: str, name: str) -> str:
        """Create new user"""
        async with self.pool.acquire() as conn:
            user_id = await conn.fetchval(
                "INSERT INTO users (email, password_hash, name) VALUES ($1, $2, $3) RETURNING id",
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
    
    # ===== EXPERIMENT OPERATIONS (UNIFICADO) =====
    
    async def create_experiment(
        self, 
        user_id: str, 
        name: str, 
        description: str = None,
        config: Dict[str, Any] = None,
        url: str = None,
        arms: List[Dict[str, Any]] = None,
        elements: List[Any] = None,  # ElementConfig objects
        targeting: Any = None  # TargetingConfig object
    ) -> Dict[str, Any]:
        """
        Crear experimento - UNIFICADO
        Soporta tanto Fase 1 (arms) como Fase 2 (elements)
        
        Returns: {'experiment_id': str, 'arm_ids': List[str], 'element_ids': List[str]}
        """
        async with self.pool.acquire() as conn:
            # Crear experimento base
            experiment_id = await conn.fetchval(
                """
                INSERT INTO experiments (user_id, name, description, config, url) 
                VALUES ($1, $2, $3, $4, $5) 
                RETURNING id
                """,
                user_id, name, description, json.dumps(config or {}), url
            )
            
            result = {
                'experiment_id': str(experiment_id),
                'arm_ids': [],
                'element_ids': []
            }
            
            # Fase 1: Crear arms si se proporcionaron
            if arms:
                for arm_data in arms:
                    arm_id = await conn.fetchval(
                        """
                        INSERT INTO arms (experiment_id, name, description, content) 
                        VALUES ($1, $2, $3, $4) 
                        RETURNING id
                        """,
                        experiment_id, 
                        arm_data.get('name'),
                        arm_data.get('description'),
                        json.dumps(arm_data.get('content', {}))
                    )
                    result['arm_ids'].append(str(arm_id))
            
            # Fase 2: Crear elements si se proporcionaron
            if elements:
                for idx, element in enumerate(elements):
                    element_id = await conn.fetchval(
                        """
                        INSERT INTO experiment_elements (
                            experiment_id, element_order, selector_config, 
                            element_type, original_content, variants, 
                            stability_score, stability_info, position
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        RETURNING id
                        """,
                        experiment_id, idx,
                        json.dumps({
                            'primary': {
                                'type': element.selector.primary.type.value,
                                'selector': element.selector.primary.selector,
                                'specificity': element.selector.primary.specificity
                            },
                            'fallbacks': [
                                {
                                    'type': fb.type.value,
                                    'selector': fb.selector,
                                    'specificity': fb.specificity
                                } for fb in element.selector.fallbacks
                            ],
                            'xpath': element.selector.xpath
                        }),
                        element.element_type.value,
                        json.dumps(element.original_content),
                        json.dumps([{
                            'type': v.type,
                            'value': v.value,
                            'attributes': v.attributes,
                            'styles': v.styles
                        } for v in element.variants]),
                        element.stability.score if element.stability else 50,
                        json.dumps({
                            'factors': element.stability.factors if element.stability else [],
                            'warnings': element.stability.warnings if element.stability else [],
                            'recommendations': element.stability.recommendations if element.stability else []
                        }),
                        json.dumps({
                            'x': element.position.x,
                            'y': element.position.y,
                            'width': element.position.width,
                            'height': element.position.height,
                            'viewport_width': element.position.viewport_width,
                            'viewport_height': element.position.viewport_height
                        }) if element.position else None
                    )
                    result['element_ids'].append(str(element_id))
            
            # Guardar targeting si se proporciona
            if targeting and targeting.enabled:
                await conn.execute(
                    """
                    INSERT INTO targeting_rules (experiment_id, rules_config)
                    VALUES ($1, $2)
                    """,
                    experiment_id,
                    json.dumps({
                        'enabled': targeting.enabled,
                        'groups': [
                            {
                                'id': group.id,
                                'name': group.name,
                                'rules': [
                                    {
                                        'type': rule.type,
                                        'operator': rule.operator.value,
                                        'value': rule.value,
                                        'enabled': rule.enabled
                                    } for rule in group.rules
                                ]
                            } for group in targeting.groups
                        ],
                        'traffic_allocation': targeting.traffic_allocation
                    })
                )
        
        return result
    
    async def get_experiment(self, experiment_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener experimento - UNIFICADO
        Detecta automáticamente si es Fase 1 o Fase 2
        """
        async with self.pool.acquire() as conn:
            # Experimento base
            exp_row = await conn.fetchrow(
                "SELECT * FROM experiments WHERE id = $1 AND user_id = $2",
                experiment_id, user_id
            )
            
            if not exp_row:
                return None
            
            experiment = dict(exp_row)
            
            # Obtener arms (Fase 1)
            arm_rows = await conn.fetch(
                """
                SELECT 
                    id, name, description, content, is_active, alpha, beta, 
                    assignments, conversions,
                    CASE WHEN assignments > 0 THEN conversions::FLOAT / assignments::FLOAT ELSE 0 END as conversion_rate
                FROM arms 
                WHERE experiment_id = $1
                ORDER BY created_at
                """,
                experiment_id
            )
            experiment['arms'] = [dict(row) for row in arm_rows]
            
            # Obtener elements (Fase 2)
            element_rows = await conn.fetch(
                "SELECT * FROM experiment_elements WHERE experiment_id = $1 ORDER BY element_order",
                experiment_id
            )
            experiment['elements'] = [dict(row) for row in element_rows]
            
            # Obtener targeting
            targeting_row = await conn.fetchrow(
                "SELECT rules_config FROM targeting_rules WHERE experiment_id = $1",
                experiment_id
            )
            experiment['targeting'] = json.loads(targeting_row['rules_config']) if targeting_row else None
            
            # Determinar tipo
            experiment['experiment_type'] = 'multi_element' if experiment['elements'] else 'traditional'
            
            return experiment
    
    async def get_user_experiments(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all experiments for user"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    e.id, e.name, e.description, e.status, e.created_at, e.started_at, e.url,
                    COUNT(DISTINCT a.id) as arms_count,
                    COUNT(DISTINCT el.id) as elements_count,
                    COALESCE(SUM(a.assignments), 0) as total_users,
                    CASE 
                        WHEN COALESCE(SUM(a.assignments), 0) > 0 
                        THEN COALESCE(SUM(a.conversions), 0)::FLOAT / COALESCE(SUM(a.assignments), 1)::FLOAT
                        ELSE 0
                    END as conversion_rate
                FROM experiments e
                LEFT JOIN arms a ON e.id = a.experiment_id
                LEFT JOIN experiment_elements el ON e.id = el.experiment_id
                WHERE e.user_id = $1
                GROUP BY e.id
                ORDER BY e.created_at DESC
                """,
                user_id
            )
            
            experiments = []
            for row in rows:
                exp = dict(row)
                exp['experiment_type'] = 'multi_element' if exp['elements_count'] > 0 else 'traditional'
                experiments.append(exp)
            
            return experiments
    
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
    
    # ===== ARM OPERATIONS =====
    
    async def get_experiment_arms(self, experiment_id: str) -> List[Dict[str, Any]]:
        """Get arms with stats"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    id, name, description, content, is_active, alpha, beta, 
                    assignments, conversions,
                    CASE WHEN assignments > 0 THEN conversions::FLOAT / assignments::FLOAT ELSE 0 END as conversion_rate
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
            content = await conn.fetchval("SELECT content FROM arms WHERE id = $1", arm_id)
        return content or {}
    
    async def increment_arm_assignments(self, arm_id: str) -> None:
        """Increment assignment count"""
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE arms SET assignments = assignments + 1 WHERE id = $1", arm_id)
    
    async def increment_arm_conversions(self, arm_id: str) -> None:
        """Increment conversion count"""
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE arms SET conversions = conversions + 1 WHERE id = $1", arm_id)
    
    async def increment_arm_alpha(self, arm_id: str) -> None:
        """Increment alpha (success)"""
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE arms SET alpha = alpha + 1 WHERE id = $1", arm_id)
    
    async def increment_arm_beta(self, arm_id: str) -> None:
        """Increment beta (failure)"""
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE arms SET beta = beta + 1 WHERE id = $1", arm_id)
    
    # ===== ASSIGNMENT OPERATIONS =====
    
    async def get_user_assignment(self, experiment_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get existing assignment"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM assignments WHERE experiment_id = $1 AND user_id = $2",
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
        conversion_value: float = 1.0
    ) -> None:
        """Record conversion"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE assignments 
                SET converted_at = NOW(), conversion_value = $2
                WHERE id = $1 AND converted_at IS NULL
                """,
                assignment_id, conversion_value
            )
    
    # ===== ANALYTICS (UNIFICADO) =====
    
    async def get_experiment_analytics(self, experiment_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive analytics - works for both phases"""
        experiment = await self.get_experiment(experiment_id, user_id)
        if not experiment:
            return None
        
        async with self.pool.acquire() as conn:
            # Stats básicos
            if experiment['arms']:
                arm_stats = await conn.fetch(
                    """
                    SELECT 
                        a.*,
                        COUNT(CASE WHEN ass.converted_at IS NOT NULL THEN 1 END) as actual_conversions,
                        COUNT(CASE WHEN ass.assigned_at > NOW() - INTERVAL '24 hours' THEN 1 END) as assignments_24h
                    FROM arms a
                    LEFT JOIN assignments ass ON a.id = ass.arm_id
                    WHERE a.experiment_id = $1
                    GROUP BY a.id
                    """,
                    experiment_id
                )
                experiment['arms_stats'] = [dict(row) for row in arm_stats]
            
            # Stats de elementos (Fase 2)
            if experiment['elements']:
                element_stats = await conn.fetch(
                    """
                    SELECT 
                        el.id,
                        COUNT(DISTINCT ei.session_analytics_id) as interactions_count,
                        COUNT(DISTINCT ei.id) as total_interactions
                    FROM experiment_elements el
                    LEFT JOIN element_interactions ei ON el.id = ei.element_id
                    WHERE el.experiment_id = $1
                    GROUP BY el.id
                    """,
                    experiment_id
                )
                experiment['elements_stats'] = [dict(row) for row in element_stats]
        
        return experiment
    
    # ===== SESSION ANALYTICS (FASE 2) =====
    
    async def create_session_analytics(
        self,
        session_id: str,
        user_id: str,
        experiment_id: str,
        variant_assignments: Dict[str, str],
        device_info: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create session analytics"""
        async with self.pool.acquire() as conn:
            analytics_id = await conn.fetchval(
                """
                INSERT INTO session_analytics 
                (session_id, user_id, experiment_id, variant_assignments, device_info, metrics)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                session_id, user_id, experiment_id, 
                json.dumps(variant_assignments),
                json.dumps(device_info) if device_info else None,
                json.dumps(metrics) if metrics else None
            )
        return str(analytics_id)
    
    async def record_element_interaction(
        self,
        session_analytics_id: str,
        element_id: str,
        interaction_type: str,
        interaction_data: Dict[str, Any]
    ) -> None:
        """Record element interaction"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO element_interactions 
                (session_analytics_id, element_id, interaction_type, interaction_data)
                VALUES ($1, $2, $3, $4)
                """,
                session_analytics_id, element_id, interaction_type,
                json.dumps(interaction_data)
            )
    
    async def record_micro_conversion(
        self,
        session_analytics_id: str,
        conversion_type: str,
        value: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record micro conversion"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO micro_conversions 
                (session_analytics_id, conversion_type, value, metadata)
                VALUES ($1, $2, $3, $4)
                """,
                session_analytics_id, conversion_type, value,
                json.dumps(metadata) if metadata else None
            )
    
    # ===== PREVIEW & ANALYSIS =====
    
    async def create_preview(
        self,
        experiment_id: str,
        user_id: str,
        preview_config: Dict[str, Any]
    ) -> str:
        """Create preview"""
        async with self.pool.acquire() as conn:
            preview_id = await conn.fetchval(
                """
                INSERT INTO experiment_previews 
                (experiment_id, user_id, preview_config)
                VALUES ($1, $2, $3)
                RETURNING id
                """,
                experiment_id, user_id, json.dumps(preview_config)
            )
        return str(preview_id)
    
    async def save_page_analysis(
        self,
        user_id: str,
        url: str,
        analysis_data: Dict[str, Any]
    ) -> str:
        """Save page analysis"""
        async with self.pool.acquire() as conn:
            analysis_id = await conn.fetchval(
                """
                INSERT INTO page_analysis (user_id, url, analysis_data)
                VALUES ($1, $2, $3)
                RETURNING id
                """,
                user_id, url, json.dumps(analysis_data)
            )
        return str(analysis_id)
    
    # ===== CLEANUP & MAINTENANCE =====
    
    async def cleanup_old_data(self, days: int = 90) -> Dict[str, int]:
        """Cleanup old data"""
        async with self.pool.acquire() as conn:
            assignments_result = await conn.execute(
                f"DELETE FROM assignments WHERE assigned_at < NOW() - INTERVAL '{days} days'"
            )
            
            sessions_result = await conn.execute(
                f"DELETE FROM session_analytics WHERE session_start < NOW() - INTERVAL '{days} days'"
            )
            
            previews_result = await conn.execute(
                "DELETE FROM experiment_previews WHERE expires_at <= NOW()"
            )
        
        return {
            'assignments': int(assignments_result.split()[-1]) if assignments_result else 0,
            'sessions': int(sessions_result.split()[-1]) if sessions_result else 0,
            'previews': int(previews_result.split()[-1]) if previews_result else 0
        }
    
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
                    (SELECT COUNT(*) FROM experiment_elements) as total_elements,
                    (SELECT COUNT(*) FROM assignments) as total_assignments,
                    (SELECT COUNT(*) FROM session_analytics) as total_sessions
                """
            )
        return dict(stats) if stats else {}
