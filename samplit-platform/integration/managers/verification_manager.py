# integration/managers/verification_manager.py

"""
Verification Manager

Verifica automáticamente que las instalaciones estén funcionando correctamente.
"""

import aiohttp
import logging
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class VerificationManager:
    """
    Manager para verificar instalaciones automáticamente
    """
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=10)
        self.user_agent = 'SamplitVerificationBot/1.0'
    
    async def verify_installation(
        self,
        site_url: str,
        installation_token: str
    ) -> Dict[str, Any]:
        """
        Verificar que la instalación esté funcionando
        
        Args:
            site_url: URL del sitio
            installation_token: Token de instalación
            
        Returns:
            Dict con resultado de la verificación:
            {
                'verified': bool,
                'method': str,
                'message': str,
                'details': dict
            }
        """
        try:
            # Intentar diferentes métodos de verificación
            
            # Método 1: Buscar token en HTML
            html_verified = await self._verify_html(site_url, installation_token)
            if html_verified['verified']:
                return html_verified
            
            # Método 2: Verificar endpoint de verificación
            endpoint_verified = await self._verify_endpoint(site_url, installation_token)
            if endpoint_verified['verified']:
                return endpoint_verified
            
            # Método 3: Verificar headers
            headers_verified = await self._verify_headers(site_url)
            if headers_verified['verified']:
                return headers_verified
            
            # No se pudo verificar
            return {
                'verified': False,
                'method': 'none',
                'message': 'Could not verify installation. Please check your setup.',
                'details': {
                    'html_check': html_verified['message'],
                    'endpoint_check': endpoint_verified['message'],
                    'headers_check': headers_verified['message']
                }
            }
            
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}", exc_info=True)
            return {
                'verified': False,
                'method': 'error',
                'message': f'Verification error: {str(e)}',
                'details': {}
            }
    
    async def _verify_html(
        self,
        site_url: str,
        installation_token: str
    ) -> Dict[str, Any]:
        """
        Verificar buscando el token en el HTML
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    site_url,
                    headers={'User-Agent': self.user_agent}
                ) as response:
                    
                    if response.status != 200:
                        return {
                            'verified': False,
                            'method': 'html',
                            'message': f'HTTP {response.status}'
                        }
                    
                    html = await response.text()
                    
                    # Buscar token en el HTML
                    if installation_token in html:
                        # Verificar que esté en un script de Samplit
                        if 'SAMPLIT' in html or 'MAB' in html:
                            return {
                                'verified': True,
                                'method': 'html',
                                'message': 'Tracker code found in HTML',
                                'details': {
                                    'found_token': True,
                                    'found_config': True
                                }
                            }
                    
                    return {
                        'verified': False,
                        'method': 'html',
                        'message': 'Tracker code not found in HTML'
                    }
                    
        except aiohttp.ClientError as e:
            return {
                'verified': False,
                'method': 'html',
                'message': f'Connection error: {str(e)}'
            }
        except Exception as e:
            return {
                'verified': False,
                'method': 'html',
                'message': f'Error: {str(e)}'
            }
    
    async def _verify_endpoint(
        self,
        site_url: str,
        installation_token: str
    ) -> Dict[str, Any]:
        """
        Verificar usando endpoint especial
        """
        try:
            verify_url = f"{site_url}?mab_verify={installation_token}"
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    verify_url,
                    headers={'User-Agent': self.user_agent}
                ) as response:
                    
                    if response.status != 200:
                        return {
                            'verified': False,
                            'method': 'endpoint',
                            'message': f'HTTP {response.status}'
                        }
                    
                    html = await response.text()
                    
                    # Buscar marca de verificación
                    if 'MAB_INSTALLATION_ID' in html and installation_token in html:
                        return {
                            'verified': True,
                            'method': 'endpoint',
                            'message': 'Verification endpoint responded correctly',
                            'details': {
                                'endpoint': verify_url
                            }
                        }
                    
                    return {
                        'verified': False,
                        'method': 'endpoint',
                        'message': 'Verification endpoint not responding'
                    }
                    
        except aiohttp.ClientError as e:
            return {
                'verified': False,
                'method': 'endpoint',
                'message': f'Connection error: {str(e)}'
            }
        except Exception as e:
            return {
                'verified': False,
                'method': 'endpoint',
                'message': f'Error: {str(e)}'
            }
    
    async def _verify_headers(
        self,
        site_url: str
    ) -> Dict[str, Any]:
        """
        Verificar mediante headers de respuesta
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.head(
                    site_url,
                    headers={'User-Agent': self.user_agent}
                ) as response:
                    
                    # Buscar header de Samplit
                    if 'X-MAB-Injected' in response.headers:
                        return {
                            'verified': True,
                            'method': 'headers',
                            'message': 'Samplit proxy headers detected',
                            'details': {
                                'proxy_detected': True
                            }
                        }
                    
                    return {
                        'verified': False,
                        'method': 'headers',
                        'message': 'No Samplit headers found'
                    }
                    
        except aiohttp.ClientError as e:
            return {
                'verified': False,
                'method': 'headers',
                'message': f'Connection error: {str(e)}'
            }
        except Exception as e:
            return {
                'verified': False,
                'method': 'headers',
                'message': f'Error: {str(e)}'
            }
    
    async def check_health(
        self,
        site_url: str
    ) -> Dict[str, Any]:
        """
        Verificar salud general del sitio
        
        Args:
            site_url: URL del sitio
            
        Returns:
            Dict con información de salud
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    site_url,
                    headers={'User-Agent': self.user_agent}
                ) as response:
                    
                    status_code = response.status
                    response_time = response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0
                    
                    # Determinar salud
                    if status_code == 200:
                        health = 'healthy'
                    elif 200 <= status_code < 300:
                        health = 'healthy'
                    elif 300 <= status_code < 400:
                        health = 'warning'
                    elif status_code == 429:
                        health = 'rate_limited'
                    else:
                        health = 'unhealthy'
                    
                    return {
                        'health': health,
                        'status_code': status_code,
                        'response_time': response_time,
                        'accessible': True,
                        'message': f'Site is {health}'
                    }
                    
        except aiohttp.ClientError as e:
            return {
                'health': 'unreachable',
                'status_code': 0,
                'response_time': 0,
                'accessible': False,
                'message': f'Site unreachable: {str(e)}'
            }
        except Exception as e:
            return {
                'health': 'error',
                'status_code': 0,
                'response_time': 0,
                'accessible': False,
                'message': f'Health check error: {str(e)}'
            }
