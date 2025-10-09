"""
ADS API Router

Endpoints para gestión de campañas de ads con optimización automática.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from public_api.routers.auth import get_current_user
from data_access.database import get_database, DatabaseManager
from orchestration.services.platform_credentials_service import PlatformCredentialsService
from orchestration.services.ads_optimizer_service import AdsOptimizerService

router = APIRouter()

# ============================================
# MODELS
# ============================================

class ConnectMetaRequest(BaseModel):
    """Connect Meta Ads account"""
    access_token: str = Field(..., min_length=10)
    ad_account_id: str = Field(..., regex=r"^act_\d+$")

class ConnectGoogleRequest(BaseModel):
    """Connect Google Ads account"""
    developer_token: str
    client_id: str
    client_secret: str
    refresh_token: str
    customer_id: str = Field(..., regex=r"^\d{3}-\d{3}-\d{4}$")

class CreativeData(BaseModel):
    """Ad creative data"""
    headline: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    cta_text: str = Field(default="Learn More", max_length=50)

class OptimizationSettings(BaseModel):
    """Optimization settings"""
    enabled: bool = True
    strategy: str = Field(default="adaptive", regex="^(adaptive|fast_learning)$")
    min_samples_per_creative: int = Field(default=100, ge=10)
    confidence_threshold: float = Field(default=0.90, ge=0.80, le=0.99)
    auto_pause_losers: bool = True
    auto_scale_winners: bool = True

class CreateCampaignRequest(BaseModel):
    """Create ad campaign"""
    name: str = Field(..., min_length=3, max_length=255)
    platform: str = Field(..., regex="^(meta|google)$")
    campaign_objective: str = Field(
        default="conversions",
        regex="^(conversions|traffic|awareness)$"
    )
    daily_budget: float = Field(..., gt=0)
    target_url: str
    creatives: List[CreativeData] = Field(..., min_items=2, max_items=10)
    optimization: OptimizationSettings = OptimizationSettings()

class CampaignResponse(BaseModel):
    """Campaign response"""
    campaign_id: str
    name: str
    platform: str
    status: str
    daily_budget: float
    optimization_enabled: bool
    created_at: datetime

class CampaignAnalytics(BaseModel):
    """Campaign analytics"""
    campaign_id: str
    campaign_name: str
    platform: str
    status: str
    
    # Performance
    impressions: int
    clicks: int
    conversions: int
    spend: float
    ctr: float
    cpc: float
    cpa: float
    
    # Creatives
    creatives: List[Dict[str, Any]]
    
    # Optimization insights
    best_creative_id: Optional[str]
    best_creative_probability: Optional[float]
    recommendations: List[str]

# ============================================
# PLATFORM CONNECTIONS
# ============================================

@router.post("/integrations/meta")
async def connect_meta_account(
    request: ConnectMetaRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Connect Meta Ads account
    
    Saves encrypted credentials and tests connection.
    """
    
    credentials_service = PlatformCredentialsService(db)
    
    # Save credentials
    await credentials_service.save_credentials(
        user_id=user_id,
        platform='meta',
        credentials={
            'access_token': request.access_token,
            'ad_account_id': request.ad_account_id
        }
    )
    
    # Test connection
    is_valid = await credentials_service.test_credentials(user_id, 'meta')
    
    if not is_valid:
        # Rollback
        await credentials_service.delete_credentials(user_id, 'meta')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Meta Ads credentials"
        )
    
    return {
        "status": "connected",
        "platform": "meta",
        "ad_account_id": request.ad_account_id
    }

@router.post("/integrations/google")
async def connect_google_account(
    request: ConnectGoogleRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Connect Google Ads account
    
    Saves encrypted credentials and tests connection.
    """
    
    credentials_service = PlatformCredentialsService(db)
    
    # Save credentials
    await credentials_service.save_credentials(
        user_id=user_id,
        platform='google',
        credentials={
            'developer_token': request.developer_token,
            'client_id': request.client_id,
            'client_secret': request.client_secret,
            'refresh_token': request.refresh_token,
            'customer_id': request.customer_id
        }
    )
    
    # Test connection
    is_valid = await credentials_service.test_credentials(user_id, 'google')
    
    if not is_valid:
        await credentials_service.delete_credentials(user_id, 'google')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google Ads credentials"
        )
    
    return {
        "status": "connected",
        "platform": "google",
        "customer_id": request.customer_id
    }

@router.get("/integrations")
async def list_integrations(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """List connected platforms"""
    
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT platform, status, created_at, updated_at
            FROM platform_integrations
            WHERE user_id = $1
            """,
            user_id
        )
    
    return {
        "integrations": [dict(row) for row in rows]
    }

