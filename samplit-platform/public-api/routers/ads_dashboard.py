# public-api/routers/ads_dashboard.py

from fastapi import APIRouter, Depends
from public_api.routers.auth import get_current_user

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard(
    user_id: str = Depends(get_current_user),
    db = Depends(get_database)
):
    """Dashboard con métricas clave"""
    
    async with db.pool.acquire() as conn:
        # Active campaigns
        campaigns = await conn.fetch(
            """
            SELECT 
                c.*,
                SUM(cr.impressions) as total_impressions,
                SUM(cr.clicks) as total_clicks,
                SUM(cr.conversions) as total_conversions,
                SUM(cr.spend) as total_spend
            FROM ad_campaigns c
            LEFT JOIN ad_creatives cr ON c.id = cr.campaign_id
            WHERE c.user_id = $1 AND c.status = 'active'
            GROUP BY c.id
            """,
            user_id
        )
        
        # Recent optimization actions
        actions = await conn.fetch(
            """
            SELECT * FROM optimization_actions
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 10
            """,
            user_id
        )
    
    return {
        "campaigns": [dict(c) for c in campaigns],
        "recent_actions": [dict(a) for a in actions],
        "summary": {
            "active_campaigns": len(campaigns),
            "total_spend": sum(c['total_spend'] or 0 for c in campaigns),
            "total_conversions": sum(c['total_conversions'] or 0 for c in campaigns)
        }
    }
