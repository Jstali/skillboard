"""Application configuration settings."""
import os
from typing import Optional
from cryptography.fernet import Fernet
import base64


class Settings:
    """Application settings with environment variable support.
    
    Uses properties to read from environment at runtime, allowing .env to be loaded first.
    """
    
    @property
    def DATABASE_URL(self) -> str:
        return os.getenv("DATABASE_URL", "postgresql://user:password@localhost/skillboard")
    
    @property
    def HRMS_BASE_URL(self) -> str:
        return os.getenv("HRMS_BASE_URL", "http://127.0.0.1:8000")
    
    @property
    def HRMS_TIMEOUT(self) -> int:
        return int(os.getenv("HRMS_TIMEOUT", "30"))
    
    @property
    def HRMS_INTEGRATION_EMAIL(self) -> str:
        return os.getenv("HRMS_INTEGRATION_EMAIL", "")
    
    @property
    def HRMS_INTEGRATION_PASSWORD(self) -> str:
        return os.getenv("HRMS_INTEGRATION_PASSWORD", "")
    
    @property
    def SECRET_KEY(self) -> str:
        return os.getenv("SECRET_KEY", "your-secret-key-here")
    
    ALGORITHM: str = "HS256"
    
    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    @property
    def ENCRYPTION_KEY(self) -> str:
        return os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    
    @property
    def fernet(self) -> Fernet:
        """Get Fernet encryption instance."""
        return Fernet(self.ENCRYPTION_KEY.encode())
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt a sensitive value."""
        return self.fernet.encrypt(value.encode()).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a sensitive value."""
        return self.fernet.decrypt(encrypted_value.encode()).decode()


# Global settings instance
settings = Settings()