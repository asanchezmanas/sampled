# orchestration/services/email_optimizer.py

class EmailOptimizationService:
    """
    Email testing and optimization service
    
    Uses Samplit's adaptive algorithms to optimize:
    - Subject lines
    - Send times
    - Content variants
    - From names
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.optimizer = OptimizerFactory.create(
            OptimizationStrategy.ADAPTIVE
        )
    
    async def select_email_variant(self, 
                                   campaign_id: str,
                                   recipient_context: Dict) -> Dict:
        """
        Select optimal email variant for recipient
        
        This uses Samplit's adaptive algorithm to learn
        which email combinations work best.
        """
        
        # Get available variants
        variants = await self.db.get_email_variants(campaign_id)
        
        # Prepare for optimization
        options = [
            {
                'id': v['id'],
                'subject': v['subject'],
                'content_id': v['content_id'],
                'performance': await self._get_performance(v['id'])
            }
            for v in variants
        ]
        
        # Select using Samplit engine 
        selected_id = await self.optimizer.select(options, recipient_context)
        
        selected_variant = next(v for v in variants if v['id'] == selected_id)
        
        return selected_variant
    
    async def record_email_action(self,
                                  variant_id: str,
                                  action: str,  # 'open', 'click', 'convert'
                                  recipient_context: Dict):
        """
        Record email action (open, click, conversion)
        """
        
        # Calcular reward según action
        reward = {
            'open': 0.3,
            'click': 0.7,
            'convert': 1.0
        }.get(action, 0.0)
        
        # Update optimizer
        await self.optimizer.update(variant_id, reward, recipient_context)
        
        # Persist to DB
        await self.db.record_email_performance(
            variant_id=variant_id,
            action=action,
            reward=reward,
            context=recipient_context
        )
