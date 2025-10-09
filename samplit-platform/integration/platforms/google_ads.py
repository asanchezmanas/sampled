# integration/platforms/google_ads.py

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from typing import Dict, Any, List

class GoogleAdsIntegration:
    """
    Integración con Google Ads API
    
    Docs: https://developers.google.com/google-ads/api/docs/start
    """
    
    def __init__(self, config_path: str):
        """
        Initialize Google Ads client
        
        config_path: Path to google-ads.yaml
        """
        self.client = GoogleAdsClient.load_from_storage(config_path)
        self.customer_id = None  # Set per user
    
    def set_customer(self, customer_id: str):
        """Set customer ID for operations"""
        self.customer_id = customer_id.replace('-', '')
    
    async def create_campaign(
        self,
        name: str,
        budget_amount_micros: int,  # Budget in micros (1 USD = 1,000,000 micros)
        advertising_channel_type: str = 'SEARCH'
    ) -> str:
        """
        Crear campaña en Google Ads
        """
        campaign_service = self.client.get_service("CampaignService")
        campaign_budget_service = self.client.get_service("CampaignBudgetService")
        
        # Create budget
        budget_operation = self.client.get_type("CampaignBudgetOperation")
        budget = budget_operation.create
        budget.name = f"Budget for {name}"
        budget.amount_micros = budget_amount_micros
        budget.delivery_method = self.client.enums.BudgetDeliveryMethodEnum.STANDARD
        
        budget_response = campaign_budget_service.mutate_campaign_budgets(
            customer_id=self.customer_id,
            operations=[budget_operation]
        )
        
        budget_resource_name = budget_response.results[0].resource_name
        
        # Create campaign
        campaign_operation = self.client.get_type("CampaignOperation")
        campaign = campaign_operation.create
        campaign.name = name
        campaign.advertising_channel_type = getattr(
            self.client.enums.AdvertisingChannelTypeEnum,
            advertising_channel_type
        )
        campaign.status = self.client.enums.CampaignStatusEnum.PAUSED
        campaign.campaign_budget = budget_resource_name
        campaign.bidding_strategy_type = (
            self.client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSIONS
        )
        
        campaign_response = campaign_service.mutate_campaigns(
            customer_id=self.customer_id,
            operations=[campaign_operation]
        )
        
        return campaign_response.results[0].resource_name
    
    async def create_ad_group_ad(
        self,
        ad_group_resource_name: str,
        headlines: List[str],
        descriptions: List[str],
        final_url: str
    ) -> str:
        """
        Crear ad en Google Ads (Responsive Search Ad)
        """
        ad_group_ad_service = self.client.get_service("AdGroupAdService")
        
        ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
        ad_group_ad = ad_group_ad_operation.create
        ad_group_ad.ad_group = ad_group_resource_name
        ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.PAUSED
        
        # Responsive Search Ad
        ad = ad_group_ad.ad
        ad.responsive_search_ad.path1 = "deals"
        ad.responsive_search_ad.path2 = "sale"
        ad.final_urls.append(final_url)
        
        # Add headlines (max 15)
        for headline_text in headlines[:15]:
            headline = self.client.get_type("AdTextAsset")
            headline.text = headline_text
            ad.responsive_search_ad.headlines.append(headline)
        
        # Add descriptions (max 4)
        for description_text in descriptions[:4]:
            description = self.client.get_type("AdTextAsset")
            description.text = description_text
            ad.responsive_search_ad.descriptions.append(description)
        
        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=self.customer_id,
            operations=[ad_group_ad_operation]
        )
        
        return response.results[0].resource_name
    
    async def get_ad_performance(
        self,
        ad_resource_name: str
    ) -> Dict[str, Any]:
        """
        Obtener métricas de performance de un ad
        
        Esto alimenta al algoritmo Thompson Sampling.
        """
        ga_service = self.client.get_service("GoogleAdsService")
        
        query = f"""
            SELECT
                ad_group_ad.ad.id,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.cost_micros,
                metrics.ctr,
                metrics.average_cpc
            FROM ad_group_ad
            WHERE ad_group_ad.resource_name = '{ad_resource_name}'
            AND segments.date DURING TODAY
        """
        
        try:
            response = ga_service.search(
                customer_id=self.customer_id,
                query=query
            )
            
            for row in response:
                return {
                    'impressions': row.metrics.impressions,
                    'clicks': row.metrics.clicks,
                    'conversions': row.metrics.conversions,
                    'cost_micros': row.metrics.cost_micros,
                    'ctr': row.metrics.ctr,
                    'average_cpc': row.metrics.average_cpc
                }
            
            return {
                'impressions': 0,
                'clicks': 0,
                'conversions': 0,
                'cost_micros': 0,
                'ctr': 0,
                'average_cpc': 0
            }
            
        except GoogleAdsException as ex:
            print(f"Request failed: {ex}")
            return None
    
    async def update_ad_status(
        self,
        ad_resource_name: str,
        status: str  # 'ENABLED', 'PAUSED', 'REMOVED'
    ):
        """
        Actualizar status de ad
        
        Usado para pausar underperformers o activar winners.
        """
        ad_group_ad_service = self.client.get_service("AdGroupAdService")
        
        ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
        ad_group_ad = ad_group_ad_operation.update
        ad_group_ad.resource_name = ad_resource_name
        ad_group_ad.status = getattr(
            self.client.enums.AdGroupAdStatusEnum,
            status
        )
        
        field_mask = self.client.get_type("FieldMask")
        field_mask.paths.append("status")
        ad_group_ad_operation.update_mask.CopyFrom(field_mask)
        
        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=self.customer_id,
            operations=[ad_group_ad_operation]
        )
        
        return response
