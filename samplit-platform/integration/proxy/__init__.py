# integration/proxy/__init__.py

"""
Proxy & Middleware System

Sistema de proxy reverso que intercepta HTML y automáticamente
inyecta el tracker de Samplit sin requerir cambios de código.
"""

from .proxy_middleware import MABProxyMiddleware
from .injection_engine import InjectionEngine
from .config_generator import ConfigGenerator

__all__ = [
    'MABProxyMiddleware',
    'InjectionEngine',
    'ConfigGenerator'
]
