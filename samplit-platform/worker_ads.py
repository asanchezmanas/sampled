# worker_ads.py

"""
Background worker para optimización de ADS
"""

import asyncio
import logging
import os
from datetime import datetime

from data_access.database import DatabaseManager
from orchestration.services.ads_optimizer_service import AdsOptimizerService
from integration.platforms.meta_ads import MetaAdsIntegration

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def optimization_cycle(db: DatabaseManager):
    """Un ciclo de optimización"""
    
    logger.info("🤖 Starting optimization cycle...")
    
    # Get active campaigns
    async with db.pool.acquire() as conn:
        campaigns = await conn.fetch(
            """
            SELECT * FROM ad_campaigns
            WHERE status = 'active' AND optimization_enabled = true
            """
        )
    
    logger.info(f"Found {len(campaigns)} campaigns to optimize")
    
    # Optimize each campaign
    optimizer = AdsOptimizerService(db)
    
    for campaign in campaigns:
        try:
            # Get platform integration
            async with db.pool.acquire() as conn:
                integration = await conn.fetchrow(
                    """
                    SELECT * FROM platform_integrations
                    WHERE user_id = $1 AND platform = $2
                    """,
                    campaign['user_id'],
                    campaign['platform']
                )
            
            if not integration:
                logger.warning(f"No integration for campaign {campaign['id']}")
                continue
            
            # Pull latest metrics from platform
            if campaign['platform'] == 'meta':
                await pull_meta_metrics(campaign, integration)
            
            # Optimize
            await optimizer.optimize_campaign(dict(campaign))
            
        except Exception as e:
            logger.error(f"Failed to optimize campaign {campaign['id']}: {e}")
    
    logger.info("✅ Optimization cycle completed")

async def pull_meta_metrics(campaign: Dict, integration: Dict):
    """Pull metrics from Meta Ads"""
    
    from engine.state.encryption import get_encryptor
    
    # Decrypt credentials
    encryptor = get_encryptor()
    credentials = encryptor.decrypt_state(integration['credentials'])
    
    # Initialize Meta API
    meta = MetaAdsIntegration(
        access_token=credentials['access_token'],
        ad_account_id=credentials['ad_account_id']
    )
    
    # Get creatives
    db = DatabaseManager()
    await db.initialize()
    
    async with db.pool.acquire() as conn:
        creatives = await conn.fetch(
            "SELECT * FROM ad_creatives WHERE campaign_id = $1",
            campaign['id']
        )
    
    # Pull metrics for each
    for creative in creatives:
        if not creative['platform_ad_id']:
            continue
        
        try:
            insights = await meta.get_ad_insights(creative['platform_ad_id'])
            
            # Update DB
            async with db.pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE ad_creatives
                    SET 
                        impressions = $1,
                        clicks = $2,
                        conversions = $3,
                        spend = $4,
                        ctr = $5,
                        cpc = $6,
                        updated_at = NOW()
                    WHERE id = $7
                    """,
                    insights['impressions'],
                    insights['clicks'],
                    insights['conversions'],
                    insights['spend'],
                    insights['ctr'],
                    insights['cpc'],
                    creative['id']
                )
        except Exception as e:
            logger.error(f"Failed to pull metrics for creative {creative['id']}: {e}")

async def main():
    """Main worker loop"""
    
    logger.info("🚀 ADS Optimizer Worker starting...")
    
    # Initialize DB
    db = DatabaseManager()
    await db.initialize()
    
    # Get optimization interval
    interval_minutes = int(os.getenv('OPTIMIZATION_INTERVAL_MINUTES', 60))
    
    logger.info(f"Optimization interval: {interval_minutes} minutes")
    
    while True:
        try:
            await optimization_cycle(db)
            
            # Wait for next cycle
            await asyncio.sleep(interval_minutes * 60)
            
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(300)  # Retry in 5 min

if __name__ == "__main__":
    asyncio.run(main())