@router.delete("/integrations/{platform}")
async def disconnect_platform(
    platform: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Disconnect platform"""
    
    if platform not in ['meta', 'google']:
        raise HTTPException(400, "Invalid platform")
    
    credentials_service = PlatformCredentialsService(db)
    await credentials_service.delete_credentials(user_id, platform)
    
    return {"status": "disconnected", "platform": platform}

# ============================================
# CAMPAIGNS
# ============================================

@router.post("/campaigns", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    request: CreateCampaignRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Create optimized ad campaign
    
    Creates campaign with automatic Thompson Sampling optimization.
    """
    
    # Verify platform integration exists
    credentials_service = PlatformCredentialsService(db)
    credentials = await credentials_service.get_credentials(user_id, request.platform)
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No {request.platform} integration found. Connect your account first."
        )
    
    # Create campaign in DB
    async with db.pool.acquire() as conn:
        campaign_id = await conn.fetchval(
            """
            INSERT INTO ad_campaigns (
                user_id, name, platform, campaign_objective,
                daily_budget, original_daily_budget, target_url,
                optimization_enabled, optimization_strategy,
                min_samples_per_creative, confidence_threshold,
                auto_pause_losers, auto_scale_winners
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING id
            """,
            user_id, request.name, request.platform, request.campaign_objective,
            request.daily_budget, request.daily_budget, request.target_url,
            request.optimization.enabled, request.optimization.strategy,
            request.optimization.min_samples_per_creative,
            request.optimization.confidence_threshold,
            request.optimization.auto_pause_losers,
            request.optimization.auto_scale_winners
        )
        
        # Create creatives
        from engine.state.encryption import get_encryptor
        encryptor = get_encryptor()
        
        for creative_data in request.creatives:
            # Initial Thompson Sampling state
            initial_state = {
                'success_count': 1,
                'failure_count': 1,
                'samples': 0,
                'algorithm_type': 'bayesian'
            }
            
            encrypted_state = encryptor.encrypt_state(initial_state)
            
            await conn.execute(
                """
                INSERT INTO ad_creatives (
                    campaign_id, headline, description,
                    image_url, video_url, cta_text,
                    algorithm_state, state_version
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, 1)
                """,
                campaign_id,
                creative_data.headline,
                creative_data.description,
                creative_data.image_url,
                creative_data.video_url,
                creative_data.cta_text,
                encrypted_state
            )
    
    return CampaignResponse(
        campaign_id=str(campaign_id),
        name=request.name,
        platform=request.platform,
        status='draft',
        daily_budget=request.daily_budget,
        optimization_enabled=request.optimization.enabled,
        created_at=datetime.utcnow()
    )

