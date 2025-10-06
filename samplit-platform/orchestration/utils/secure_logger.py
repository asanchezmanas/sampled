# orchestration/utils/secure_logger.py

class SecureLogger:
    """
    Logger que sanitiza información sensible
    
    Previene que detalles de algoritmos aparezcan en logs
    """
    
    SENSITIVE_TERMS = [
        'thompson', 'bandit', 'epsilon', 'ucb',
        'beta distribution', 'bayesian', 'alpha', 'beta'
    ]
    
    REPLACEMENTS = {
        'thompson': 'adaptive',
        'bandit': 'optimizer',
        'epsilon': 'exploration',
        'ucb': 'confidence',
        'beta distribution': 'posterior',
        'bayesian': 'statistical'
    }
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log info with sanitization"""
        sanitized_msg = self._sanitize(message)
        sanitized_kwargs = {
            k: self._sanitize(str(v)) 
            for k, v in kwargs.items()
        }
        
        self.logger.info(sanitized_msg, extra=sanitized_kwargs)
    
    def _sanitize(self, text: str) -> str:
        """Remove sensitive terms"""
        lower_text = text.lower()
        
        for term in self.SENSITIVE_TERMS:
            if term in lower_text:
                replacement = self.REPLACEMENTS.get(term, 'proprietary')
                text = text.replace(term, replacement)
                text = text.replace(term.title(), replacement.title())
                text = text.replace(term.upper(), replacement.upper())
        
        return text
