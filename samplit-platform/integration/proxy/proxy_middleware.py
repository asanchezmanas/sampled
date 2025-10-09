# integration/proxy/proxy_middleware.py

"""
MAB Proxy Middleware

Intercepta requests del usuario, obtiene HTML original e inyecta tracker automáticamente.
"""

from fastapi import Request, Response
from fastapi.responses import StreamingResponse
import aiohttp
import logging
from typing import Optional, Dict, Any
from .injection_engine import InjectionEngine

logger = logging.getLogger(__name__)

class MABProxyMiddleware:
    """
    Middleware que intercepta HTML e inyecta tracker automáticamente
    
    El usuario configura su servidor (nginx/apache) para hacer proxy a través de nosotros.
    Nosotros retornamos el HTML con el tracker ya inyectado.
    """
    
    def __init__(self, api_url: str = "https://api.samplit.com"):
        self.api_url = api_url
        self.injection_engine = InjectionEngine(api_url)
        self.timeout = aiohttp.ClientTimeout(total=30)
        
    async def process_request(
        self, 
        request: Request,
        installation_token: str,
        original_url: str
    ) -> Response:
        """
        Procesar request: obtener HTML original e inyectar tracker
        
        Args:
            request: FastAPI Request object
            installation_token: Token de la instalación
            original_url: URL original del sitio del usuario
            
        Returns:
            Response con HTML modificado o contenido original
        """
        try:
            # 1. Obtener HTML original del sitio del usuario
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                headers = self._get_forwarded_headers(request)
                
                async with session.get(original_url, headers=headers) as response:
                    
                    if response.status != 200:
                        logger.warning(
                            f"Original site returned {response.status} for {original_url}"
                        )
                        return Response(
                            content=f"Error fetching original content: {response.status}",
                            status_code=response.status
                        )
                    
                    content_type = response.headers.get('Content-Type', '')
                    
                    # Solo procesar HTML
                    if 'text/html' not in content_type.lower():
                        # Pasar contenido sin modificar (CSS, JS, imágenes, etc)
                        content = await response.read()
                        return Response(
                            content=content,
                            media_type=content_type,
                            headers=self._filter_headers(dict(response.headers))
                        )
                    
                    # 2. Obtener HTML
                    html = await response.text()
                    
                    # 3. Inyectar tracker
                    modified_html = await self.injection_engine.inject_tracker(
                        html=html,
                        installation_token=installation_token,
                        url=original_url
                    )
                    
                    logger.info(f"Tracker injected for {original_url}")
                    
                    # 4. Retornar HTML modificado
                    return Response(
                        content=modified_html,
                        media_type='text/html; charset=utf-8',
                        headers={
                            'Content-Type': 'text/html; charset=utf-8',
                            'X-MAB-Injected': 'true',
                            'Cache-Control': 'no-cache'
                        }
                    )
                    
        except aiohttp.ClientError as e:
            logger.error(f"Proxy request failed: {str(e)}")
            return Response(
                content=f"Proxy error: Could not reach original site",
                status_code=502
            )
        except Exception as e:
            logger.error(f"Proxy middleware error: {str(e)}", exc_info=True)
            return Response(
                content=f"Proxy error: {str(e)}",
                status_code=500
            )
    
    def _get_forwarded_headers(self, request: Request) -> Dict[str, str]:
        """Obtener headers para forward del request original"""
        return {
            'User-Agent': request.headers.get(
                'User-Agent', 
                'MABProxy/1.0'
            ),
            'Accept': request.headers.get('Accept', '*/*'),
            'Accept-Language': request.headers.get('Accept-Language', 'en-US'),
            'Accept-Encoding': 'gzip, deflate',
            'Referer': request.headers.get('Referer', ''),
            'X-Forwarded-For': request.client.host if request.client else '',
            'X-Forwarded-Proto': request.url.scheme,
            'X-Real-IP': request.client.host if request.client else ''
        }
    
    def _filter_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Filtrar headers que no deben ser forwardeados"""
        blocked_headers = {
            'transfer-encoding',
            'content-encoding',
            'content-length',
            'connection',
            'keep-alive',
            'proxy-authenticate',
            'proxy-authorization',
            'te',
            'trailers',
            'upgrade'
        }
        
        return {
            k: v for k, v in headers.items()
            if k.lower() not in blocked_headers
        }