@router.get("/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(
    platform: Optional[str] = None,
    status: Optional[str] = None,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """List user's campaigns"""
    
    query = "SELECT * FROM ad_campaigns WHERE user_id = $1"
    params = [user_id]
    
    if platform:
        query += f" AND platform = ${len(params) + 1}"
        params.append(platform)
    
    if status:
        query += f" AND status = ${len(params) + 1}"
        params.append(status)
    
    query += " ORDER BY created_at DESC"
    
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
    
    return [
        CampaignResponse(
            campaign_id=str(row['id']),
            name=row['name'],
            platform=row['platform'],
            status=row['status'],
            daily_budget=float(row['daily_budget']),
            optimization_enabled=row['optimization_enabled'],
            created_at=row['created_at']
        )
        for row in rows
    ]

@router.get("/campaigns/{campaign_id}/analytics", response_model=CampaignAnalytics)
async def get_campaign_analytics(
    campaign_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Get campaign analytics with Thompson Sampling insights
    """
    
    # Get campaign
    async with db.pool.acquire() as conn:
        campaign = await conn.fetchrow(
            """
            SELECT * FROM ad_campaigns
            WHERE id = $1 AND user_id = $2
            """,
            campaign_id, user_id
        )
    
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    
    # Get creatives with metrics
    async with db.pool.acquire() as conn:
        creatives = await conn.fetch(
            """
            SELECT * FROM ad_creatives
            WHERE campaign_id = $1
            ORDER BY ctr DESC
            """,
            campaign_id
        )
    
    # Calculate Thompson Sampling probabilities
    optimizer = AdsOptimizerService(db)
    creatives_list = [dict(c) for c in creatives]
    
    # Decrypt states for analysis
    from engine.state.encryption import get_encryptor
    encryptor = get_encryptor()
    
    for creative in creatives_list:
        if creative['algorithm_state']:
            creative['algorithm_state_decrypted'] = encryptor.decrypt_state(
                creative['algorithm_state']
            )
    
    probabilities = optimizer.calculate_probabilities(creatives_list)
    
    # Best creative
    best_creative_id = max(probabilities, key=probabilities.get) if probabilities else None
    best_probability = probabilities.get(best_creative_id, 0) if best_creative_id else None
    
    # Aggregate metrics
    total_impressions = sum(c['impressions'] for c in creatives)
    total_clicks = sum(c['clicks'] for c in creatives)
    total_conversions = sum(c['conversions'] for c in creatives)
    total_spend = sum(float(c['spend']) for c in creatives)
    
    avg_ctr = (total_clicks / total_impressions) if total_impressions > 0 else 0
    avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
    cpa = (total_spend / total_conversions) if total_conversions > 0 else 0
    
    # Generate recommendations
    recommendations = []
    
    if best_probability and best_probability > 0.9:
        best_name = next(c['headline'] for c in creatives if c['id'] == best_creative_id)
        recommendations.append(
            f"🏆 Clear winner: '{best_name}' ({best_probability:.1%} confidence)"
        )
    
    if avg_ctr < 0.01:
        recommendations.append(
            "⚠️ Low CTR (<1%). Consider testing new headlines or images."
        )
    
    if total_impressions < 1000:
        recommendations.append(
            "⏳ Not enough data yet. Continue running for better insights."
        )
    
    # Format creatives for response
    creatives_response = [
        {
            'id': str(c['id']),
            'headline': c['headline'],
            'description': c['description'],
            'status': c['status'],
            'impressions': c['impressions'],
            'clicks': c['clicks'],
            'conversions': c['conversions'],
            'spend': float(c['spend']),
            'ctr': float(c['ctr']),
            'cpc': float(c['cpc']),
            'thompson_probability': probabilities.get(c['id'], 0)
        }
        for c in creatives
    ]
    
    return CampaignAnalytics(
        campaign_id=str(campaign['id']),
        campaign_name=campaign['name'],
        platform=campaign['platform'],
        status=campaign['status'],
        impressions=total_impressions,
        clicks=total_clicks,
        conversions=total_conversions,
        spend=total_spend,
        ctr=avg_ctr,
        cpc=avg_cpc,
        cpa=cpa,
        creatives=creatives_response,
        best_creative_id=best_creative_id,
        best_creative_probability=best_probability,
        recommendations=recommendations
    )

@router.patch("/campaigns/{campaign_id}/status")
async def update_campaign_status(
    campaign_id: str,
    new_status: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Update campaign status"""
    
    if new_status not in ['draft', 'active', 'paused', 'completed', 'archived']:
        raise HTTPException(400, "Invalid status")
    
    async with db.pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE ad_campaigns
            SET status = $1, updated_at = NOW()
            WHERE id = $2 AND user_id = $3
            """,
            new_status, campaign_id, user_id
        )
    
    if result == "UPDATE 0":
        raise HTTPException(404, "Campaign not found")
    
    return {"status": new_status, "campaign_id": campaign_id}

@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Delete campaign (soft delete)"""
    
    async with db.pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE ad_campaigns
            SET status = 'archived', updated_at = NOW()
            WHERE id = $2 AND user_id = $3
            """,
            campaign_id, user_id
        )
    
    if result == "UPDATE 0":
        raise HTTPException(404, "Campaign not found")
    
    return {"status": "archived", "campaign_id": campaign_id}
