# orchestration/services/notification_optimizer.py

from typing import List, Dict, Any, Optional
from data_access.database import DatabaseManager
from orchestration.factories.optimizer_factory import OptimizerFactory
from orchestration.interfaces.optimization_interface import OptimizationStrategy
import logging

class NotificationOptimizationService:
    """
    Push notification optimization service
    
    Optimizes:
    - Message content
    - Send timing
    - Personalization
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        
        # Use hybrid strategy (Thompson + Epsilon for low engagement)
        self.content_optimizer = OptimizerFactory.create(
            OptimizationStrategy.HYBRID
        )
        
        # Time optimization might need different strategy
        self.time_optimizer = OptimizerFactory.create(
            OptimizationStrategy.FAST_LEARNING
        )
        self.logger = logging.getLogger(__name__)
    
    async def get_optimal_notification(self,
                                      campaign_id: str,
                                      user_profile: Dict) -> Dict:
        """
        Get optimal notification variant and send time
        """
        
        # Optimize content
        content_variants = await self.db.get_notification_variants(campaign_id)
        
        selected_content = await self.content_optimizer.select(
            options=content_variants,
            context={'user': user_profile, 'type': 'content'}
        )
        
        # Optimize timing
        time_options = self._generate_time_windows(user_profile)
        
        optimal_time = await self.time_optimizer.select(
            options=time_options,
            context={'user': user_profile, 'type': 'timing'}
        )
        
        return {
            'content_variant_id': selected_content,
            'optimal_send_time': optimal_time,
            'personalization': self._apply_personalization(
                selected_content, 
                user_profile
            )
        }
    
    def _generate_time_windows(self, user_profile: Dict) -> List[Dict]:
        """
        Generate candidate send time windows based on user behavior
        
        Uses historical engagement patterns
        """
        timezone = user_profile.get('timezone', 'UTC')
        historical_engagement = user_profile.get('engagement_by_hour', {})
        
        # Define time windows (hourly slots)
        time_windows = []
        for hour in range(24):
            time_windows.append({
                'id': f'hour_{hour}',
                'hour': hour,
                'timezone': timezone,
                'historical_engagement': historical_engagement.get(str(hour), 0),
                'performance': historical_engagement.get(str(hour), 0)
            })
        
        return time_windows
    
    async def record_notification_outcome(self,
                                         variant_id: str,
                                         time_window_id: str,
                                         outcome: str,  # 'delivered', 'opened', 'clicked', 'converted'
                                         user_profile: Dict):
        """
        Record notification outcome for learning
        """
        
        # Reward mapping
        reward_map = {
            'delivered': 0.1,
            'opened': 0.4,
            'clicked': 0.7,
            'converted': 1.0,
            'dismissed': -0.1,
            'unsubscribed': -1.0
        }
        
        reward = reward_map.get(outcome, 0.0)
        
        # Update both optimizers
        await self.content_optimizer.update(
            option_id=variant_id,
            reward=reward,
            context={'user': user_profile, 'type': 'content'}
        )
        
        await self.time_optimizer.update(
            option_id=time_window_id,
            reward=reward,
            context={'user': user_profile, 'type': 'timing'}
        )
