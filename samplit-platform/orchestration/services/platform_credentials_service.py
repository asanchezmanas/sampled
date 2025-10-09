# orchestration/services/platform_credentials_service.py

"""
Platform Credentials Service

Maneja credenciales cifradas de plataformas de ads
"""

import logging
from typing import Dict, Any, Optional
from data_access.database import DatabaseManager
from engine.state.encryption import get_encryptor

logger = logging.getLogger(__name__)

class PlatformCredentialsService:
    """
    Servicio para gestionar credenciales de plataformas
    
    Todas las credenciales se almacenan cifradas en DB.
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.encryptor = get_encryptor()
    
    async def save_credentials(
        self,
        user_id: str,
        platform: str,
        credentials: Dict[str, Any]
    ):
        """
        Guardar credenciales cifradas
        
        Args:
            user_id: ID del usuario
            platform: 'meta' o 'google'
            credentials: Dict con access tokens, etc
        """
        
        # Encrypt credentials
        encrypted = self.encryptor.encrypt_state(credentials)
        
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO platform_integrations (
                    user_id, platform, credentials, status
                ) VALUES ($1, $2, $3, 'active')
                ON CONFLICT (user_id, platform)
                DO UPDATE SET 
                    credentials = $3,
                    status = 'active',
                    updated_at = NOW()
                """,
                user_id, platform, encrypted
            )
        
        logger.info(f"Saved credentials for user {user_id} platform {platform}")
    
    async def get_credentials(
        self,
        user_id: str,
        platform: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtener credenciales descifradas
        
        Returns:
            Dict con credenciales o None si no existen
        """
        
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT credentials FROM platform_integrations
                WHERE user_id = $1 AND platform = $2 AND status = 'active'
                """,
                user_id, platform
            )
        
        if not row or not row['credentials']:
            return None
        
        # Decrypt
        credentials = self.encryptor.decrypt_state(row['credentials'])
        
        return credentials
    
    async def delete_credentials(
        self,
        user_id: str,
        platform: str
    ):
        """Eliminar credenciales (marcar como inactive)"""
        
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE platform_integrations
                SET status = 'inactive', updated_at = NOW()
                WHERE user_id = $1 AND platform = $2
                """,
                user_id, platform
            )
        
        logger.info(f"Deleted credentials for user {user_id} platform {platform}")
    
    async def test_credentials(
        self,
        user_id: str,
        platform: str
    ) -> bool:
        """
        Probar que las credenciales funcionan
        
        Returns:
            True si las credenciales son válidas
        """
        
        credentials = await self.get_credentials(user_id, platform)
        
        if not credentials:
            return False
        
        try:
            if platform == 'meta':
                from integration.platforms.meta_ads import MetaAdsIntegration
                
                meta = MetaAdsIntegration(
                    access_token=credentials['access_token'],
                    ad_account_id=credentials['ad_account_id']
                )
                
                # Test API call
                import aiohttp
                url = f"https://graph.facebook.com/v18.0/me"
                params = {'access_token': credentials['access_token']}
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            return True
                        return False
            
            elif platform == 'google':
                # Google credentials are tested when creating client
                from integration.platforms.google_ads import GoogleAdsIntegration
                
                google = GoogleAdsIntegration(credentials)
                google.set_customer(credentials['customer_id'])
                
                # If no exception, credentials are valid
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Credential test failed: {e}")
            return False

