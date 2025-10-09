# integration/managers/__init__.py

"""
Integration Managers

Managers que gestionan recursos externos y verificaciones.
"""

from .installation_manager import InstallationManager
from .verification_manager import VerificationManager

__all__ = [
    'InstallationManager',
    'VerificationManager'
]
