# tests/unit/test_thompson_sampling.py

import pytest
import numpy as np
from engine.core.allocators._bayesian import AdaptiveBayesianAllocator
from engine.core.math._distributions import (
    sample_posterior,
    calculate_confidence_bounds,
    calculate_probability_best
)

class TestThompsonSampling:
    """Test suite for Thompson Sampling implementation"""
    
    @pytest.fixture
    def allocator(self):
        """Create allocator instance"""
        config = {
            'learning_rate': 0.1,
            'min_samples': 30
        }
        return AdaptiveBayesianAllocator(config)
    
    @pytest.mark.asyncio
    async def test_select_single_option(self, allocator):
        """Test selection with single option"""
        options = [
            {
                'id': 'variant_1',
                'performance': 0.5,
                'samples': 10,
                '_internal_state': {
                    'success_count': 5,
                    'failure_count': 5,
                    'samples': 10
                }
            }
        ]
        
        selected = await allocator.select(options, {})
        assert selected == 'variant_1'
    
    @pytest.mark.asyncio
    async def test_select_multiple_options(self, allocator):
        """Test selection with multiple options"""
        options = [
            {
                'id': 'variant_1',
                'performance': 0.1,
                'samples': 100,
                '_internal_state': {
                    'success_count': 10,
                    'failure_count': 90,
                    'samples': 100
                }
            },
            {
                'id': 'variant_2',
                'performance': 0.3,
                'samples': 100,
                '_internal_state': {
                    'success_count': 30,
                    'failure_count': 70,
                    'samples': 100
                }
            },
            {
                'id': 'variant_3',
                'performance': 0.5,
                'samples': 100,
                '_internal_state': {
                    'success_count': 50,
                    'failure_count': 50,
                    'samples': 100
                }
            }
        ]
        
        # Run multiple selections
        selections = []
        for _ in range(100):
            selected = await allocator.select(options, {})
            selections.append(selected)
        
        # Best performer should be selected most often
        assert selections.count('variant_3') > selections.count('variant_1')
    
    @pytest.mark.asyncio
    async def test_exploration_bonus(self, allocator):
        """Test that under-sampled options get exploration bonus"""
        options = [
            {
                'id': 'well_tested',
                'performance': 0.3,
                'samples': 500,
                '_internal_state': {
                    'success_count': 150,
                    'failure_count': 350,
                    'samples': 500
                }
            },
            {
                'id': 'under_tested',
                'performance': 0.2,
                'samples': 5,  # Very few samples
                '_internal_state': {
                    'success_count': 1,
                    'failure_count': 4,
                    'samples': 5
                }
            }
        ]
        
        # Run selections
        selections = []
        for _ in range(100):
            selected = await allocator.select(options, {})
            selections.append(selected)
        
        # Under-tested should get selected sometimes due to exploration
        assert selections.count('under_tested') > 0
    
    @pytest.mark.asyncio
    async def test_update_success(self, allocator):
        """Test updating after success"""
        option_id = 'test_variant'
        
        # Initialize model
        allocator._initialize_model(option_id)
        initial_success = allocator._performance_models[option_id]['successes']
        
        # Update with success
        await allocator.update(option_id, 1.0, {})
        
        # Success count should increase
        assert allocator._performance_models[option_id]['successes'] == initial_success + 1
    
    @pytest.mark.asyncio
    async def test_update_failure(self, allocator):
        """Test updating after failure"""
        option_id = 'test_variant'
        
        # Initialize model
        allocator._initialize_model(option_id)
        initial_failure = allocator._performance_models[option_id]['failures']
        
        # Update with failure
        await allocator.update(option_id, 0.0, {})
        
        # Failure count should increase
        assert allocator._performance_models[option_id]['failures'] == initial_failure + 1
    
    def test_sample_posterior_distribution(self):
        """Test Beta distribution sampling"""
        # High conversion rate
        sample_high = sample_posterior(
            success_count=90,
            failure_count=10,
            exploration_bonus=0.0
        )
        
        # Low conversion rate
        sample_low = sample_posterior(
            success_count=10,
            failure_count=90,
            exploration_bonus=0.0
        )
        
        assert 0 <= sample_high <= 1
        assert 0 <= sample_low <= 1
        assert sample_high > sample_low  # Most of the time
    
    def test_calculate_confidence_bounds(self):
        """Test confidence interval calculation"""
        bounds = calculate_confidence_bounds(
            success_count=30,
            failure_count=70,
            confidence_level=0.95
        )
        
        assert 'expected' in bounds
        assert 'lower' in bounds
        assert 'upper' in bounds
        
        # Expected should be between lower and upper
        assert bounds['lower'] <= bounds['expected'] <= bounds['upper']
        
        # Expected should be close to observed rate
        observed_rate = 30 / 100
        assert abs(bounds['expected'] - observed_rate) < 0.05
    
    def test_calculate_probability_best(self):
        """Test probability of being best calculation"""
        options_data = [
            {'successes': 10, 'failures': 90},
            {'successes': 30, 'failures': 70},
            {'successes': 50, 'failures': 50}
        ]
        
        prob_best = calculate_probability_best(options_data, samples=5000)
        
        # Should have 3 probabilities
        assert len(prob_best) == 3
        
        # All should sum to ~1.0
        total_prob = sum(prob_best.values())
        assert 0.95 <= total_prob <= 1.05
        
        # Best performer (50% rate) should have highest probability
        assert prob_best[2] > prob_best[1] > prob_best[0]
