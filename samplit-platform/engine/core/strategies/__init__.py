# engine/core/strategies/__init__.py

"""
Optimization Strategies

This module contains different optimization strategies
for various use cases.

All implementations use generic names to avoid revealing
specific algorithms (Thompson Sampling, Epsilon-Greedy, etc.)
"""

from .standard import StandardStrategy
from .adaptive import AdaptiveStrategy
from .fast_learning import FastLearningStrategy
from .sequential import SequentialStrategy
from .hybrid import HybridStrategy

__all__ = [
    'StandardStrategy',
    'AdaptiveStrategy',
    'FastLearningStrategy',
    'SequentialStrategy',
    'HybridStrategy'
]
