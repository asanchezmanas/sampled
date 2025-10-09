# integration/platforms/meta_ads.py

import aiohttp
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class MetaAdsIntegration:
    """Integración simplificada con Meta Ads API"""
    
    def __init__(self, access_token: str, ad_account_id: str):
        self.access_token = access_token
        self.ad_account_id = ad_account_id
        self.base_url = "https://graph.facebook.com/v18.0"
    
    async def get_ad_insights(
        self,
        ad_id: str,
        date_preset: str = 'last_7d'
    ) -> Dict[str, Any]:
        """Obtener métricas de un ad"""
        
        url = f"{self.base_url}/{ad_id}/insights"
        params = {
            'access_token': self.access_token,
            'date_preset': date_preset,
            'fields': 'impressions,clicks,spend,actions,ctr,cpc'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                result = await response.json()
                
                if not result.get('data'):
                    return {
                        'impressions': 0,
                        'clicks': 0,
                        'conversions': 0,
                        'spend': 0,
                        'ctr': 0,
                        'cpc': 0
                    }
                
                data = result['data'][0]
                
                # Extract conversions from actions
                conversions = 0
                if 'actions' in data:
                    for action in data['actions']:
                        if action['action_type'] in ['purchase', 'lead', 'complete_registration']:
                            conversions += int(action['value'])
                
                return {
                    'impressions': int(data.get('impressions', 0)),
                    'clicks': int(data.get('clicks', 0)),
                    'conversions': conversions,
                    'spend': float(data.get('spend', 0)),
                    'ctr': float(data.get('ctr', 0)),
                    'cpc': float(data.get('cpc', 0))
                }
    
    async def pause_ad(self, ad_id: str):
        """Pausar ad"""
        url = f"{self.base_url}/{ad_id}"
        
        async with aiohttp.ClientSession() as session:
            data = {
                'status': 'PAUSED',
                'access_token': self.access_token
            }
            await session.post(url, data=data)
            
        logger.info(f"Paused ad: {ad_id}")
    
    async def activate_ad(self, ad_id: str):
        """Activar ad"""
        url = f"{self.base_url}/{ad_id}"
        
        async with aiohttp.ClientSession() as session:
            data = {
                'status': 'ACTIVE',
                'access_token': self.access_token
            }
            await session.post(url, data=data)
            
        logger.info(f"Activated ad: {ad_id}")
