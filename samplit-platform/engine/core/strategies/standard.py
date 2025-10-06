# engine/core/strategies/standard.py

"""
Standard Strategy

Traditional A/B testing with equal traffic split.
No adaptive optimization - just random assignment.
"""

import random
from typing import List, Dict, Any
from ..base import BaseStrategy

class StandardStrategy(BaseStrategy):
    """
    Standard A/B testing strategy
    
    - Equal traffic split
    - No learning/adaptation
    - Simple random assignment
    
    Use case: When you want traditional A/B testing
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "standard"
    
    async def select(self, 
                    options: List[Dict[str, Any]], 
                    context: Dict[str, Any]) -> str:
        """
        Random selection with equal probability
        
        This is NOT adaptive - just traditional A/B split
        """
        if not options:
            raise ValueError("No options provided")
        
        # Simple random choice
        selected = random.choice(options)
        
        self.logger.info(
            "Standard allocation",
            variant=selected['id'],
            method="random_split"
        )
        
        return selected['id']
    
    async def update(self, 
                    option_id: str, 
                    reward: float,
                    context: Dict[str, Any]) -> None:
        """
        No updates needed for standard strategy
        
        Standard A/B doesn't learn from results
        """
        pass  # No learning in standard strategy
    
    def get_insights(self) -> Dict[str, Any]:
        """Get strategy insights"""
        return {
            "strategy": "standard",
            "type": "traditional_ab",
            "adaptive": False,
            "description": "Equal traffic split with no learning"
        }
