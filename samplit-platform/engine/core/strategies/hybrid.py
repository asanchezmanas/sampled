# engine/core/strategies/hybrid.py

"""
Hybrid Strategy

Auto-selects between Thompson Sampling and Epsilon-Greedy
based on traffic and performance patterns.

Implementation: [CONFIDENTIAL]
"""

from typing import List, Dict, Any
from ..base import BaseStrategy
from ..allocators._bayesian import AdaptiveBayesianAllocator
from ..allocators._explore import ExploreExploitAllocator

class HybridStrategy(BaseStrategy):
    """
    Hybrid adaptive strategy
    
    - Starts with Thompson Sampling
    - Switches to Epsilon-Greedy if traffic is too low
    - Auto-adjusts based on performance
    
    Use case: Unknown traffic patterns, adaptive optimization
    
    Implementation details are proprietary.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "hybrid"
        
        # Thresholds
        self.low_traffic_threshold = config.get('low_traffic_threshold', 50)
        self.switch_interval = config.get('switch_interval', 100)
        
        # Create both allocators
        self.thompson = AdaptiveBayesianAllocator(config)
        self.epsilon = ExploreExploitAllocator(config)
        
        # Current allocator
        self.current_allocator = self.thompson
        self.current_mode = "adaptive"
        
        # Stats
        self._total_samples = 0
        self._switches = 0
    
    async def select(
        self, 
        options: List[Dict[str, Any]], 
        context: Dict[str, Any]
    ) -> str:
        """
        Select using adaptive algorithm choice
        
        Automatically switches between Thompson and Epsilon
        based on traffic patterns.
        """
        
        # Check if we should switch modes
        if self._should_switch_mode(options):
            self._switch_mode(options)
        
        # Select using current allocator
        selected_id = await self.current_allocator.select(options, context)
        
        self._total_samples += 1
        
        self.logger.info(
            f"Hybrid selection (mode: {self.current_mode})",
            variant=selected_id,
            method="samplit-hybrid"
        )
        
        return selected_id
    
    async def update(
        self, 
        option_id: str, 
        reward: float,
        context: Dict[str, Any]
    ) -> None:
        """Update both allocators"""
        
        # Update current allocator
        await self.current_allocator.update(option_id, reward, context)
        
        # Also update the other one to keep it in sync
        other_allocator = (
            self.epsilon if self.current_allocator is self.thompson 
            else self.thompson
        )
        await other_allocator.update(option_id, reward, context)
    
    def _should_switch_mode(self, options: List[Dict[str, Any]]) -> bool:
        """Determine if we should switch allocation mode"""
        
        # Check every N samples
        if self._total_samples % self.switch_interval != 0:
            return False
        
        # Calculate total traffic
        total_samples = sum(
            opt.get('samples', 0) 
            for opt in options
        )
        
        # Low traffic -> use Epsilon-Greedy
        if total_samples < self.low_traffic_threshold:
            return self.current_mode != "fast_learning"
        
        # Normal traffic -> use Thompson
        return self.current_mode != "adaptive"
    
    def _switch_mode(self, options: List[Dict[str, Any]]) -> None:
        """Switch between modes"""
        
        total_samples = sum(
            opt.get('samples', 0) 
            for opt in options
        )
        
        if total_samples < self.low_traffic_threshold:
            # Switch to Epsilon-Greedy
            if self.current_allocator is not self.epsilon:
                self.current_allocator = self.epsilon
                self.current_mode = "fast_learning"
                self._switches += 1
                self.logger.info(
                    f"Switched to fast learning mode "
                    f"(low traffic: {total_samples} samples)"
                )
        else:
            # Switch to Thompson Sampling
            if self.current_allocator is not self.thompson:
                self.current_allocator = self.thompson
                self.current_mode = "adaptive"
                self._switches += 1
                self.logger.info(
                    f"Switched to adaptive mode "
                    f"(sufficient traffic: {total_samples} samples)"
                )
    
    def get_insights(self) -> Dict[str, Any]:
        """Get hybrid strategy insights"""
        return {
            "strategy": "hybrid",
            "type": "auto_adaptive",
            "current_mode": self.current_mode,
            "total_samples": self._total_samples,
            "mode_switches": self._switches,
            "adaptive": True,
            "learning_enabled": True,
            "description": f"Hybrid strategy (currently in {self.current_mode} mode)"
        }


def create(config: Dict[str, Any]) -> HybridStrategy:
    """Factory function"""
    return HybridStrategy(config)
