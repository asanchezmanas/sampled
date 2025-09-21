# backend/auth.py
import os
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from utils import Logger

class AuthManager:
    """Simple JWT authentication manager"""
    
    def __init__(self):
        self.logger = Logger()
        self.secret_key = os.environ.get("JWT_SECRET", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.token_expire_hours = 24
        
        if self.secret_key == "your-secret-key-change-in-production":
            self.logger.warning("Using default JWT secret - change in production!")
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            self.logger.error(f"Password verification failed: {str(e)}")
            return False
    
    def create_token(self, user_id: str) -> str:
        """Create JWT token for user"""
        payload = {
            'user_id': user_id,
            'exp': datetime.now(timezone.utc) + timedelta(hours=self.token_expire_hours),
            'iat': datetime.now(timezone.utc)
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user_id"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload.get('user_id')
        except jwt.ExpiredSignatureError:
            self.logger.debug("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.debug(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Token verification error: {str(e)}")
            return None