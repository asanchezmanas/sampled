# engine/core/strategies/fast_learning.py

"""
Fast Learning Strategy

Optimized for low-traffic scenarios.
Learns quickly with limited data.

Implementation: [CONFIDENTIAL - EXPLORATION-EXPLOITATION]
"""

from typing import List, Dict, Any
from ..base import BaseStrategy
from ..allocators._explore import ExploreExploitAllocator

class FastLearningStrategy(BaseStrategy):
    """
    Fast learning strategy for low traffic
    
    - Optimized for quick learning
    - Works well with < 1000 visitors
    - Balances exploration aggressively
    
    Use case: Low traffic experiments, new tests
    
    Implementation details are proprietary.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "fast_learning"
        
        # Configure for low traffic
        fast_config = {
            **config,
            'exploration': config.get('exploration', 0.15),  # Higher exploration
            'decay': config.get('decay', 0.99),  # Slower decay
            'min_exploration': 0.05
        }
        
        self.allocator = ExploreExploitAllocator(fast_config)
    
    async def select(self, 
                    options: List[Dict[str, Any]], 
                    context: Dict[str, Any]) -> str:
        """
        Select variant optimized for fast learning
        
        Uses enhanced exploration strategy for
        quick convergence with limited data.
        """
        selected_id = await self.allocator.select(options, context)
        
        self.logger.info(
            "Fast learning allocation",
            variant=selected_id,
            method="samplit-fast"
        )
        
        return selected_id
    
    async def update(self, 
                    option_id: str, 
                    reward: float,
                    context: Dict[str, Any]) -> None:
        """Update with result"""
        await self.allocator.update(option_id, reward, context)
    
    def get_insights(self) -> Dict[str, Any]:
        """Get strategy insights"""
        return {
            "strategy": "fast_learning",
            "type": "low_traffic_optimized",
            "adaptive": True,
            "learning_enabled": True,
            "optimized_for": "< 1000 daily visitors",
            "description": "Fast learning with enhanced exploration"
        }
