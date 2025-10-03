# backend/database_extended.py
import asyncpg
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from models_extended import *
from database import DatabaseManager  # Tu clase existente

class DatabaseManagerExtended(DatabaseManager):
    """
    Extensión de DatabaseManager para Fase 2
    Mantiene compatibilidad completa con Fase 1
    """
    
    async def _create_tables(self):
        """Crear tablas existentes + nuevas tablas Fase 2"""
        
        # Ejecutar creación de tablas originales
        await super()._create_tables()
        
        # Nuevas tablas para Fase 2
        phase2_schema = """
        
        -- Tabla de elementos (nuevo en Fase 2)
        CREATE TABLE IF NOT EXISTS experiment_elements (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
            element_order INTEGER NOT NULL DEFAULT 0,
            
            -- Configuración del selector
            primary_selector_type VARCHAR(20) NOT NULL,
            primary_selector VARCHAR(500) NOT NULL,
            primary_specificity INTEGER DEFAULT 50,
            fallback_selectors JSONB DEFAULT '[]',
            xpath VARCHAR(1000),
            
            -- Tipo y contenido
            element_type VARCHAR(20) NOT NULL DEFAULT 'text',
            original_content JSONB NOT NULL DEFAULT '{}',
            variants JSONB NOT NULL DEFAULT '[]',
            
            -- Análisis de estabilidad
            stability_score INTEGER DEFAULT 50,
            stability_factors JSONB DEFAULT '[]',
            stability_warnings JSONB DEFAULT '[]',
            stability_recommendations JSONB DEFAULT '[]',
            
            -- Posición para preview
            position_x DECIMAL(10,2),
            position_y DECIMAL(10,2), 
            position_width DECIMAL(10,2),
            position_height DECIMAL(10,2),
            viewport_width INTEGER,
            viewport_height INTEGER,
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            UNIQUE(experiment_id, element_order)
        );
        
        -- Reglas de targeting
        CREATE TABLE IF NOT EXISTS targeting_rules (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
            group_id VARCHAR(50) NOT NULL,
            group_name VARCHAR(255),
            
            rule_type VARCHAR(50) NOT NULL,
            operator VARCHAR(20) NOT NULL,
            value VARCHAR(500) NOT NULL,
            enabled BOOLEAN DEFAULT true,
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            INDEX idx_targeting_experiment_group (experiment_id, group_id)
        );
        
        -- Configuración extendida de experimentos
        ALTER TABLE experiments ADD COLUMN IF NOT EXISTS url VARCHAR(500);
        ALTER TABLE experiments ADD COLUMN IF NOT EXISTS max_elements INTEGER DEFAULT 5;
        ALTER TABLE experiments ADD COLUMN IF NOT EXISTS enable_preview BOOLEAN DEFAULT true;
        ALTER TABLE experiments ADD COLUMN IF NOT EXISTS enable_heatmaps BOOLEAN DEFAULT false;
        ALTER TABLE experiments ADD COLUMN IF NOT EXISTS custom_css TEXT;
        ALTER TABLE experiments ADD COLUMN IF NOT EXISTS exclude_selectors JSONB DEFAULT '[]';
        
        -- Analytics extendidas de sesiones
        CREATE TABLE IF NOT EXISTS session_analytics (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_id VARCHAR(255) NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
            
            -- Asignaciones de variantes por elemento
            variant_assignments JSONB NOT NULL DEFAULT '{}',
            
            -- Métricas de página
            page_load_time DECIMAL(10,2),
            time_on_page DECIMAL(10,2) DEFAULT 0,
            scroll_depth DECIMAL(5,2) DEFAULT 0,
            
            -- Contexto del usuario
            device_info JSONB,
            viewport_width INTEGER,
            viewport_height INTEGER,
            
            session_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            INDEX idx_session_experiment (experiment_id, session_id),
            INDEX idx_session_user (user_id, experiment_id),
            INDEX idx_session_time (session_start)
        );
        
        -- Interacciones con elementos
        CREATE TABLE IF NOT EXISTS element_interactions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_analytics_id UUID NOT NULL REFERENCES session_analytics(id) ON DELETE CASCADE,
            element_id UUID REFERENCES experiment_elements(id) ON DELETE CASCADE,
            
            interaction_type VARCHAR(50) NOT NULL,
            coordinates_x DECIMAL(10,2),
            coordinates_y DECIMAL(10,2),
            metadata JSONB DEFAULT '{}',
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            INDEX idx_interactions_session (session_analytics_id),
            INDEX idx_interactions_element (element_id),
            INDEX idx_interactions_type (interaction_type)
        );
        
        -- Micro conversiones
        CREATE TABLE IF NOT EXISTS micro_conversions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_analytics_id UUID NOT NULL REFERENCES session_analytics(id) ON DELETE CASCADE,
            
            conversion_type VARCHAR(50) NOT NULL,
            value DECIMAL(10,2) DEFAULT 1.0,
            metadata JSONB DEFAULT '{}',
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            INDEX idx_micro_conversions_session (session_analytics_id),
            INDEX idx_micro_conversions_type (conversion_type)
        );
        
        -- Previews de experimentos
        CREATE TABLE IF NOT EXISTS experiment_previews (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            
            variant_selections JSONB NOT NULL DEFAULT '{}',
            viewport_width INTEGER DEFAULT 1920,
            viewport_height INTEGER DEFAULT 1080,
            screenshot_url VARCHAR(500),
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '7 days',
            
            INDEX idx_previews_experiment (experiment_id),
            INDEX idx_previews_user (user_id),
            INDEX idx_previews_expires (expires_at)
        );
        
        -- Análisis de páginas
        CREATE TABLE IF NOT EXISTS page_analysis (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            
            url VARCHAR(500) NOT NULL,
            title VARCHAR(255),
            elements_found JSONB DEFAULT '[]',
            page_info JSONB DEFAULT '{}',
            recommendations JSONB DEFAULT '[]',
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            INDEX idx_page_analysis_user (user_id),
            INDEX idx_page_analysis_url (url),
            INDEX idx_page_analysis_time (created_at)
        );
        
        -- Índices adicionales para performance
        CREATE INDEX IF NOT EXISTS idx_experiment_elements_type ON experiment_elements(element_type);
        CREATE INDEX IF NOT EXISTS idx_experiment_elements_stability ON experiment_elements(stability_score);
        CREATE INDEX IF NOT EXISTS idx_targeting_rules_type ON targeting_rules(rule_type);
        CREATE INDEX IF NOT EXISTS idx_session_analytics_time_range ON session_analytics(session_start, last_activity);
        
        -- Triggers para updated_at
        CREATE OR REPLACE FUNCTION update_experiment_elements_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        DROP TRIGGER IF EXISTS update_experiment_elements_updated_at ON experiment_elements;
        CREATE TRIGGER update_experiment_elements_updated_at
            BEFORE UPDATE ON experiment_elements
            FOR EACH ROW EXECUTE FUNCTION update_experiment_elements_updated_at();
        
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(phase2_schema)
        
        self.logger.info("Phase 2 database schema created/updated")
    
    # ===== EXPERIMENT ELEMENTS OPERATIONS =====
    
    async def create_experiment_element(
        self,
        experiment_id: str,
        element_config: ElementConfig
    ) -> str:
        """Crear elemento para experimento"""
        async with self.pool.acquire() as conn:
            element_id = await conn.fetchval(
                """
                INSERT INTO experiment_elements (
                    experiment_id, element_order,
                    primary_selector_type, primary_selector, primary_specificity,
                    fallback_selectors, xpath, element_type, original_content, variants,
                    stability_score, stability_factors, stability_warnings, stability_recommendations,
                    position_x, position_y, position_width, position_height,
                    viewport_width, viewport_height
                ) VALUES (
                    $1, COALESCE((SELECT MAX(element_order) + 1 FROM experiment_elements WHERE experiment_id = $1), 0),
                    $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19
                ) RETURNING id
                """,
                experiment_id,
                element_config.selector.primary.type.value,
                element_config.selector.primary.selector,
                element_config.selector.primary.specificity,
                json.dumps([{
                    'type': fb.type.value,
                    'selector': fb.selector,
                    'specificity': fb.specificity,
                    'reliable': fb.reliable
                } for fb in element_config.selector.fallbacks]),
                element_config.selector.xpath,
                element_config.element_type.value,
                json.dumps(element_config.original_content),
                json.dumps([{
                    'type': v.type,
                    'value': v.value,
                    'attributes': v.attributes,
                    'styles': v.styles
                } for v in element_config.variants]),
                element_config.stability.score if element_config.stability else 50,
                json.dumps(element_config.stability.factors if element_config.stability else []),
                json.dumps(element_config.stability.warnings if element_config.stability else []),
                json.dumps(element_config.stability.recommendations if element_config.stability else []),
                element_config.position.x if element_config.position else None,
                element_config.position.y if element_config.position else None,
                element_config.position.width if element_config.position else None,
                element_config.position.height if element_config.position else None,
                element_config.position.viewport_width if element_config.position else None,
                element_config.position.viewport_height if element_config.position else None
            )
        
        return str(element_id)
    
    async def get_experiment_elements(self, experiment_id: str) -> List[Dict[str, Any]]:
        """Obtener elementos de un experimento"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    id, element_order, primary_selector_type, primary_selector, 
                    primary_specificity, fallback_selectors, xpath, element_type,
                    original_content, variants, stability_score, stability_factors,
                    stability_warnings, stability_recommendations,
                    position_x, position_y, position_width, position_height,
                    viewport_width, viewport_height, created_at, updated_at
                FROM experiment_elements 
                WHERE experiment_id = $1 
                ORDER BY element_order
                """,
                experiment_id
            )
        
        elements = []
        for row in rows:
            element_data = dict(row)
            # Deserializar JSON fields
            element_data['fallback_selectors'] = json.loads(element_data['fallback_selectors'] or '[]')
            element_data['original_content'] = json.loads(element_data['original_content'] or '{}')
            element_data['variants'] = json.loads(element_data['variants'] or '[]')
            element_data['stability_factors'] = json.loads(element_data['stability_factors'] or '[]')
            element_data['stability_warnings'] = json.loads(element_data['stability_warnings'] or '[]')
            element_data['stability_recommendations'] = json.loads(element_data['stability_recommendations'] or '[]')
            elements.append(element_data)
        
        return elements
    
    async def update_element_stability(
        self,
        element_id: str,
        stability: ElementStability
    ) -> None:
        """Actualizar análisis de estabilidad de elemento"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE experiment_elements 
                SET stability_score = $1, stability_factors = $2,
                    stability_warnings = $3, stability_recommendations = $4
                WHERE id = $5
                """,
                stability.score,
                json.dumps(stability.factors),
                json.dumps(stability.warnings),
                json.dumps(stability.recommendations),
                element_id
            )
    
    # ===== TARGETING OPERATIONS =====
    
    async def save_targeting_rules(
        self,
        experiment_id: str,
        targeting_config: TargetingConfig
    ) -> None:
        """Guardar reglas de targeting"""
        async with self.pool.acquire() as conn:
            # Limpiar reglas existentes
            await conn.execute(
                "DELETE FROM targeting_rules WHERE experiment_id = $1",
                experiment_id
            )
            
            # Insertar nuevas reglas
            for group in targeting_config.groups:
                for rule in group.rules:
                    await conn.execute(
                        """
                        INSERT INTO targeting_rules 
                        (experiment_id, group_id, group_name, rule_type, operator, value, enabled)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                        experiment_id, group.id or group.name.lower().replace(' ', '_'),
                        group.name, rule.type, rule.operator.value, rule.value, rule.enabled
                    )
    
    async def get_targeting_rules(self, experiment_id: str) -> Dict[str, Any]:
        """Obtener reglas de targeting"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT group_id, group_name, rule_type, operator, value, enabled
                FROM targeting_rules 
                WHERE experiment_id = $1
                ORDER BY group_id, rule_type
                """,
                experiment_id
            )
        
        groups = {}
        for row in rows:
            group_id = row['group_id']
            if group_id not in groups:
                groups[group_id] = {
                    'id': group_id,
                    'name': row['group_name'],
                    'rules': []
                }
            
            groups[group_id]['rules'].append({
                'type': row['rule_type'],
                'operator': row['operator'],
                'value': row['value'],
                'enabled': row['enabled']
            })
        
        return {
            'enabled': len(groups) > 0,
            'groups': list(groups.values())
        }
    
    # ===== ANALYTICS OPERATIONS =====
    
    async def create_session_analytics(
        self,
        session_id: str,
        user_id: str,
        experiment_id: str,
        variant_assignments: Dict[str, str],
        device_info: Optional[Dict[str, Any]] = None,
        viewport_width: Optional[int] = None,
        viewport_height: Optional[int] = None
    ) -> str:
        """Crear sesión de analytics"""
        async with self.pool.acquire() as conn:
            analytics_id = await conn.fetchval(
                """
                INSERT INTO session_analytics 
                (session_id, user_id, experiment_id, variant_assignments, 
                 device_info, viewport_width, viewport_height)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                session_id, user_id, experiment_id, 
                json.dumps(variant_assignments),
                json.dumps(device_info) if device_info else None,
                viewport_width, viewport_height
            )
        
        return str(analytics_id)
    
    async def record_element_interaction(
        self,
        session_analytics_id: str,
        element_id: str,
        interaction_type: str,
        coordinates: Optional[Tuple[float, float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Registrar interacción con elemento"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO element_interactions 
                (session_analytics_id, element_id, interaction_type, 
                 coordinates_x, coordinates_y, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                session_analytics_id, element_id, interaction_type,
                coordinates[0] if coordinates else None,
                coordinates[1] if coordinates else None,
                json.dumps(metadata) if metadata else None
            )
    
    async def record_micro_conversion(
        self,
        session_analytics_id: str,
        conversion_type: str,
        value: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Registrar micro conversión"""
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
    
    async def update_session_metrics(
        self,
        session_analytics_id: str,
        page_load_time: Optional[float] = None,
        time_on_page: Optional[float] = None,
        scroll_depth: Optional[float] = None
    ) -> None:
        """Actualizar métricas de sesión"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE session_analytics 
                SET page_load_time = COALESCE($2, page_load_time),
                    time_on_page = COALESCE($3, time_on_page),
                    scroll_depth = COALESCE($4, scroll_depth),
                    last_activity = NOW()
                WHERE id = $1
                """,
                session_analytics_id, page_load_time, time_on_page, scroll_depth
            )
    
    # ===== PREVIEW OPERATIONS =====
    
    async def create_experiment_preview(
        self,
        experiment_id: str,
        user_id: str,
        variant_selections: Dict[str, int],
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        screenshot_url: Optional[str] = None
    ) -> str:
        """Crear preview de experimento"""
        async with self.pool.acquire() as conn:
            preview_id = await conn.fetchval(
                """
                INSERT INTO experiment_previews 
                (experiment_id, user_id, variant_selections, viewport_width, 
                 viewport_height, screenshot_url)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                experiment_id, user_id, json.dumps(variant_selections),
                viewport_width, viewport_height, screenshot_url
            )
        
        return str(preview_id)
    
    async def get_experiment_preview(self, preview_id: str) -> Optional[Dict[str, Any]]:
        """Obtener preview de experimento"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT experiment_id, user_id, variant_selections, viewport_width,
                       viewport_height, screenshot_url, created_at, expires_at
                FROM experiment_previews 
                WHERE id = $1 AND expires_at > NOW()
                """,
                preview_id
            )
        
        if row:
            preview_data = dict(row)
            preview_data['variant_selections'] = json.loads(preview_data['variant_selections'])
            return preview_data
        return None
    
    async def cleanup_expired_previews(self) -> int:
        """Limpiar previews expirados"""
        async with self.pool.acquire() as conn:
            deleted_count = await conn.fetchval(
                """
                DELETE FROM experiment_previews 
                WHERE expires_at <= NOW()
                RETURNING (SELECT COUNT(*) FROM experiment_previews WHERE expires_at <= NOW())
                """)
        
        return deleted_count or 0
    
    # ===== PAGE ANALYSIS OPERATIONS =====
    
    async def save_page_analysis(
        self,
        user_id: str,
        url: str,
        title: str,
        elements_found: List[Dict[str, Any]],
        page_info: Dict[str, Any],
        recommendations: List[str]
    ) -> str:
        """Guardar análisis de página"""
        async with self.pool.acquire() as conn:
            analysis_id = await conn.fetchval(
                """
                INSERT INTO page_analysis 
                (user_id, url, title, elements_found, page_info, recommendations)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                user_id, url, title, 
                json.dumps(elements_found),
                json.dumps(page_info),
                json.dumps(recommendations)
            )
        
        return str(analysis_id)
    
    async def get_page_analysis(self, analysis_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtener análisis de página"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT url, title, elements_found, page_info, recommendations, created_at
                FROM page_analysis 
                WHERE id = $1 AND user_id = $2
                """,
                analysis_id, user_id
            )
        
        if row:
            analysis_data = dict(row)
            analysis_data['elements_found'] = json.loads(analysis_data['elements_found'])
            analysis_data['page_info'] = json.loads(analysis_data['page_info'])
            analysis_data['recommendations'] = json.loads(analysis_data['recommendations'])
            return analysis_data
        return None
    
    async def get_user_page_analyses(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtener análisis de páginas del usuario"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, url, title, created_at,
                       ARRAY_LENGTH(CAST(elements_found AS json[]), 1) as elements_count
                FROM page_analysis 
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                user_id, limit
            )
        
        return [dict(row) for row in rows]
    
    # ===== ANALYTICS QUERIES =====
    
    async def get_element_interaction_stats(
        self, 
        element_id: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Obtener estadísticas de interacción con elemento"""
        async with self.pool.acquire() as conn:
            # Filtros de fecha
            date_filter = ""
            params = [element_id]
            
            if start_date:
                date_filter += " AND ei.created_at >= $2"
                params.append(start_date)
            if end_date:
                date_filter += f" AND ei.created_at <= ${len(params) + 1}"
                params.append(end_date)
            
            # Estadísticas generales
            general_stats = await conn.fetchrow(f"""
                SELECT 
                    COUNT(*) as total_interactions,
                    COUNT(DISTINCT sa.session_id) as unique_sessions,
                    COUNT(DISTINCT sa.user_id) as unique_users,
                    AVG(sa.time_on_page) as avg_time_on_page,
                    AVG(sa.scroll_depth) as avg_scroll_depth
                FROM element_interactions ei
                JOIN session_analytics sa ON ei.session_analytics_id = sa.id
                WHERE ei.element_id = $1{date_filter}
            """, *params)
            
            # Distribución por tipo de interacción
            interaction_types = await conn.fetch(f"""
                SELECT 
                    interaction_type,
                    COUNT(*) as count,
                    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
                FROM element_interactions ei
                WHERE ei.element_id = $1{date_filter}
                GROUP BY interaction_type
                ORDER BY count DESC
            """, *params)
            
            # Heatmap data (coordenadas de clicks)
            heatmap_data = await conn.fetch(f"""
                SELECT 
                    coordinates_x as x,
                    coordinates_y as y,
                    COUNT(*) as intensity
                FROM element_interactions ei
                WHERE ei.element_id = $1 
                  AND ei.coordinates_x IS NOT NULL 
                  AND ei.coordinates_y IS NOT NULL{date_filter}
                GROUP BY coordinates_x, coordinates_y
                ORDER BY intensity DESC
                LIMIT 1000
            """, *params)
        
        return {
            'general_stats': dict(general_stats) if general_stats else {},
            'interaction_types': [dict(row) for row in interaction_types],
            'heatmap_data': [dict(row) for row in heatmap_data]
        }
    
    async def get_experiment_conversion_funnel(
        self, 
        experiment_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Obtener embudo de conversión del experimento"""
        async with self.pool.acquire() as conn:
            # Definir steps del funnel
            funnel_steps = [
                ('page_view', 'Page View'),
                ('element_view', 'Element in View'),
                ('element_interaction', 'Element Clicked'),
                ('micro_conversion', 'Micro Conversion'),
                ('final_conversion', 'Final Conversion')
            ]
            
            date_filter = ""
            params = [experiment_id]
            
            if start_date:
                date_filter += " AND sa.session_start >= $2"
                params.append(start_date)
            if end_date:
                date_filter += f" AND sa.session_start <= ${len(params) + 1}"
                params.append(end_date)
            
            funnel_data = []
            
            # Page views (sesiones totales)
            page_views = await conn.fetchval(f"""
                SELECT COUNT(DISTINCT sa.session_id)
                FROM session_analytics sa
                WHERE sa.experiment_id = $1{date_filter}
            """, *params)
            
            funnel_data.append({
                'step': 'page_view',
                'name': 'Page View',
                'count': page_views or 0,
                'percentage': 100.0 if page_views else 0
            })
            
            # Element interactions
            element_interactions = await conn.fetchval(f"""
                SELECT COUNT(DISTINCT sa.session_id)
                FROM session_analytics sa
                JOIN element_interactions ei ON sa.id = ei.session_analytics_id
                WHERE sa.experiment_id = $1{date_filter}
            """, *params)
            
            funnel_data.append({
                'step': 'element_interaction', 
                'name': 'Element Clicked',
                'count': element_interactions or 0,
                'percentage': (element_interactions / page_views * 100) if page_views else 0
            })
            
            # Micro conversions
            micro_conversions = await conn.fetchval(f"""
                SELECT COUNT(DISTINCT sa.session_id)
                FROM session_analytics sa
                JOIN micro_conversions mc ON sa.id = mc.session_analytics_id
                WHERE sa.experiment_id = $1{date_filter}
            """, *params)
            
            funnel_data.append({
                'step': 'micro_conversion',
                'name': 'Micro Conversion', 
                'count': micro_conversions or 0,
                'percentage': (micro_conversions / page_views * 100) if page_views else 0
            })
            
            # Final conversions (from assignments table)
            final_conversions = await conn.fetchval(f"""
                SELECT COUNT(DISTINCT a.user_id)
                FROM assignments a
                WHERE a.experiment_id = $1 
                  AND a.converted_at IS NOT NULL{date_filter.replace('sa.session_start', 'a.converted_at')}
            """, *params)
            
            funnel_data.append({
                'step': 'final_conversion',
                'name': 'Final Conversion',
                'count': final_conversions or 0,
                'percentage': (final_conversions / page_views * 100) if page_views else 0
            })
        
        return funnel_data
    
    async def get_experiment_heatmap_data(
        self,
        experiment_id: str,
        element_id: Optional[str] = None,
        interaction_type: str = 'click',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Obtener datos de heatmap para experimento"""
        async with self.pool.acquire() as conn:
            params = [experiment_id, interaction_type]
            filters = []
            
            if element_id:
                filters.append(f"ei.element_id = ${len(params) + 1}")
                params.append(element_id)
            
            if start_date:
                filters.append(f"ei.created_at >= ${len(params) + 1}")
                params.append(start_date)
                
            if end_date:
                filters.append(f"ei.created_at <= ${len(params) + 1}")
                params.append(end_date)
            
            where_clause = " AND ".join(filters)
            if where_clause:
                where_clause = " AND " + where_clause
            
            heatmap_points = await conn.fetch(f"""
                SELECT 
                    ei.coordinates_x as x,
                    ei.coordinates_y as y,
                    COUNT(*) as intensity,
                    sa.viewport_width,
                    sa.viewport_height,
                    ee.element_type
                FROM element_interactions ei
                JOIN session_analytics sa ON ei.session_analytics_id = sa.id  
                LEFT JOIN experiment_elements ee ON ei.element_id = ee.id
                WHERE sa.experiment_id = $1 
                  AND ei.interaction_type = $2
                  AND ei.coordinates_x IS NOT NULL 
                  AND ei.coordinates_y IS NOT NULL{where_clause}
                GROUP BY ei.coordinates_x, ei.coordinates_y, sa.viewport_width, sa.viewport_height, ee.element_type
                ORDER BY intensity DESC
                LIMIT 5000
            """, *params)
        
        return [dict(row) for row in heatmap_points]
    
    # ===== PERFORMANCE MONITORING =====
    
    async def get_database_performance_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de performance de la base de datos"""
        async with self.pool.acquire() as conn:
            # Tamaños de tablas principales
            table_sizes = await conn.fetch("""
                SELECT 
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public' 
                  AND tablename IN ('experiments', 'experiment_elements', 'session_analytics', 'element_interactions')
                ORDER BY size_bytes DESC
            """)
            
            # Estadísticas de actividad reciente
            activity_stats = await conn.fetchrow("""
                SELECT 
                    (SELECT COUNT(*) FROM experiments WHERE created_at > NOW() - INTERVAL '24 hours') as experiments_24h,
                    (SELECT COUNT(*) FROM session_analytics WHERE session_start > NOW() - INTERVAL '24 hours') as sessions_24h,
                    (SELECT COUNT(*) FROM element_interactions WHERE created_at > NOW() - INTERVAL '24 hours') as interactions_24h,
                    (SELECT COUNT(*) FROM assignments WHERE assigned_at > NOW() - INTERVAL '24 hours') as assignments_24h
            """)
            
            # Performance de queries frecuentes
            slow_queries = await conn.fetch("""
                SELECT query, mean_time, calls, total_time
                FROM pg_stat_statements 
                WHERE query LIKE '%experiment%' OR query LIKE '%element%'
                ORDER BY mean_time DESC
                LIMIT 10
            """) if await conn.fetchval("SELECT COUNT(*) FROM pg_extension WHERE extname = 'pg_stat_statements'") else []
        
        return {
            'table_sizes': [dict(row) for row in table_sizes],
            'activity_24h': dict(activity_stats) if activity_stats else {},
            'slow_queries': [dict(row) for row in slow_queries]
        }
    
    # ===== CLEANUP OPERATIONS =====
    
    async def cleanup_old_analytics_data(self, days: int = 90) -> Dict[str, int]:
        """Limpiar datos de analytics antiguos"""
        async with self.pool.acquire() as conn:
            # Limpiar interacciones
            interactions_deleted = await conn.fetchval("""
                DELETE FROM element_interactions 
                WHERE created_at < NOW() - INTERVAL '%s days'
                RETURNING (SELECT COUNT(*) FROM element_interactions 
                          WHERE created_at < NOW() - INTERVAL '%s days')
            """, days, days)
            
            # Limpiar micro conversiones
            micro_conv_deleted = await conn.fetchval("""
                DELETE FROM micro_conversions 
                WHERE created_at < NOW() - INTERVAL '%s days'
                RETURNING (SELECT COUNT(*) FROM micro_conversions 
                          WHERE created_at < NOW() - INTERVAL '%s days')
            """, days, days)
            
            # Limpiar sesiones huérfanas
            sessions_deleted = await conn.fetchval("""
                DELETE FROM session_analytics 
                WHERE session_start < NOW() - INTERVAL '%s days'
                  AND NOT EXISTS (
                    SELECT 1 FROM element_interactions ei 
                    WHERE ei.session_analytics_id = session_analytics.id
                  )
                RETURNING (SELECT COUNT(*) FROM session_analytics 
                          WHERE session_start < NOW() - INTERVAL '%s days')
            """, days, days)
            
            # Limpiar análisis de páginas antiguos
            analysis_deleted = await conn.fetchval("""
                DELETE FROM page_analysis 
                WHERE created_at < NOW() - INTERVAL '%s days'
                RETURNING (SELECT COUNT(*) FROM page_analysis 
                          WHERE created_at < NOW() - INTERVAL '%s days')
            """, days, days)
        
        cleanup_summary = {
            'interactions_deleted': interactions_deleted or 0,
            'micro_conversions_deleted': micro_conv_deleted or 0,
            'sessions_deleted': sessions_deleted or 0,
            'analyses_deleted': analysis_deleted or 0
        }
        
        self.logger.info(f"Cleanup completed: {cleanup_summary}")
        return cleanup_summary
