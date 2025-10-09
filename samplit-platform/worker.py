# worker.py

"""
Background worker para optimización automática de ads
"""

import asyncio
from data_access.database import DatabaseManager
from orchestration.services.ads_auto_optimizer import AdsAutoOptimizer
from integration.platforms.meta_ads import MetaAdsIntegration
from integration.platforms.google_ads import GoogleAdsIntegration
import os

async def main():
    # Initialize
    db = DatabaseManager()
    await db.initialize()
    
    # Platform integrations
    meta = MetaAdsIntegration(
        access_token=os.getenv('META_ACCESS_TOKEN'),
        ad_account_id=os.getenv('META_AD_ACCOUNT_ID')
    )
    
    google = GoogleAdsIntegration(
        config_path='google-ads.yaml'
    )
    
    # Start optimizer
    optimizer = AdsAutoOptimizer(db, meta, google)
    await optimizer.start()

if __name__ == "__main__":
    asyncio.run(main())
