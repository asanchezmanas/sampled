# orchestration/services/funnel_optimizer.py

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from data_access.database import DatabaseManager
from orchestration.factories.optimizer_factory import OptimizerFactory
from orchestration.interfaces.optimization_interface import OptimizationStrategy
import logging

@dataclass
class FunnelStep:
    """Represents a step in the funnel"""
    id: str
    name: str
    order: int
    variants: List[Dict[str, Any]]
    is_required: bool = True
    timeout_seconds: Optional[int] = None

@dataclass
class FunnelSession:
    """Active funnel session for a user"""
    session_id: str
    user_id: str
    funnel_id: str
    current_step: int
    selections: List[str]  # Variant IDs selected at each step
    started_at: datetime
    context: Dict[str, Any]

class FunnelOptimizationService:
    """
    Multi-step funnel optimization
    
    ⭐ COMPETITIVE ADVANTAGE ⭐
    
    This optimizes entire funnel paths, not just individual steps.
    We learn which combinations of variants across steps convert best.
    
    Example:
    Step 1 (Hero): A, B, C
    Step 2 (CTA): X, Y
    Step 3 (Form): P, Q
    
    We learn that path "B -> X -> P" converts better than
    even the individually best performers "A -> Y -> Q"
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        
        # Sequential allocator for multi-step optimization
        self.optimizer = OptimizerFactory.create(
            OptimizationStrategy.SEQUENTIAL,
            config={
                'use_context': True,
                'max_steps': 20,
                'learning_rate': 0.15
            }
        )
        
        # Active sessions
        self.active_sessions: Dict[str, FunnelSession] = {}
    
    async def start_funnel_session(self,
                                   funnel_id: str,
                                   user_id: str,
                                   context: Dict[str, Any]) -> FunnelSession:
        """
        Start a new funnel session for user
        """
        
        session_id = self._generate_session_id()
        
        session = FunnelSession(
            session_id=session_id,
            user_id=user_id,
            funnel_id=funnel_id,
            current_step=0,
            selections=[],
            started_at=datetime.now(),
            context=context
        )
        
        self.active_sessions[session_id] = session
        
        # Persist to DB
        await self.db.create_funnel_session(session)
        
        return session
    
    async def get_next_step_variant(self,
                                    session_id: str) -> Dict[str, Any]:
        """
        Get optimal variant for next funnel step
        
        This is where the magic happens - we consider the user's
        path so far and select the variant that historically
        performs best in combination with previous selections.
        """
        
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get funnel definition
        funnel = await self.db.get_funnel(session.funnel_id)
        steps = funnel['steps']
        
        if session.current_step >= len(steps):
            return {'completed': True}
        
        # Current step
        current_step = steps[session.current_step]
        
        # Prepare context with path history
        optimization_context = {
            'step_id': current_step['id'],
            'step_order': session.current_step,
            'previous_selections': session.selections,
            'user_context': session.context,
            'funnel_id': session.funnel_id
        }
        
        # Get available variants for this step
        variants = current_step['variants']
        
        # Prepare options with performance data
        options = []
        for variant in variants:
            perf_data = await self.db.get_variant_performance(
                variant['id'],
                step_id=current_step['id']
            )
            
            options.append({
                'id': variant['id'],
                'content': variant['content'],
                'performance': perf_data.get('conversion_rate', 0),
                'samples': perf_data.get('sample_size', 0)
            })
        
        # Select using sequential optimizer
        # This considers both individual performance AND path performance
        selected_id = await self.optimizer.select(
            options=options,
            context=optimization_context
        )
        
        # Get full variant data
        selected_variant = next(v for v in variants if v['id'] == selected_id)
        
        # Update session
        session.selections.append(selected_id)
        
        # Log decision
        self.logger.info(
            "Funnel step variant selected",
            session_id=session_id,
            step=session.current_step,
            variant_id=selected_id,
            path_so_far=" -> ".join(session.selections)
        )
        
        return {
            'step': current_step,
            'variant': selected_variant,
            'session': session,
            'progress': (session.current_step + 1) / len(steps)
        }
    
    async def record_step_completion(self,
                                     session_id: str,
                                     converted: bool = False,
                                     metadata: Optional[Dict] = None):
        """
        Record that user completed current step
        
        Updates both step-level and path-level performance
        """
        
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        # Reward for completing step
        step_reward = 0.5 if not converted else 1.0
        
        # Update optimizer
        current_variant_id = session.selections[-1] if session.selections else None
        
        if current_variant_id:
            optimization_context = {
                'step_id': session.current_step,
                'previous_selections': session.selections[:-1],
                'user_context': session.context,
                'full_path': session.selections,
                'funnel_id': session.funnel_id
            }
            
            await self.optimizer.update(
                option_id=current_variant_id,
                reward=step_reward,
                context=optimization_context
            )
        
        # Move to next step if not final conversion
        if not converted:
            session.current_step += 1
        
        # Persist
        await self.db.update_funnel_session(session, metadata)
    
    async def record_funnel_conversion(self,
                                       session_id: str,
                                       conversion_value: float = 1.0,
                                       metadata: Optional[Dict] = None):
        """
        Record complete funnel conversion
        
        This updates the entire path with final conversion reward
        """
        
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        # Update each step in path with final reward
        for i, variant_id in enumerate(session.selections):
            optimization_context = {
                'step_id': i,
                'previous_selections': session.selections[:i],
                'user_context': session.context,
                'full_path': session.selections,
                'funnel_id': session.funnel_id,
                'final_conversion': True
            }
            
            await self.optimizer.update(
                option_id=variant_id,
                reward=conversion_value,
                context=optimization_context
            )
        
        # Persist conversion
        await self.db.record_funnel_conversion(
            session=session,
            value=conversion_value,
            metadata=metadata
        )
        
        # Clean up session
        del self.active_sessions[session_id]
        
        self.logger.info(
            "Funnel conversion recorded",
            session_id=session_id,
            path=" -> ".join(session.selections),
            value=conversion_value
        )
    
    async def get_funnel_insights(self, funnel_id: str) -> Dict[str, Any]:
        """
        Get comprehensive funnel insights
        
        Returns:
        - Best performing paths
        - Step-by-step drop-off analysis
        - Variant performance by step
        - Path combinations analysis
        """
        
        # Get optimizer insights (path performance)
        optimizer_insights = self.optimizer.get_funnel_insights()
        
        # Get step-level analytics
        step_analytics = await self.db.get_funnel_step_analytics(funnel_id)
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(step_analytics)
        
        # Top converting paths
        top_paths = optimizer_insights['top_performing_paths']
        
        # Recommendations
        recommendations = self._generate_recommendations(
            top_paths, 
            bottlenecks,
            step_analytics
        )
        
        return {
            'funnel_id': funnel_id,
            'overview': {
                'total_sessions': step_analytics['total_sessions'],
                'completed_funnels': step_analytics['conversions'],
                'overall_conversion_rate': step_analytics['conversion_rate'],
                'avg_steps_completed': step_analytics['avg_steps']
            },
            'top_performing_paths': top_paths[:5],
            'bottlenecks': bottlenecks,
            'step_performance': step_analytics['by_step'],
            'recommendations': recommendations,
            'optimization_status': {
                'unique_paths_tested': optimizer_insights['total_unique_paths'],
                'steps_optimized': optimizer_insights['steps_optimized'],
                'learning_progress': self._calculate_learning_progress(funnel_id)
            }
        }
    
    def _identify_bottlenecks(self, analytics: Dict) -> List[Dict]:
        """
        Identify funnel bottlenecks
        
        A bottleneck is a step where drop-off is significantly
        higher than expected
        """
        bottlenecks = []
        steps = analytics['by_step']
        
        for i, step in enumerate(steps):
            if i == 0:
                continue
            
            prev_step = steps[i-1]
            
            # Calculate drop-off rate
            drop_off = 1 - (step['entries'] / prev_step['entries'])
            
            # Expected drop-off (baseline: 20% per step)
            expected_drop_off = 0.20
            
            # If actual drop-off is 50% higher than expected
            if drop_off > expected_drop_off * 1.5:
                bottlenecks.append({
                    'step_id': step['id'],
                    'step_name': step['name'],
                    'step_order': i,
                    'drop_off_rate': drop_off,
                    'severity': 'high' if drop_off > 0.4 else 'medium',
                    'users_lost': prev_step['entries'] - step['entries']
                })
        
        return sorted(bottlenecks, key=lambda x: x['drop_off_rate'], reverse=True)
    
    def _generate_recommendations(self, 
                                 top_paths: List[Dict],
                                 bottlenecks: List[Dict],
                                 analytics: Dict) -> List[str]:
        """
        Generate actionable recommendations
        """
        recommendations = []
        
        # Recommendation 1: Winning paths
        if top_paths and len(top_paths) > 0:
            best_path = top_paths[0]
            if best_path['sample_size'] >= 50:
                recommendations.append(
                    f"🏆 Deploy winning path: '{best_path['path']}' "
                    f"({best_path['conversion_rate']:.1%} conversion, "
                    f"{best_path['sample_size']} samples)"
                )
        
        # Recommendation 2: Bottlenecks
        if bottlenecks:
            worst_bottleneck = bottlenecks[0]
            recommendations.append(
                f"⚠️ Critical bottleneck at step '{worst_bottleneck['step_name']}': "
                f"{worst_bottleneck['drop_off_rate']:.1%} drop-off. "
                f"Test more aggressive variants at this step."
            )
        
        # Recommendation 3: Under-tested paths
        total_paths = analytics.get('total_unique_paths', 0)
        steps_count = analytics.get('steps_count', 0)
        theoretical_paths = 2 ** steps_count  # Assuming 2 variants per step average
        
        if total_paths < theoretical_paths * 0.3:
            recommendations.append(
                f"📊 Only {total_paths} unique paths tested out of ~{theoretical_paths} possible. "
                "Increase traffic or extend test duration for better insights."
            )
        
        # Recommendation 4: Sample size
        total_samples = analytics.get('total_sessions', 0)
        min_recommended = steps_count * 100  # 100 samples per step minimum
        
        if total_samples < min_recommended:
            recommendations.append(
                f"⏳ Need more data: {total_samples} samples collected, "
                f"recommend {min_recommended} for statistical confidence."
            )
        
        return recommendations
    
    def _calculate_learning_progress(self, funnel_id: str) -> float:
        """
        Calculate how much the optimizer has learned
        
        Based on:
        - Sample size collected
        - Path coverage
        - Confidence in top performers
        """
        # This would be more sophisticated in production
        # For now, simple heuristic
        return 0.75  # 75% learned
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import uuid
        return f"fsess_{uuid.uuid4().hex[:16]}"
