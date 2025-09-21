# backend/thompson.py
import numpy as np
import scipy.stats as stats
from typing import Dict, List, Any, Tuple
import asyncio
from utils import Logger

class ThompsonSamplingManager:
    """
    Core Thompson Sampling implementation
    Simplified but statistically robust
    """
    
    def __init__(self, database_manager):
        self.db = database_manager
        self.logger = Logger()
        
        # Configuration
        self.min_samples_for_reliable_stats = 30
        self.exploration_bonus = 0.1
        self.confidence_threshold = 0.95
        
    def select_arm(self, arms: List[Dict[str, Any]]) -> str:
        """
        Select arm using Thompson Sampling
        
        Args:
            arms: List of arm dictionaries with alpha, beta, assignments stats
            
        Returns:
            Selected arm ID
        """
        if not arms:
            raise ValueError("No arms provided")
        
        # Filter active arms
        active_arms = [arm for arm in arms if arm.get('is_active', True)]
        if not active_arms:
            raise ValueError("No active arms available")
        
        if len(active_arms) == 1:
            return active_arms[0]['id']
        
        arm_scores = {}
        total_assignments = sum(arm.get('assignments', 0) for arm in active_arms)
        
        for arm in active_arms:
            # Get Beta distribution parameters
            alpha = max(arm.get('alpha', 1.0), 1.0)
            beta = max(arm.get('beta', 1.0), 1.0)
            assignments = arm.get('assignments', 0)
            
            # Sample from Beta distribution (Thompson Sampling)
            sampled_rate = np.random.beta(alpha, beta)
            
            # Add exploration bonus for arms with few samples
            if assignments < self.min_samples_for_reliable_stats:
                if total_assignments > 0:
                    exploration_bonus = self.exploration_bonus * np.sqrt(
                        np.log(max(total_assignments, 1)) / max(assignments, 1)
                    )
                else:
                    exploration_bonus = self.exploration_bonus
                
                sampled_rate += exploration_bonus
                
                self.logger.debug(
                    f"Added exploration bonus {exploration_bonus:.3f} to arm {arm['id']} "
                    f"(assignments: {assignments})"
                )
            
            arm_scores[arm['id']] = sampled_rate
            
            self.logger.debug(
                f"Arm {arm['id']}: alpha={alpha:.2f}, beta={beta:.2f}, "
                f"score={sampled_rate:.4f}, assignments={assignments}"
            )
        
        # Select arm with highest score
        selected_arm_id = max(arm_scores, key=arm_scores.get)
        selected_score = arm_scores[selected_arm_id]
        
        self.logger.info(
            f"Thompson Sampling selected arm {selected_arm_id} "
            f"with score {selected_score:.4f}"
        )
        
        return selected_arm_id
    
    async def update_arm_success(self, arm_id: str) -> None:
        """Update arm after successful conversion"""
        try:
            await self.db.increment_arm_alpha(arm_id)
            self.logger.debug(f"Updated arm {arm_id} alpha (conversion)")
        except Exception as e:
            self.logger.error(f"Failed to update arm success: {str(e)}")
    
    async def update_arm_failure(self, arm_id: str) -> None:
        """Update arm after failed conversion"""
        try:
            await self.db.increment_arm_beta(arm_id)
            self.logger.debug(f"Updated arm {arm_id} beta (no conversion)")
        except Exception as e:
            self.logger.error(f"Failed to update arm failure: {str(e)}")
    
    def get_bayesian_analysis(self, arms_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform comprehensive Bayesian analysis
        
        Args:
            arms_data: List of arms with statistics
            
        Returns:
            Dictionary with Bayesian analysis results
        """
        if len(arms_data) < 2:
            return {
                "message": "Need at least 2 arms for comparison",
                "min_samples_needed": self.min_samples_for_reliable_stats
            }
        
        # Check if we have enough data
        total_assignments = sum(arm.get('assignments', 0) for arm in arms_data)
        if total_assignments < self.min_samples_for_reliable_stats:
            return {
                "message": f"Need at least {self.min_samples_for_reliable_stats} total assignments",
                "current_assignments": total_assignments,
                "min_samples_needed": self.min_samples_for_reliable_stats
            }
        
        try:
            # Calculate probabilities each arm is best
            prob_best = self._calculate_prob_best(arms_data)
            
            # Calculate expected conversion rates and credible intervals
            arm_statistics = self._calculate_arm_statistics(arms_data)
            
            # Determine winner and confidence
            best_arm_id = max(prob_best, key=prob_best.get)
            best_prob = prob_best[best_arm_id]
            
            # Statistical power analysis
            power_analysis = self._calculate_statistical_power(arms_data)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                arms_data, prob_best, best_prob, power_analysis
            )
            
            return {
                "prob_best": prob_best,
                "arm_statistics": arm_statistics,
                "best_arm": best_arm_id,
                "best_arm_probability": best_prob,
                "confidence_threshold_met": best_prob >= self.confidence_threshold,
                "recommended_winner": best_arm_id if best_prob >= self.confidence_threshold else None,
                "continue_experiment": best_prob < self.confidence_threshold,
                "statistical_power": power_analysis["power"],
                "recommendations": recommendations,
                "sample_sizes": {arm['id']: arm.get('assignments', 0) for arm in arms_data}
            }
            
        except Exception as e:
            self.logger.error(f"Bayesian analysis failed: {str(e)}")
            return {
                "error": "Analysis failed",
                "message": "Unable to perform statistical analysis"
            }
    
    def _calculate_prob_best(
        self, 
        arms_data: List[Dict[str, Any]], 
        samples: int = 10000
    ) -> Dict[str, float]:
        """Calculate probability each arm is the best using Monte Carlo"""
        
        arm_samples = {}
        
        # Generate samples for each arm
        for arm in arms_data:
            alpha = max(arm.get('alpha', 1.0), 1.0)
            beta = max(arm.get('beta', 1.0), 1.0)
            arm_samples[arm['id']] = np.random.beta(alpha, beta, samples)
        
        # Count how often each arm is best
        prob_best = {}
        arm_ids = list(arm_samples.keys())
        
        for arm_id in arm_ids:
            is_best_count = 0
            
            for i in range(samples):
                is_best = True
                current_sample = arm_samples[arm_id][i]
                
                # Check if this arm's sample is best
                for other_arm_id in arm_ids:
                    if other_arm_id != arm_id and arm_samples[other_arm_id][i] > current_sample:
                        is_best = False
                        break
                
                if is_best:
                    is_best_count += 1
            
            prob_best[arm_id] = is_best_count / samples
        
        return prob_best
    
    def _calculate_arm_statistics(self, arms_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Calculate statistics for each arm"""
        
        statistics = {}
        
        for arm in arms_data:
            alpha = max(arm.get('alpha', 1.0), 1.0)
            beta = max(arm.get('beta', 1.0), 1.0)
            
            # Beta distribution statistics
            mean = alpha / (alpha + beta)
            variance = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))
            std = np.sqrt(variance)
            
            # 95% credible interval
            ci_lower = stats.beta.ppf(0.025, alpha, beta)
            ci_upper = stats.beta.ppf(0.975, alpha, beta)
            
            statistics[arm['id']] = {
                "expected_conversion_rate": mean,
                "standard_deviation": std,
                "credible_interval_lower": ci_lower,
                "credible_interval_upper": ci_upper,
                "assignments": arm.get('assignments', 0),
                "conversions": arm.get('conversions', 0),
                "observed_rate": (
                    arm.get('conversions', 0) / arm.get('assignments', 1) 
                    if arm.get('assignments', 0) > 0 else 0
                )
            }
        
        return statistics
    
    def _calculate_statistical_power(self, arms_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate statistical power of the experiment"""
        
        if len(arms_data) != 2:
            return {"power": 0.0, "message": "Power analysis only available for 2-arm tests"}
        
        arm1, arm2 = arms_data[0], arms_data[1]
        
        # Observed rates
        rate1 = arm1.get('conversions', 0) / max(arm1.get('assignments', 1), 1)
        rate2 = arm2.get('conversions', 0) / max(arm2.get('assignments', 1), 1)
        
        # Effect size
        effect_size = abs(rate2 - rate1)
        
        # Sample sizes
        n1 = arm1.get('assignments', 0)
        n2 = arm2.get('assignments', 0)
        
        if n1 == 0 or n2 == 0 or effect_size == 0:
            return {"power": 0.0, "effect_size": effect_size}
        
        # Pooled standard error
        pooled_rate = (arm1.get('conversions', 0) + arm2.get('conversions', 0)) / (n1 + n2)
        pooled_se = np.sqrt(pooled_rate * (1 - pooled_rate) * (1/n1 + 1/n2))
        
        if pooled_se == 0:
            return {"power": 0.0, "effect_size": effect_size}
        
        # Z-score and power calculation
        z_score = effect_size / pooled_se
        power = 1 - stats.norm.cdf(1.96 - abs(z_score))  # Two-tailed test
        
        return {
            "power": max(0.0, min(1.0, power)),
            "effect_size": effect_size,
            "z_score": z_score
        }
    
    def _generate_recommendations(
        self, 
        arms_data: List[Dict[str, Any]], 
        prob_best: Dict[str, float], 
        best_prob: float,
        power_analysis: Dict[str, float]
    ) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        total_assignments = sum(arm.get('assignments', 0) for arm in arms_data)
        
        if best_prob >= self.confidence_threshold:
            best_arm_name = next(
                arm['name'] for arm in arms_data 
                if arm['id'] == max(prob_best, key=prob_best.get)
            )
            recommendations.append(
                f"✓ Clear winner identified: {best_arm_name} "
                f"({best_prob:.1%} probability of being best)"
            )
            recommendations.append("Consider stopping the experiment and implementing the winner")
            
        elif total_assignments < self.min_samples_for_reliable_stats:
            needed = self.min_samples_for_reliable_stats - total_assignments
            recommendations.append(
                f"⏳ Need {needed} more users for reliable results "
                f"({total_assignments}/{self.min_samples_for_reliable_stats})"
            )
            
        elif power_analysis.get("power", 0) < 0.8:
            recommendations.append(
                f"⚡ Low statistical power ({power_analysis.get('power', 0):.1%}). "
                "Consider running longer or increasing traffic"
            )
            
        else:
            recommendations.append(
                f"📊 Results are close. Best arm has {best_prob:.1%} probability. "
                "Continue testing for more confidence"
            )
        
        # Traffic distribution recommendation
        if len(arms_data) > 2:
            worst_performers = [
                arm for arm in arms_data 
                if prob_best.get(arm['id'], 0) < 0.1
            ]
            if worst_performers:
                recommendations.append(
                    "Consider pausing clearly underperforming variants to focus traffic"
                )
        
        return recommendations
    
    def calculate_required_sample_size(
        self, 
        baseline_rate: float, 
        minimum_detectable_effect: float,
        power: float = 0.8, 
        alpha: float = 0.05
    ) -> int:
        """Calculate required sample size for desired statistical power"""
        
        if baseline_rate <= 0 or baseline_rate >= 1:
            raise ValueError("Baseline rate must be between 0 and 1")
        
        if minimum_detectable_effect <= 0:
            raise ValueError("Minimum detectable effect must be positive")
        
        # Effect size calculation
        p1 = baseline_rate
        p2 = baseline_rate + minimum_detectable_effect
        
        if p2 > 1:
            p2 = 1
        
        # Pooled probability
        p_pooled = (p1 + p2) / 2
        
        # Standard deviations
        sd1 = np.sqrt(p1 * (1 - p1))
        sd2 = np.sqrt(p2 * (1 - p2))
        sd_pooled = np.sqrt(p_pooled * (1 - p_pooled))
        
        # Critical values
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power)
        
        # Sample size calculation
        numerator = (z_alpha * sd_pooled * np.sqrt(2) + z_beta * np.sqrt(sd1**2 + sd2**2))**2
        denominator = (p2 - p1)**2
        
        n_per_group = numerator / denominator
        
        return int(np.ceil(n_per_group))