"""
Authentication Manager

This module implements the main authentication manager that handles user
authentication, session management, and token generation.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

from .rbac import rbac, Role

class AuthManager:
    """
    Main Authentication Manager.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.jwt_secret = self.config.get("jwt_secret", "super-secret")
        self.jwt_algorithm = self.config.get("jwt_algorithm", "HS256")
        self.jwt_expire_minutes = self.config.get("jwt_expire_minutes", 30)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify user password."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash user password."""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.jwt_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)
        return encoded_jwt
    
    def decode_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode JWT access token."""
        try:
            decoded_token = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return decoded_token
        except jwt.PyJWTError:
            return None


