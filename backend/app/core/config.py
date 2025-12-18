"""Application configuration settings."""
import os
from typing import Optional
from cryptography.fernet import Fernet
import base64


class Settings:
    """Application settings with environment variable support.
    
    Uses properties to read from environment at runtime, allowing .env to be loaded first.
    """
    
    # Cache for encryption key to ensure consistency
    _encryption_key: Optional[str] = None
    _fernet_instance: Optional[Fernet] = None
    
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
        """Get encryption key, generating and caching if not set."""
        if Settings._encryption_key is None:
            env_key = os.getenv("ENCRYPTION_KEY")
            if env_key:
                Settings._encryption_key = env_key
            else:
                # Generate and cache a key for the session
                Settings._encryption_key = Fernet.generate_key().decode()
        return Settings._encryption_key
    
    @property
    def fernet(self) -> Fernet:
        """Get Fernet encryption instance, cached for consistency."""
        if Settings._fernet_instance is None:
            Settings._fernet_instance = Fernet(self.ENCRYPTION_KEY.encode())
        return Settings._fernet_instance
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt a sensitive value."""
        return self.fernet.encrypt(value.encode()).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a sensitive value."""
        return self.fernet.decrypt(encrypted_value.encode()).decode()


# Global settings instance
settings = Settings()