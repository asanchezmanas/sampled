# engine/core/strategies/sequential.py

"""
Sequential Strategy

Multi-step optimization for funnels.

⭐ COMPETITIVE ADVANTAGE - Funnel path optimization

Implementation: [CONFIDENTIAL - PATENT PENDING]
"""

from typing import List, Dict, Any
from ..base import BaseStrategy
from ..allocators._sequential import SequentialAllocator

class SequentialStrategy(BaseStrategy):
    """
    Sequential multi-step strategy
    
    - Optimizes entire funnel paths
    - Learns which combinations work best
    - Step-by-step AND path-level optimization
    
    ⭐ This is our killer feature for funnel optimization
    
    Use case: Multi-step funnels, user journeys
    
    Implementation details are highly confidential.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "sequential"
        
        # Configure for funnel optimization
        funnel_config = {
            **config,
            'use_context': True,
            'max_steps': config.get('max_steps', 20),
            'learning_rate': config.get('learning_rate', 0.15)
        }
        
        self.allocator = SequentialAllocator(funnel_config)
    
    async def select(self, 
                    options: List[Dict[str, Any]], 
                    context: Dict[str, Any]) -> str:
        """
        Select variant considering full funnel path
        
        This is where the magic happens - we don't just
        optimize individual steps, we optimize entire paths.
        
        Context must include:
        - step_id: Current funnel step
        - previous_selections: Variants selected in previous steps
        """
        if 'step_id' not in context:
            raise ValueError("Sequential strategy requires 'step_id' in context")
        
        selected_id = await self.allocator.select(options, context)
        
        self.logger.info(
            "Sequential allocation",
            variant=selected_id,
            step=context.get('step_id'),
            method="samplit-funnel"
        )
        
        return selected_id
    
    async def update(self, 
                    option_id: str, 
                    reward: float,
                    context: Dict[str, Any]) -> None:
        """
        Update with step or final conversion
        
        Updates both step-level and path-level performance
        """
        await self.allocator.update(option_id, reward, context)
    
    def get_funnel_insights(self) -> Dict[str, Any]:
        """
        Get funnel-specific insights
        
        Returns top performing paths, bottlenecks, etc.
        """
        return self.allocator.get_funnel_insights()
    
    def get_insights(self) -> Dict[str, Any]:
        """Get strategy insights"""
        return {
            "strategy": "sequential",
            "type": "multi_step_funnel",
            "adaptive": True,
            "learning_enabled": True,
            "path_optimization": True,
            "competitive_advantage": True,
            "description": "Multi-step path optimization for funnels"
        }
