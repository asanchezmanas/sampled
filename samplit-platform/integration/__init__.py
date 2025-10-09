# integration/__init__.py

"""
Integration Layer

Esta capa maneja todas las integraciones externas:
- Proxy/Middleware para inyección automática
- Plataformas (WordPress, Shopify, etc.)
- Gestión de instalaciones
- Verificación automática
"""

from .proxy.proxy_middleware import MABProxyMiddleware
from .proxy.injection_engine import InjectionEngine
from .proxy.config_generator import ConfigGenerator
from .managers.installation_manager import InstallationManager
from .managers.verification_manager import VerificationManager

__all__ = [
    'MABProxyMiddleware',
    'InjectionEngine',
    'ConfigGenerator',
    'InstallationManager',
    'VerificationManager'
]
