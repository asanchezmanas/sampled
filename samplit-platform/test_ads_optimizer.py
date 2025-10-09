# test_ads_optimizer.py

import asyncio
from data_access.database import DatabaseManager
from orchestration.services.ads_optimizer_service import AdsOptimizerService

async def test_optimizer():
    """Test básico del optimizer"""
    
    db = DatabaseManager()
    await db.initialize()
    
    # Create test campaign
    async with db.pool.acquire() as conn:
        campaign_id = await conn.fetchval(
            """
            INSERT INTO ad_campaigns (
                user_id, name, platform, campaign_objective,
                daily_budget, original_daily_budget,
                optimization_enabled
            ) VALUES (
                'test-user-id', 'Test Campaign', 'meta', 'conversions',
                100, 100, true
            ) RETURNING id
            """
        )
        
        # Create test creatives
        for i in range(3):
            await conn.execute(
                """
                INSERT INTO ad_creatives (
                    campaign_id, headline, impressions, clicks, conversions
                ) VALUES ($1, $2, $3, $4, $5)
                """,
                campaign_id,
                f"Creative {i+1}",
                1000 + i*500,
                50 + i*20,
                5 + i*3
            )
    
    # Run optimizer
    optimizer = AdsOptimizerService(db)
    
    campaign = await conn.fetchrow(
        "SELECT * FROM ad_campaigns WHERE id = $1",
        campaign_id
    )
    
    await optimizer.optimize_campaign(dict(campaign))
    
    print("✅ Test completed")

if __name__ == "__main__":
    asyncio.run(test_optimizer())
