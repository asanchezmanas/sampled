# Backend: orchestration/services/integration_service.py

class IntegrationService:
    async def connect_meta_account(
        self,
        user_id: str,
        access_token: str,
        ad_account_id: str
    ):
        """
        Conectar cuenta de Meta Ads
        """
        # Verificar que el token funciona
        meta = MetaAdsIntegration(access_token, ad_account_id)
        
        try:
            # Test API call
            await meta.get_account_info()
        except Exception as e:
            raise HTTPException(400, f"Invalid credentials: {e}")
        
        # Guardar credenciales (cifradas)
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO platform_integrations (
                    user_id, platform, credentials, status
                ) VALUES ($1, 'meta', $2, 'active')
                ON CONFLICT (user_id, platform) 
                DO UPDATE SET credentials = $2, status = 'active'
                """,
                user_id,
                self.encrypt_credentials({
                    'access_token': access_token,
                    'ad_account_id': ad_account_id
                })
            )
        
        return {"status": "connected", "platform": "meta"}
