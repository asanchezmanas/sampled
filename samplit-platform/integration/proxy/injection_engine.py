# integration/proxy/injection_engine.py

"""
Injection Engine

Motor que inyecta el tracker de Samplit en HTML automáticamente.
"""

import re
import json
import logging
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class InjectionEngine:
    """
    Motor de inyección de código en HTML
    
    Inyecta inteligentemente el tracker en el lugar óptimo del HTML
    sin romper la estructura de la página.
    """
    
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.tracker_url = f"{api_url}/static/tracker.js"
    
    async def inject_tracker(
        self,
        html: str,
        installation_token: str,
        url: str,
        experiments: Optional[List[Dict]] = None
    ) -> str:
        """
        Inyectar tracker en HTML
        
        Args:
            html: HTML original
            installation_token: Token de instalación
            url: URL de la página
            experiments: Experimentos activos (opcional)
            
        Returns:
            HTML con tracker inyectado
        """
        try:
            # Si no se pasaron experimentos, construir config básica
            if experiments is None:
                experiments = []
            
            # Construir configuración del tracker
            config = self._build_tracker_config(
                installation_token,
                url,
                experiments
            )
            
            # Generar código del tracker
            tracker_code = self._generate_tracker_code(config)
            
            # Inyectar en HTML
            modified_html = self._inject_code(html, tracker_code)
            
            return modified_html
            
        except Exception as e:
            logger.error(f"Injection failed: {str(e)}", exc_info=True)
            # En caso de error, retornar HTML original
            return html
    
    def _build_tracker_config(
        self,
        installation_token: str,
        url: str,
        experiments: List[Dict]
    ) -> Dict[str, Any]:
        """Construir configuración para el tracker"""
        return {
            'installationToken': installation_token,
            'apiEndpoint': self.api_url,
            'currentUrl': url,
            'experiments': [
                {
                    'id': exp.get('id'),
                    'name': exp.get('name'),
                    'elements': exp.get('elements', [])
                }
                for exp in experiments
            ],
            'tracking': {
                'enabled': True,
                'pageViews': True,
                'clicks': True,
                'scrollDepth': True
            },
            'debug': False
        }
    
    def _generate_tracker_code(self, config: Dict[str, Any]) -> str:
        """Generar código HTML del tracker"""
        config_json = json.dumps(config, separators=(',', ':'))
        
        return f"""
<!-- Samplit Tracker (Auto-Injected) -->
<script>
window.SAMPLIT_CONFIG = {config_json};
</script>
<script src="{self.tracker_url}" async></script>
<!-- End Samplit Tracker -->
"""
    
    def _inject_code(self, html: str, tracker_code: str) -> str:
        """
        Inyectar código en HTML
        
        Estrategia de inyección (en orden de preferencia):
        1. Después del <head> tag
        2. Después del <body> tag  
        3. Al inicio del documento (fallback)
        """
        
        # Método 1: Inyectar después de <head>
        if '<head>' in html.lower():
            modified = re.sub(
                r'(<head[^>]*>)',
                r'\1' + tracker_code,
                html,
                count=1,
                flags=re.IGNORECASE
            )
            if modified != html:
                logger.debug("Injected after <head>")
                return modified
        
        # Método 2: Inyectar después de <body>
        if '<body>' in html.lower():
            modified = re.sub(
                r'(<body[^>]*>)',
                r'\1' + tracker_code,
                html,
                count=1,
                flags=re.IGNORECASE
            )
            if modified != html:
                logger.debug("Injected after <body>")
                return modified
        
        # Método 3: Fallback - inyectar al inicio
        logger.warning("No <head> or <body> found, injecting at start")
        return tracker_code + html
    
    def generate_manual_snippet(
        self,
        installation_token: str,
        site_url: str
    ) -> str:
        """
        Generar snippet para instalación manual
        
        Este código lo copia el usuario en su sitio manualmente.
        """
        config = self._build_tracker_config(
            installation_token,
            site_url,
            []
        )
        
        return f"""<!-- Samplit Tracker -->
<script>
window.SAMPLIT_CONFIG = {{
    installationToken: '{installation_token}',
    apiEndpoint: '{self.api_url}'
}};
</script>
<script src="{self.tracker_url}" async></script>
<!-- End Samplit Tracker -->"""
