# integration/managers/installation_manager.py

"""
Installation Manager

Gestiona el ciclo de vida de las instalaciones:
- Creación
- Verificación
- Monitoreo de salud
- Gestión de tokens
"""

import uuid
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from data_access.database import DatabaseManager

logger = logging.getLogger(__name__)

class InstallationManager:
    """
    Manager para gestionar instalaciones de usuarios
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def create_installation(
        self,
        user_id: str,
        site_url: str,
        platform: str,
        installation_method: str,
        site_name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Crear nueva instalación
        
        Args:
            user_id: ID del usuario
            site_url: URL del sitio
            platform: Plataforma (wordpress, custom, etc)
            installation_method: Método (manual, middleware, plugin)
            site_name: Nombre del sitio (opcional)
            metadata: Metadata adicional
            
        Returns:
            Dict con datos de la instalación creada
        """
        try:
            # Generar tokens únicos
            installation_token = self._generate_installation_token()
            api_token = self._generate_api_token()
            
            async with self.db.pool.acquire() as conn:
                installation_id = await conn.fetchval(
                    """
                    INSERT INTO platform_installations (
                        user_id, platform, installation_method,
                        site_url, site_name,
                        installation_token, api_token,
                        status, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                    """,
                    user_id, platform, installation_method,
                    site_url, site_name,
                    installation_token, api_token,
                    'pending', metadata or {}
                )
                
                # Log creación
                await conn.execute(
                    """
                    INSERT INTO installation_logs (
                        installation_id, event_type, message
                    ) VALUES ($1, $2, $3)
                    """,
                    installation_id,
                    'created',
                    f'Installation created for {site_url}'
                )
            
            logger.info(
                f"Installation created: {installation_id} for user {user_id}"
            )
            
            return {
                'installation_id': str(installation_id),
                'installation_token': installation_token,
                'api_token': api_token,
                'status': 'pending',
                'site_url': site_url,
                'platform': platform,
                'installation_method': installation_method
            }
            
        except Exception as e:
            logger.error(f"Failed to create installation: {str(e)}", exc_info=True)
            raise
    
    async def get_user_installations(
        self,
        user_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtener instalaciones del usuario
        
        Args:
            user_id: ID del usuario
            status: Filtrar por status (opcional)
            
        Returns:
            Lista de instalaciones
        """
        try:
            query = """
                SELECT 
                    pi.*,
                    (SELECT COUNT(*) FROM experiments 
                     WHERE user_id = pi.user_id 
                     AND status = 'active' 
                     AND url LIKE pi.site_url || '%') as active_experiments,
                    CASE 
                        WHEN pi.last_activity > NOW() - INTERVAL '1 hour' THEN 'healthy'
                        WHEN pi.last_activity > NOW() - INTERVAL '24 hours' THEN 'warning'
                        WHEN pi.last_activity IS NULL THEN 'pending'
                        ELSE 'inactive'
                    END as health
                FROM platform_installations pi
                WHERE pi.user_id = $1
            """
            
            params = [user_id]
            
            if status:
                query += " AND pi.status = $2"
                params.append(status)
            
            query += " ORDER BY pi.created_at DESC"
            
            async with self.db.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get installations: {str(e)}", exc_info=True)
            return []
    
    async def get_installation_by_token(
        self,
        installation_token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtener instalación por token
        
        Args:
            installation_token: Token de instalación
            
        Returns:
            Datos de la instalación o None
        """
        try:
            async with self.db.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM platform_installations
                    WHERE installation_token = $1
                    """,
                    installation_token
                )
            
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"Failed to get installation: {str(e)}", exc_info=True)
            return None
    
    async def update_installation_status(
        self,
        installation_id: str,
        status: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Actualizar status de instalación
        
        Args:
            installation_id: ID de la instalación
            status: Nuevo status
            user_id: ID del usuario (para verificar ownership)
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            query = """
                UPDATE platform_installations
                SET status = $1, updated_at = NOW()
                WHERE id = $2
            """
            params = [status, installation_id]
            
            if user_id:
                query += " AND user_id = $3"
                params.append(user_id)
            
            async with self.db.pool.acquire() as conn:
                result = await conn.execute(query, *params)
                
                # Log cambio de status
                if result == 'UPDATE 1':
                    await conn.execute(
                        """
                        INSERT INTO installation_logs (
                            installation_id, event_type, message
                        ) VALUES ($1, $2, $3)
                        """,
                        installation_id,
                        'status_changed',
                        f'Status changed to {status}'
                    )
            
            return result == 'UPDATE 1'
            
        except Exception as e:
            logger.error(f"Failed to update status: {str(e)}", exc_info=True)
            return False
    
    async def mark_verified(
        self,
        installation_id: str
    ) -> bool:
        """
        Marcar instalación como verificada
        
        Args:
            installation_id: ID de la instalación
            
        Returns:
            True si se verificó correctamente
        """
        try:
            async with self.db.pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE platform_installations
                    SET status = 'active',
                        verified_at = NOW(),
                        last_activity = NOW(),
                        updated_at = NOW()
                    WHERE id = $1
                    """,
                    installation_id
                )
                
                # Log verificación
                if result == 'UPDATE 1':
                    await conn.execute(
                        """
                        INSERT INTO installation_logs (
                            installation_id, event_type, message
                        ) VALUES ($1, $2, $3)
                        """,
                        installation_id,
                        'verified',
                        'Installation verified successfully'
                    )
            
            logger.info(f"Installation {installation_id} verified")
            return result == 'UPDATE 1'
            
        except Exception as e:
            logger.error(f"Failed to mark verified: {str(e)}", exc_info=True)
            return False
    
    async def update_last_activity(
        self,
        installation_token: str
    ) -> bool:
        """
        Actualizar última actividad
        
        Se llama cada vez que el tracker hace una request.
        
        Args:
            installation_token: Token de instalación
            
        Returns:
            True si se actualizó
        """
        try:
            async with self.db.pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE platform_installations
                    SET last_activity = NOW()
                    WHERE installation_token = $1
                    """,
                    installation_token
                )
            
            return result == 'UPDATE 1'
            
        except Exception as e:
            logger.error(f"Failed to update activity: {str(e)}", exc_info=True)
            return False
    
    async def regenerate_api_token(
        self,
        installation_id: str,
        user_id: str
    ) -> Optional[str]:
        """
        Regenerar API token
        
        Args:
            installation_id: ID de la instalación
            user_id: ID del usuario (verificar ownership)
            
        Returns:
            Nuevo token o None
        """
        try:
            new_token = self._generate_api_token()
            
            async with self.db.pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE platform_installations
                    SET api_token = $1, updated_at = NOW()
                    WHERE id = $2 AND user_id = $3
                    """,
                    new_token, installation_id, user_id
                )
                
                # Log regeneración
                if result == 'UPDATE 1':
                    await conn.execute(
                        """
                        INSERT INTO installation_logs (
                            installation_id, event_type, message
                        ) VALUES ($1, $2, $3)
                        """,
                        installation_id,
                        'token_regenerated',
                        'API token regenerated'
                    )
            
            return new_token if result == 'UPDATE 1' else None
            
        except Exception as e:
            logger.error(f"Failed to regenerate token: {str(e)}", exc_info=True)
            return None
    
    async def delete_installation(
        self,
        installation_id: str,
        user_id: str
    ) -> bool:
        """
        Eliminar instalación (soft delete)
        
        Args:
            installation_id: ID de la instalación
            user_id: ID del usuario
            
        Returns:
            True si se eliminó
        """
        try:
            async with self.db.pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE platform_installations
                    SET status = 'archived', updated_at = NOW()
                    WHERE id = $1 AND user_id = $2
                    """,
                    installation_id, user_id
                )
                
                # Log eliminación
                if result == 'UPDATE 1':
                    await conn.execute(
                        """
                        INSERT INTO installation_logs (
                            installation_id, event_type, message
                        ) VALUES ($1, $2, $3)
                        """,
                        installation_id,
                        'archived',
                        'Installation archived by user'
                    )
            
            logger.info(f"Installation {installation_id} archived")
            return result == 'UPDATE 1'
            
        except Exception as e:
            logger.error(f"Failed to delete installation: {str(e)}", exc_info=True)
            return False
    
    async def get_installation_logs(
        self,
        installation_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Obtener logs de instalación
        
        Args:
            installation_id: ID de la instalación
            limit: Número de logs a retornar
            
        Returns:
            Lista de logs
        """
        try:
            async with self.db.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT event_type, message, metadata, created_at
                    FROM installation_logs
                    WHERE installation_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    installation_id, limit
                )
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get logs: {str(e)}", exc_info=True)
            return []
    
    def _generate_installation_token(self) -> str:
        """Generar token de instalación único"""
        return f"inst_{uuid.uuid4().hex[:16]}"
    
    def _generate_api_token(self) -> str:
        """Generar API token único"""
        return f"mab_{uuid.uuid4().hex[:32]}"
