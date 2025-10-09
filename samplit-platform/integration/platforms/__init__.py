# integration/platforms/__init__.py


"""
Platform Integrations

Wrappers for ads platforms APIs
"""

from .meta_ads import MetaAdsIntegration
from .google_ads import GoogleAdsIntegration

__all__ = ['MetaAdsIntegration', 'GoogleAdsIntegration']
