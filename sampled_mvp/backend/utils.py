# backend/utils.py
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict

class Logger:
    """Simple structured logger"""
    
    def __init__(self, name: str = "mab-system"):
        self.logger = logging.getLogger(name)
        
        if not self.logger.handlers:
            # Configure handler
            handler = logging.StreamHandler(sys.stdout)
            
            # Set format
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
            self.logger.addHandler(handler)
            
            # Set level
            log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
            self.logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.debug(message)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.info(message)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.warning(message)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.error(message)

def generate_user_id(email: str = None, session_data: Dict[str, Any] = None) -> str:
    """Generate stable user ID for anonymous users"""
    import hashlib
    import uuid
    
    if email:
        # For logged-in users, use email hash
        return hashlib.md5(email.encode()).hexdigest()
    
    # For anonymous users, generate random but trackable ID
    if session_data and 'ip' in session_data and 'user_agent' in session_data:
        # Create stable ID based on IP + User Agent (for same device)
        fingerprint = f"{session_data['ip']}_{session_data['user_agent']}"
        return hashlib.md5(fingerprint.encode()).hexdigest()
    
    # Fallback to random UUID
    return str(uuid.uuid4())

def validate_experiment_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and set defaults for experiment config"""
    
    defaults = {
        "traffic_allocation": 1.0,  # 100% traffic
        "min_sample_size": 100,
        "confidence_threshold": 0.95,
        "auto_pause": False,
        "conversion_selectors": [],  # CSS selectors for auto-conversion detection
        "target_domains": [],  # Domains where experiment runs
        "exclude_bots": True
    }
    
    # Merge with defaults
    validated_config = {**defaults, **config}
    
    # Validate ranges
    if not 0.01 <= validated_config["traffic_allocation"] <= 1.0:
        validated_config["traffic_allocation"] = 1.0
    
    if not 0.8 <= validated_config["confidence_threshold"] <= 0.99:
        validated_config["confidence_threshold"] = 0.95
    
    if validated_config["min_sample_size"] < 10:
        validated_config["min_sample_size"] = 100
    
    return validated_config

def format_percentage(value: float, decimal_places: int = 1) -> str:
    """Format float as percentage"""
    return f"{value * 100:.{decimal_places}f}%"

def calculate_days_since(date: datetime) -> int:
    """Calculate days since a given date"""
    if not date:
        return 0
    
    now = datetime.now(timezone.utc)
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    
    delta = now - date
    return delta.days

class RateLimiter:
    """Simple in-memory rate limiter for MVP"""
    
    def __init__(self):
        self.requests = {}
        self.window_size = 60  # 1 minute
        self.max_requests = 100  # per minute
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed"""
        now = datetime.now().timestamp()
        
        # Clean old entries
        if key in self.requests:
            self.requests[key] = [
                timestamp for timestamp in self.requests[key] 
                if now - timestamp < self.window_size
            ]
        else:
            self.requests[key] = []
        
        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True

def sanitize_user_input(text: str, max_length: int = 1000) -> str:
    """Basic input sanitization"""
    if not isinstance(text, str):
        return ""
    
    # Remove control characters except newlines and tabs
    sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Strip whitespace
    return sanitized.strip()

def parse_user_agent(user_agent: str) -> Dict[str, str]:
    """Simple user agent parsing"""
    ua = user_agent.lower()
    
    result = {
        "browser": "unknown",
        "device": "desktop",
        "os": "unknown"
    }
    
    # Browser detection
    if "chrome" in ua:
        result["browser"] = "chrome"
    elif "firefox" in ua:
        result["browser"] = "firefox"
    elif "safari" in ua and "chrome" not in ua:
        result["browser"] = "safari"
    elif "edge" in ua:
        result["browser"] = "edge"
    
    # Device detection
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        result["device"] = "mobile"
    elif "tablet" in ua or "ipad" in ua:
        result["device"] = "tablet"
    
    # OS detection
    if "windows" in ua:
        result["os"] = "windows"
    elif "mac" in ua:
        result["os"] = "macos"
    elif "linux" in ua:
        result["os"] = "linux"
    elif "android" in ua:
        result["os"] = "android"
    elif "ios" in ua or "iphone" in ua or "ipad" in ua:
        result["os"] = "ios"
    
    return result

class HealthChecker:
    """System health checker"""
    
    def __init__(self, database_manager):
        self.db = database_manager
        self.logger = Logger()
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Comprehensive system health check"""
        
        health_status = {
            "status": "healthy",
            "checks": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Database check
        try:
            db_healthy = await self.db.health_check()
            health_status["checks"]["database"] = "ok" if db_healthy else "error"
        except Exception as e:
            health_status["checks"]["database"] = f"error: {str(e)}"
            health_status["status"] = "unhealthy"
        
        # Memory check (basic)
        try:
            import psutil
            memory = psutil.virtual_memory()
            health_status["checks"]["memory"] = {
                "usage_percent": memory.percent,
                "available_gb": round(memory.available / (1024**3), 2),
                "status": "ok" if memory.percent < 90 else "warning"
            }
            
            if memory.percent > 95:
                health_status["status"] = "unhealthy"
        except ImportError:
            health_status["checks"]["memory"] = "unavailable"
        
        # Basic system stats
        try:
            import os
            health_status["checks"]["system"] = {
                "pid": os.getpid(),
                "environment": os.environ.get("ENV", "production"),
                "python_version": sys.version.split()[0]
            }
        except Exception:
            pass
        
        return health_status

# Environment configuration helper
def get_env_config() -> Dict[str, Any]:
    """Get environment configuration"""
    return {
        "environment": os.environ.get("ENV", "production"),
        "debug": os.environ.get("DEBUG", "false").lower() == "true",
        "database_url": bool(os.environ.get("DATABASE_URL")),
        "jwt_secret_set": bool(os.environ.get("JWT_SECRET")),
        "log_level": os.environ.get("LOG_LEVEL", "INFO"),
        "port": os.environ.get("PORT", "8000")
    }

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format amount as currency"""
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "EUR":
        return f"€{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def calculate_confidence_interval(
    successes: int, 
    trials: int, 
    confidence_level: float = 0.95
) -> Dict[str, float]:
    """Calculate confidence interval for conversion rate"""
    if trials == 0:
        return {"lower": 0.0, "upper": 0.0, "rate": 0.0}
    
    rate = successes / trials
    
    # Wilson score interval (more accurate for small samples)
    from math import sqrt
    
    z_score = 1.96 if confidence_level == 0.95 else 2.576  # 99% confidence
    
    denominator = 1 + (z_score**2) / trials
    center = (rate + (z_score**2) / (2 * trials)) / denominator
    margin = z_score * sqrt((rate * (1 - rate) + (z_score**2) / (4 * trials)) / trials) / denominator
    
    return {
        "rate": rate,
        "lower": max(0, center - margin),
        "upper": min(1, center + margin)
    }