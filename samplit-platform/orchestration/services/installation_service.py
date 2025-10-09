# orchestration/services/installation_service.py

"""
Installation Service

Servicio de orquestación para instalaciones.
Coordina entre managers, proxy y base de datos.
"""

import logging
from typing import Dict, Any, Optional, List
from data_access.database import DatabaseManager
from integration.managers.installation_manager import InstallationManager
from integration.managers.verification_manager import VerificationManager
from integration.proxy.injection_engine import InjectionEngine
from integration.proxy.config_generator import ConfigGenerator

logger = logging.getLogger(__name__)

class InstallationService:
    """
    Servicio de orquestación para instalaciones
    
    Coordina el flujo completo de instalación:
    1. Creación
    2. Generación de instrucciones/código
    3. Verificación
    4. Monitoreo
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.installation_manager = InstallationManager(db)
        self.verification_manager = VerificationManager()
        self.injection_engine = InjectionEngine("https://api.samplit.com")
        self.config_generator = ConfigGenerator("https://proxy.samplit.com")
    
    async def create_manual_installation(
        self,
        user_id: str,
        site_url: str,
        site_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crear instalación manual (snippet de código)
        
        Args:
            user_id: ID del usuario
            site_url: URL del sitio
            site_name: Nombre del sitio (opcional)
            
        Returns:
            Dict con instalación y código para copiar
        """
        try:
            # Crear instalación
            installation = await self.installation_manager.create_installation(
                user_id=user_id,
                site_url=site_url,
                platform='custom',
                installation_method='manual',
                site_name=site_name
            )
            
            # Generar snippet de código
            tracking_code = self.injection_engine.generate_manual_snippet(
                installation_token=installation['installation_token'],
                site_url=site_url
            )
            
            return {
                **installation,
                'tracking_code': tracking_code,
                'instructions': {
                    'type': 'manual',
                    'steps': [
                        'Copy the tracking code below',
                        'Paste it in your website\'s <head> section',
                        'Save and publish your changes',
                        'Click "Verify Installation" to confirm'
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to create manual installation: {str(e)}", exc_info=True)
            raise
    
    async def create_middleware_installation(
        self,
        user_id: str,
        site_url: str,
        platform: str,  # nginx, apache, cloudflare, etc
        site_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crear instalación con middleware/proxy
        
        Args:
            user_id: ID del usuario
            site_url: URL del sitio
            platform: Plataforma del servidor
            site_name: Nombre del sitio (opcional)
            
        Returns:
            Dict con instalación y configuración del servidor
        """
        try:
            # Crear instalación
            installation = await self.installation_manager.create_installation(
                user_id=user_id,
                site_url=site_url,
                platform=platform,
                installation_method='middleware',
                site_name=site_name
            )
            
            # Generar configuración del servidor
            from urllib.parse import urlparse
            domain = urlparse(site_url).netloc
            
            server_config = self.config_generator.generate_config(
                domain=domain,
                installation_token=installation['installation_token'],
                platform=platform
            )
            
            return {
                **installation,
                'server_config': {
                    'platform': server_config.platform,
                    'config_code': server_config.config_code,
                    'steps': server_config.steps,
                    'verification_command': server_config.verification_command
                },
                'proxy_url': f"https://proxy.samplit.com/{installation['installation_token']}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create middleware installation: {str(e)}", exc_info=True)
            raise
    
    async def verify_installation(
        self,
        installation_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Verificar que la instalación esté funcionando
        
        Args:
            installation_id: ID de la instalación
            user_id: ID del usuario
            
        Returns:
            Dict con resultado de la verificación
        """
        try:
            # Obtener instalación
            installations = await self.installation_manager.get_user_installations(
                user_id=user_id
            )
            
            installation = next(
                (i for i in installations if str(i['id']) == installation_id),
                None
            )
            
            if not installation:
                return {
                    'verified': False,
                    'error': 'Installation not found'
                }
            
            # Verificar
            verification_result = await self.verification_manager.verify_installation(
                site_url=installation['site_url'],
                installation_token=installation['installation_token']
            )
            
            # Si se verificó correctamente, actualizar en DB
            if verification_result['verified']:
                await self.installation_manager.mark_verified(installation_id)
                
                logger.info(f"Installation {installation_id} verified successfully")
            
            return verification_result
            
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}", exc_info=True)
            return {
                'verified': False,
                'error': str(e)
            }
    
    async def get_active_experiments_for_url(
        self,
        installation_token: str,
        url: str
    ) -> List[Dict[str, Any]]:
        """
        Obtener experimentos activos para una URL
        
        Usado por el proxy para saber qué experimentos inyectar.
        
        Args:
            installation_token: Token de instalación
            url: URL de la página
            
        Returns:
            Lista de experimentos activos
        """
        try:
            # Obtener instalación
            installation = await self.installation_manager.get_installation_by_token(
                installation_token
            )
            
            if not installation or installation['status'] != 'active':
                return []
            
            user_id = installation['user_id']
            
            # Obtener experimentos activos para esta URL
            async with self.db.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT 
                        e.id, e.name, e.config,
                        json_agg(json_build_object(
                            'id', ee.id,
                            'name', ee.name,
                            'selector', ee.selector,
                            'element_type', ee.element_type,
                            'variants', (
                                SELECT json_agg(json_build_object(
                                    'id', ev.id,
                                    'content', ev.content
                                ))
                                FROM element_variants ev
                                WHERE ev.element_id = ee.id
                            )
                        )) as elements
                    FROM experiments e
                    JOIN experiment_elements ee ON e.id = ee.experiment_id
                    WHERE e.user_id = $1
                      AND e.status = 'active'
                      AND (e.url = $2 OR $2 LIKE e.url || '%')
                    GROUP BY e.id
                    """,
                    user_id, url
                )
            
            experiments = []
            for row in rows:
                experiments.append({
                    'id': str(row['id']),
                    'name': row['name'],
                    'config': row['config'],
                    'elements': row['elements']
                })
            
            # Actualizar última actividad
            await self.installation_manager.update_last_activity(installation_token)
            
            return experiments
            
        except Exception as e:
            logger.error(f"Failed to get experiments: {str(e)}", exc_info=True)
            return []
    
    async def check_installation_health(
        self,
        installation_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Verificar salud de la instalación
        
        Args:
            installation_id: ID de la instalación
            user_id: ID del usuario
            
        Returns:
            Dict con información de salud
        """
        try:
            # Obtener instalación
            installations = await self.installation_manager.get_user_installations(
                user_id=user_id
            )
            
            installation = next(
                (i for i in installations if str(i['id']) == installation_id),
                None
            )
            
            if not installation:
                return {
                    'health': 'unknown',
                    'error': 'Installation not found'
                }
            
            # Verificar salud
            health_result = await self.verification_manager.check_health(
                site_url=installation['site_url']
            )
            
            return {
                **health_result,
                'installation_status': installation['status'],
                'last_activity': installation.get('last_activity'),
                'verified_at': installation.get('verified_at')
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
            return {
                'health': 'error',
                'error': str(e)
            }
    
    async def get_installation_details(
        self,
        installation_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtener detalles completos de instalación
        
        Args:
            installation_id: ID de la instalación
            user_id: ID del usuario
            
        Returns:
            Dict con detalles completos
        """
        try:
            # Obtener instalación
            installations = await self.installation_manager.get_user_installations(
                user_id=user_id
            )
            
            installation = next(
                (i for i in installations if str(i['id']) == installation_id),
                None
            )
            
            if not installation:
                return None
            
            # Obtener stats de experimentos
            async with self.db.pool.acquire() as conn:
                stats = await conn.fetchrow(
                    """
                    SELECT 
                        COUNT(DISTINCT e.id) as total_experiments,
                        COUNT(DISTINCT e.id) FILTER (WHERE e.status = 'active') as active_experiments,
                        COUNT(DISTINCT a.user_id) as total_visitors,
                        COUNT(DISTINCT a.id) FILTER (WHERE a.converted_at IS NOT NULL) as conversions
                    FROM experiments e
                    LEFT JOIN assignments a ON e.id = a.experiment_id
                    WHERE e.user_id = $1 
                      AND e.url LIKE $2
                    """,
                    user_id,
                    installation['site_url'] + '%'
                )
            
            # Obtener logs recientes
            logs = await self.installation_manager.get_installation_logs(
                installation_id,
                limit=10
            )
            
            return {
                **dict(installation),
                'stats': dict(stats) if stats else {},
                'recent_logs': logs
            }
            
        except Exception as e:
            logger.error(f"Failed to get details: {str(e)}", exc_info=True)
            return None
