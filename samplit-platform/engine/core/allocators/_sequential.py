# engine/core/allocators/_sequential.py

"""
Sequential Multi-Step Allocator

Specialized for funnel optimization where each step is a decision point.

Implementation: [PROPRIETARY - PATENT PENDING]
"""

from typing import List, Dict, Any, Optional
from .._base import BaseAllocator
from ._bayesian import AdaptiveBayesianAllocator
from datetime import datetime, timezone

class SequentialAllocator(BaseAllocator):
    """
    Multi-step optimization for funnels
    
    ⭐ This is Samplit's killer feature for funnel optimization.
    
    Each funnel step is treated as a contextual bandit problem
    where the context includes:
    - Previous step selections
    - User behavior up to this point
    - Cross-step performance correlations
    
    Implementation: [CONFIDENTIAL - COMPETITIVE ADVANTAGE]
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Allocator per step
        self.step_allocators = {}
        
        # Tracking de paths completos
        self.path_performance = {}  # "stepA_variantX -> stepB_variantY"
        
        # Config
        self.max_steps = config.get('max_steps', 10)
        self.use_path_context = config.get('use_context', True)
    
    async def select(self, 
                    options: List[Dict[str, Any]], 
                    context: Dict[str, Any]) -> str:
        """
        Select optimal variant for current funnel step
        
        This considers:
        1. Performance of this variant at this step
        2. Historical path performance (if variant was selected in previous steps)
        3. User context and behavior
        
        This is where we outperform competitors - they optimize
        each step independently. We optimize the ENTIRE funnel path.
        """
        
        step_id = context.get('step_id')
        previous_path = context.get('previous_selections', [])
        
        if not step_id:
            raise ValueError("Funnel step ID required")
        
        # Get or create allocator for this step
        if step_id not in self.step_allocators:
            self.step_allocators[step_id] = AdaptiveBayesianAllocator(
                self.config
            )
        
        allocator = self.step_allocators[step_id]
        
        # Enhance options with path context
        if self.use_path_context and previous_path:
            options = self._enrich_with_path_performance(
                options, 
                previous_path
            )
        
        # Select using step allocator
        selected = await allocator.select(options, context)
        
        self._log_sequential_decision(
            step=step_id,
            selected=selected,
            path=previous_path
        )
        
        return selected
    
    async def update(self, 
                    option_id: str, 
                    reward: float, 
                    context: Dict[str, Any]) -> None:
        """
        Update with funnel completion data
        
        This updates:
        1. Individual step performance
        2. Full path performance
        3. Cross-step correlations
        """
        
        step_id = context.get('step_id')
        full_path = context.get('full_path', [])
        
        # Update step allocator
        if step_id in self.step_allocators:
            await self.step_allocators[step_id].update(
                option_id, reward, context
            )
        
        # Update path performance (multi-step learning)
        if full_path:
            self._update_path_performance(full_path, reward)
    
    def _enrich_with_path_performance(self, 
                                     options: List[Dict], 
                                     previous_path: List[str]) -> List[Dict]:
        """
        Enhance option data with path-based performance
        
        This is the secret sauce - we look at how this variant
        performed in combination with previous selections.
        
        Example: "Hero_V1 -> CTA_V2" might convert better than
                 "Hero_V1 -> CTA_V1" even if CTA_V1 is individually better
        """
        
        enriched = []
        
        for option in options:
            opt = option.copy()
            
            # Build hypothetical path
            hypothetical_path = previous_path + [option['id']]
            path_key = " -> ".join(hypothetical_path)
            
            # Check if we have performance data for this path
            if path_key in self.path_performance:
                path_perf = self.path_performance[path_key]
                
                # Blend individual and path performance
                opt['path_adjusted_performance'] = {
                    'individual': opt.get('performance', 0),
                    'path_performance': path_perf['conversion_rate'],
                    'path_confidence': path_perf['sample_size'],
                    'blended_score': self._blend_scores(
                        opt.get('performance', 0),
                        path_perf['conversion_rate'],
                        path_perf['sample_size']
                    )
                }
            
            enriched.append(opt)
        
        return enriched
    
    def _update_path_performance(self, full_path: List[str], reward: float):
        """
        Update performance metrics for completed path
        
        This learns which combinations of variants work best together.
        """
        path_key = " -> ".join(full_path)
        
        if path_key not in self.path_performance:
            self.path_performance[path_key] = {
                'conversions': 0,
                'attempts': 0,
                'conversion_rate': 0.0,
                'sample_size': 0
            }
        
        path = self.path_performance[path_key]
        path['attempts'] += 1
        
        if reward > 0:
            path['conversions'] += 1
        
        path['sample_size'] = path['attempts']
        path['conversion_rate'] = path['conversions'] / path['attempts']
    
    def _blend_scores(self, 
                     individual: float, 
                     path: float, 
                     path_confidence: int) -> float:
        """
        Blend individual and path performance
        
        Higher path confidence = more weight on path data
        """
        if path_confidence < 10:
            return individual  # Not enough data
        
        # Weighted average based on confidence
        confidence_weight = min(path_confidence / 100, 0.7)
        
        return (individual * (1 - confidence_weight)) + (path * confidence_weight)
    
    def get_funnel_insights(self) -> Dict[str, Any]:
        """
        Get funnel-specific insights
        
        Returns analyzed paths, bottlenecks, winning combinations
        """
        
        # Top performing paths
        sorted_paths = sorted(
            self.path_performance.items(),
            key=lambda x: x[1]['conversion_rate'],
            reverse=True
        )
        
        top_paths = [
            {
                'path': path,
                'conversion_rate': data['conversion_rate'],
                'sample_size': data['sample_size']
            }
            for path, data in sorted_paths[:10]
            if data['sample_size'] >= 10
        ]
        
        return {
            'top_performing_paths': top_paths,
            'total_unique_paths': len(self.path_performance),
            'steps_optimized': len(self.step_allocators)
        }

def create(config: Dict[str, Any]) -> SequentialAllocator:
    return SequentialAllocator(config)
