# integration/proxy/config_generator.py

"""
Config Generator

Genera configuraciones de servidor (nginx, apache, cloudflare)
para el proxy middleware.
"""

from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class ServerConfig:
    """Configuración de servidor generada"""
    platform: str
    config_code: str
    steps: List[str]
    verification_command: str = ""

class ConfigGenerator:
    """
    Generador de configuraciones para diferentes plataformas
    """
    
    def __init__(self, proxy_base_url: str = "https://proxy.samplit.com"):
        self.proxy_base_url = proxy_base_url
    
    def generate_config(
        self,
        domain: str,
        installation_token: str,
        platform: str
    ) -> ServerConfig:
        """
        Generar configuración para plataforma específica
        
        Args:
            domain: Dominio del usuario (ej: example.com)
            installation_token: Token de instalación
            platform: Plataforma (nginx, apache, cloudflare, etc)
            
        Returns:
            ServerConfig con código y pasos de instalación
        """
        generators = {
            'nginx': self._generate_nginx,
            'apache': self._generate_apache,
            'cloudflare': self._generate_cloudflare,
            'haproxy': self._generate_haproxy,
        }
        
        generator = generators.get(platform, self._generate_generic)
        return generator(domain, installation_token)
    
    def _generate_nginx(self, domain: str, token: str) -> ServerConfig:
        """Generar configuración de Nginx"""
        proxy_url = f"{self.proxy_base_url}/{token}"
        
        config = f"""# Samplit Proxy Configuration for Nginx
# Add this to your nginx configuration

server {{
    listen 80;
    listen [::]:80;
    server_name {domain};
    
    location / {{
        # Proxy to Samplit
        proxy_pass {proxy_url};
        
        # Forward original headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering
        proxy_buffering off;
        proxy_request_buffering off;
    }}
}}"""
        
        steps = [
            f"1. Add the configuration above to /etc/nginx/sites-available/{domain}",
            "2. Create symbolic link: sudo ln -s /etc/nginx/sites-available/{domain} /etc/nginx/sites-enabled/",
            "3. Test configuration: sudo nginx -t",
            "4. If test passes, reload nginx: sudo systemctl reload nginx",
            f"5. Verify: curl -I https://{domain}"
        ]
        
        return ServerConfig(
            platform='nginx',
            config_code=config,
            steps=steps,
            verification_command='sudo nginx -t'
        )
    
    def _generate_apache(self, domain: str, token: str) -> ServerConfig:
        """Generar configuración de Apache"""
        proxy_url = f"{self.proxy_base_url}/{token}"
        
        config = f"""# Samplit Proxy Configuration for Apache
# Add this to your Apache virtual host

<VirtualHost *:80>
    ServerName {domain}
    
    # Enable proxy modules
    ProxyPreserveHost On
    ProxyRequests Off
    
    # Proxy configuration
    ProxyPass / {proxy_url}/
    ProxyPassReverse / {proxy_url}/
    
    # Forward headers
    RequestHeader set X-Forwarded-Proto "http"
    RequestHeader set X-Forwarded-Port "80"
    
    # Timeouts
    ProxyTimeout 60
    
    # Error handling
    ErrorLog ${{APACHE_LOG_DIR}}/{domain}-error.log
    CustomLog ${{APACHE_LOG_DIR}}/{domain}-access.log combined
</VirtualHost>"""
        
        steps = [
            "1. Enable required Apache modules:",
            "   sudo a2enmod proxy",
            "   sudo a2enmod proxy_http",
            "   sudo a2enmod headers",
            f"2. Add configuration to /etc/apache2/sites-available/{domain}.conf",
            f"3. Enable site: sudo a2ensite {domain}",
            "4. Test configuration: sudo apache2ctl configtest",
            "5. If test passes, restart Apache: sudo systemctl restart apache2",
            f"6. Verify: curl -I https://{domain}"
        ]
        
        return ServerConfig(
            platform='apache',
            config_code=config,
            steps=steps,
            verification_command='sudo apache2ctl configtest'
        )
    
    def _generate_cloudflare(self, domain: str, token: str) -> ServerConfig:
        """Generar Worker de Cloudflare"""
        proxy_url = f"{self.proxy_base_url}/{token}"
        
        config = f"""// Samplit Cloudflare Worker
// Deploy this as a Worker and add route: {domain}/*

addEventListener('fetch', event => {{
  event.respondWith(handleRequest(event.request))
}})

async function handleRequest(request) {{
  const url = new URL(request.url)
  const proxyUrl = '{proxy_url}' + url.pathname + url.search
  
  // Forward request to Samplit proxy
  const modifiedRequest = new Request(proxyUrl, {{
    method: request.method,
    headers: request.headers,
    body: request.body
  }})
  
  // Add original host header
  modifiedRequest.headers.set('X-Original-Host', url.hostname)
  
  // Fetch from Samplit proxy
  const response = await fetch(modifiedRequest)
  
  // Return response
  return response
}}"""
        
        steps = [
            "1. Go to Cloudflare Dashboard → Workers",
            "2. Click 'Create a Service'",
            "3. Name it 'samplit-proxy' and click Create",
            "4. Click 'Quick Edit' and paste the code above",
            "5. Click 'Save and Deploy'",
            f"6. Go to your website settings → Workers Routes",
            f"7. Add route: {domain}/* → samplit-proxy worker",
            "8. Save changes",
            f"9. Verify: Visit https://{domain}"
        ]
        
        return ServerConfig(
            platform='cloudflare',
            config_code=config,
            steps=steps
        )
    
    def _generate_haproxy(self, domain: str, token: str) -> ServerConfig:
        """Generar configuración de HAProxy"""
        proxy_url = f"{self.proxy_base_url}/{token}"
        proxy_host = proxy_url.split('//')[1].split('/')[0]
        
        config = f"""# Samplit Proxy Configuration for HAProxy
# Add this to /etc/haproxy/haproxy.cfg

frontend http_front
    bind *:80
    acl host_{domain.replace('.', '_')} hdr(host) -i {domain}
    use_backend samplit_proxy if host_{domain.replace('.', '_')}

backend samplit_proxy
    mode http
    option forwardfor
    http-request set-header X-Forwarded-Host %[req.hdr(Host)]
    server samplit {proxy_host}:443 ssl verify none"""
        
        steps = [
            "1. Add configuration to /etc/haproxy/haproxy.cfg",
            "2. Test configuration: sudo haproxy -c -f /etc/haproxy/haproxy.cfg",
            "3. If test passes, reload: sudo systemctl reload haproxy",
            f"4. Verify: curl -I https://{domain}"
        ]
        
        return ServerConfig(
            platform='haproxy',
            config_code=config,
            steps=steps,
            verification_command='sudo haproxy -c -f /etc/haproxy/haproxy.cfg'
        )
    
    def _generate_generic(self, domain: str, token: str) -> ServerConfig:
        """Configuración genérica para otros servidores"""
        proxy_url = f"{self.proxy_base_url}/{token}"
        
        config = f"""# Generic Proxy Configuration

Proxy URL: {proxy_url}
Domain: {domain}

Configure your server to:
1. Forward all requests to: {proxy_url}
2. Preserve original headers:
   - Host: {domain}
   - X-Real-IP: <client_ip>
   - X-Forwarded-For: <client_ip>
   - X-Forwarded-Proto: http/https
3. Set timeout to 60 seconds
4. Disable buffering for optimal performance"""
        
        steps = [
            f"1. Configure your server to proxy all requests to: {proxy_url}",
            "2. Ensure you forward the original Host header",
            "3. Forward X-Real-IP and X-Forwarded-For headers",
            "4. Set appropriate timeouts (60s recommended)",
            f"5. Verify installation: Visit https://{domain}?mab_verify={token}"
        ]
        
        return ServerConfig(
            platform='generic',
            config_code=config,
            steps=steps
        )
    
    def get_supported_platforms(self) -> List[str]:
        """Obtener lista de plataformas soportadas"""
        return ['nginx', 'apache', 'cloudflare', 'haproxy', 'generic']
