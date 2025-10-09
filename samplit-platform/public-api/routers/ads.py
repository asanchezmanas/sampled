# public-api/routers/ads.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

from public_api.routers.auth import get_current_user
from data_access.database import get_database, DatabaseManager

router = APIRouter()

class CreateAdCampaignRequest(BaseModel):
    name: str
    platform: str  # 'meta' or 'google'
    campaign_objective: str  # 'conversions', 'traffic', 'awareness'
    daily_budget: float
    
    # Platform credentials
    meta_access_token: Optional[str] = None
    meta_ad_account_id: Optional[str] = None
    google_customer_id: Optional[str] = None

class CreateAdCreativeRequest(BaseModel):
    campaign_id: str
    headline: str
    description: str
    image_url: Optional[str] = None
    cta_text: Optional[str] = "Learn More"

@router.post("/campaigns")
async def create_ad_campaign(
    request: CreateAdCampaignRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Crear campaña de ads con optimización automática
    """
    # Create in DB
    async with db.pool.acquire() as conn:
        campaign_id = await conn.fetchval(
            """
            INSERT INTO ad_campaigns (
                user_id, name, platform, campaign_objective,
                daily_budget, optimization_enabled
            ) VALUES ($1, $2, $3, $4, $5, true)
            RETURNING id
            """,
            user_id, request.name, request.platform,
            request.campaign_objective, request.daily_budget
        )
    
    # Create on platform (Meta or Google)
    if request.platform == 'meta':
        from integration.platforms.meta_ads import MetaAdsIntegration
        
        meta = MetaAdsIntegration(
            access_token=request.meta_access_token,
            ad_account_id=request.meta_ad_account_id
        )
        
        platform_campaign_id = await meta.create_campaign(
            name=request.name,
            objective='CONVERSIONS',
            daily_budget=int(request.daily_budget * 100)  # Cents
        )
        
        # Store platform ID
        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE ad_campaigns
                SET platform_campaign_id = $1
                WHERE id = $2
                """,
                platform_campaign_id, campaign_id
            )
    
    return {
        "campaign_id": str(campaign_id),
        "status": "created",
        "message": "Campaign created with automatic optimization enabled"
    }

@router.post("/campaigns/{campaign_id}/creatives")
async def create_ad_creative(
    campaign_id: str,
    request: CreateAdCreativeRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Crear creative para campaña
    
    El algoritmo Thompson Sampling decidirá automáticamente
    cuándo mostrar cada creative.
    """
    # Verify ownership
    async with db.pool.acquire() as conn:
        campaign = await conn.fetchrow(
            "SELECT * FROM ad_campaigns WHERE id = $1 AND user_id = $2",
            campaign_id, user_id
        )
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Create creative
    async with db.pool.acquire() as conn:
        creative_id = await conn.fetchval(
            """
            INSERT INTO ad_creatives (
                campaign_id, headline, description,
                image_url, cta_text, algorithm_state
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            campaign_id, request.headline, request.description,
            request.image_url, request.cta_text,
            None  # Algorithm state will be initialized on first optimization cycle
        )
    
    return {
        "creative_id": str(creative_id),
        "status": "created",
        "message": "Creative added to campaign"
    }

@router.get("/campaigns/{campaign_id}/analytics")
async def get_campaign_analytics(
    campaign_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Analytics de campaña con insights de Thompson Sampling
    """
    # Get campaign
    async with db.pool.acquire() as conn:
        campaign = await conn.fetchrow(
            "SELECT * FROM ad_campaigns WHERE id = $1 AND user_id = $2",
            campaign_id, user_id
        )
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get creatives performance
    async with db.pool.acquire() as conn:
        creatives = await conn.fetch(
            """
            SELECT 
                id, headline, description,
                impressions, clicks, conversions,
                ctr, cpc
            FROM ad_creatives
            WHERE campaign_id = $1
            ORDER BY ctr DESC
            """,
            campaign_id
        )
    
    return {
        "campaign": dict(campaign),
        "creatives": [dict(c) for c in creatives],
        "optimization_active": campaign['optimization_enabled'],
        "total_spend": sum(c['cpc'] * c['clicks'] for c in creatives),
        "best_creative": dict(creatives[0]) if creatives else None
    }
