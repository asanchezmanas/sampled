# engine/core/strategies/adaptive.py

"""
Adaptive Strategy

Uses Bayesian inference for intelligent traffic allocation.

Implementation: [CONFIDENTIAL - BAYESIAN OPTIMIZATION]
"""
from typing import List, Dict, Any
from ..base import BaseStrategy
from ..allocators._bayesian import AdaptiveBayesianAllocator
from ..allocators._explore import ExploreExploitAllocator
import logging

class AdaptiveStrategy(BaseStrategy):
    """
    Adaptive optimization strategy
    
    - Learns from results in real-time
    - Allocates more traffic to winners
    - Balances exploration vs exploitation
    
    Use case: Standard experiments with normal traffic
    
    Implementation details are proprietary.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "adaptive"
        
        # Internal allocator (implementation hidden)
        self.allocator = AdaptiveBayesianAllocator(config)
    
    async def select(self, 
                    options: List[Dict[str, Any]], 
                    context: Dict[str, Any]) -> str:
        """
        Select variant using adaptive algorithm
        
        This learns which variants perform best and
        automatically allocates more traffic to winners.
        """
        selected_id = await self.allocator.select(options, context)
        
        self.logger.info(
            "Adaptive allocation",
            variant=selected_id,
            method="samplit-adaptive"  # Generic name
        )
        
        return selected_id
    
    async def update(self, 
                    option_id: str, 
                    reward: float,
                    context: Dict[str, Any]) -> None:
        """
        Update algorithm with observed result
        
        This is where the learning happens.
        """
        await self.allocator.update(option_id, reward, context)
    
    def get_insights(self) -> Dict[str, Any]:
        """Get strategy insights"""
        return {
            "strategy": "adaptive",
            "type": "intelligent_allocation",
            "adaptive": True,
            "learning_enabled": True,
            "description": "Bayesian adaptive optimization"
        }
