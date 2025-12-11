"""Application configuration settings."""
import os
from typing import Optional
from cryptography.fernet import Fernet
import base64


class Settings:
    """Application settings with environment variable support."""
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/skillboard")
    
    # HRMS Integration settings
    HRMS_BASE_URL: str = os.getenv("HRMS_BASE_URL", "http://127.0.0.1:8000")
    HRMS_TIMEOUT: int = int(os.getenv("HRMS_TIMEOUT", "30"))
    HRMS_INTEGRATION_EMAIL: str = os.getenv("HRMS_INTEGRATION_EMAIL", "")
    HRMS_INTEGRATION_PASSWORD: str = os.getenv("HRMS_INTEGRATION_PASSWORD", "")
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Encryption key for sensitive configuration data
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    
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