# orchestration/services/ads_optimizer.py

class AdsCreativeOptimizer:
    """
    Optimiza creativos de ads usando Thompson Sampling
    
    En lugar de optimizar elementos HTML, optimizamos ad creatives.
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        # Mismo optimizador que usamos para web
        self.optimizer = OptimizerFactory.create(
            OptimizationStrategy.ADAPTIVE  # Thompson Sampling
        )
    
    async def get_ad_insights(
        self,
        ad_id: str,
        date_preset: str = 'today'
    ) -> Dict[str, Any]:
        """
        Obtener métricas de performance de un ad
        
        Esto es lo que alimenta al algoritmo Thompson Sampling.
        """
        url = f"{self.base_url}/{ad_id}/insights"
        
        params = {
            'access_token': self.access_token,
            'date_preset': date_preset,
            'fields': 'impressions,clicks,spend,conversions,ctr,cpc'
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
                return {
                    'impressions': int(data.get('impressions', 0)),
                    'clicks': int(data.get('clicks', 0)),
                    'conversions': int(data.get('conversions', 0)),
                    'spend': float(data.get('spend', 0)),
                    'ctr': float(data.get('ctr', 0)),
                    'cpc': float(data.get('cpc', 0))
                }
    
    async def update_ad_budget(
        self,
        adset_id: str,
        new_daily_budget: int
    ):
        """
        Actualizar presupuesto de ad set
        
        Usado por el algoritmo para asignar más presupuesto a winners.
        """
        url = f"{self.base_url}/{adset_id}"
        
        async with aiohttp.ClientSession() as session:
            data = {
                'daily_budget': new_daily_budget,
                'access_token': self.access_token
            }
            
            async with session.post(url, data=data) as response:
                return await response.json()
    
    async def pause_ad(self, ad_id: str):
        """Pausar ad underperformer"""
        url = f"{self.base_url}/{ad_id}"
        
        async with aiohttp.ClientSession() as session:
            data = {
                'status': 'PAUSED',
                'access_token': self.access_token
            }
            await session.post(url, data=data)
    
    async def activate_ad(self, ad_id: str):
        """Activar ad winner"""
        url = f"{self.base_url}/{ad_id}"
        
        async with aiohttp.ClientSession() as session:
            data = {
                'status': 'ACTIVE',
                'access_token': self.access_token
            }
            await session.post(url, data=data)
