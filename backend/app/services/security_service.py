"""Security Hardening Service for GDPR Compliance.

This service provides encryption, input sanitization, and security
monitoring for HRMS integration.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime
import hashlib
import base64
import re
import logging

logger = logging.getLogger(__name__)


class SecurityViolation(BaseModel):
    """Security violation record."""
    timestamp: datetime
    violation_type: str
    details: str
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    severity: str  # low, medium, high, critical


class EncryptionService:
    """Simple encryption service for sensitive data."""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize encryption service.
        
        Args:
            secret_key: Secret key for encryption (should be from config)
        """
        self._key = secret_key or "default-key-change-in-production"
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string value.
        
        Note: This is a simple XOR-based encryption for demonstration.
        In production, use proper encryption like Fernet or AES.
        """
        if not plaintext:
            return ""
        
        # Simple XOR encryption (for demo - use proper encryption in production)
        key_bytes = self._key.encode()
        plaintext_bytes = plaintext.encode()
        
        encrypted = bytes([
            plaintext_bytes[i] ^ key_bytes[i % len(key_bytes)]
            for i in range(len(plaintext_bytes))
        ])
        
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.
        """
        if not ciphertext:
            return ""
        
        try:
            encrypted = base64.b64decode(ciphertext.encode())
            key_bytes = self._key.encode()
            
            decrypted = bytes([
                encrypted[i] ^ key_bytes[i % len(key_bytes)]
                for i in range(len(encrypted))
            ])
            
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return ""
    
    def hash_value(self, value: str) -> str:
        """Create a one-way hash of a value."""
        return hashlib.sha256(value.encode()).hexdigest()


class InputSanitizer:
    """Sanitizes input data to prevent injection attacks."""
    
    # Patterns that indicate potential injection attacks
    DANGEROUS_PATTERNS = [
        r"<script.*?>.*?</script>",  # XSS
        r"javascript:",  # XSS
        r"on\w+\s*=",  # Event handlers
        r"--",  # SQL comment
        r";.*drop\s+table",  # SQL injection
        r";\s*delete\s+from",  # SQL injection
        r"union\s+select",  # SQL injection
        r"'\s*or\s+'1'\s*=\s*'1",  # SQL injection
        r"\.\./",  # Path traversal
        r"\.\.\\",  # Path traversal (Windows)
    ]
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize sanitizer.
        
        Args:
            strict_mode: If True, reject suspicious input entirely
        """
        self.strict_mode = strict_mode
        self._compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS
        ]
    
    def sanitize_string(self, value: str) -> str:
        """
        Sanitize a string value.
        
        Args:
            value: Input string
            
        Returns:
            Sanitized string
        """
        if not value:
            return value
        
        # Check for dangerous patterns
        for pattern in self._compiled_patterns:
            if pattern.search(value):
                if self.strict_mode:
                    logger.warning(f"Dangerous pattern detected in input")
                    return ""
                else:
                    value = pattern.sub("", value)
        
        # HTML encode special characters
        value = self._html_encode(value)
        
        return value
    
    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize all string values in a dictionary.
        
        Args:
            data: Input dictionary
            
        Returns:
            Sanitized dictionary
        """
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            safe_key = self.sanitize_string(str(key))
            
            # Sanitize value based on type
            if isinstance(value, str):
                sanitized[safe_key] = self.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[safe_key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[safe_key] = self.sanitize_list(value)
            else:
                sanitized[safe_key] = value
        
        return sanitized
    
    def sanitize_list(self, data: List[Any]) -> List[Any]:
        """Sanitize all values in a list."""
        sanitized = []
        
        for item in data:
            if isinstance(item, str):
                sanitized.append(self.sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item))
            else:
                sanitized.append(item)
        
        return sanitized
    
    def _html_encode(self, value: str) -> str:
        """HTML encode special characters."""
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
        }
        
        for char, replacement in replacements.items():
            value = value.replace(char, replacement)
        
        return value
    
    def is_safe(self, value: str) -> bool:
        """Check if a value is safe (no dangerous patterns)."""
        if not value:
            return True
        
        for pattern in self._compiled_patterns:
            if pattern.search(value):
                return False
        
        return True


class SecurityMonitor:
    """Monitors and logs security events."""
    
    def __init__(self):
        """Initialize security monitor."""
        self._violations: List[SecurityViolation] = []
        self._rate_limits: Dict[str, List[datetime]] = {}
    
    def log_violation(
        self,
        violation_type: str,
        details: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        severity: str = "medium"
    ) -> SecurityViolation:
        """
        Log a security violation.
        
        Args:
            violation_type: Type of violation
            details: Violation details
            user_id: User ID if known
            ip_address: IP address if known
            severity: Severity level
            
        Returns:
            SecurityViolation record
        """
        violation = SecurityViolation(
            timestamp=datetime.utcnow(),
            violation_type=violation_type,
            details=details,
            user_id=user_id,
            ip_address=ip_address,
            severity=severity
        )
        
        self._violations.append(violation)
        
        # Log to system logger
        log_msg = f"Security violation: {violation_type} - {details}"
        if severity == "critical":
            logger.critical(log_msg)
        elif severity == "high":
            logger.error(log_msg)
        elif severity == "medium":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
        
        return violation
    
    def check_rate_limit(
        self,
        key: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if a rate limit has been exceeded.
        
        Args:
            key: Rate limit key (e.g., user_id or IP)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            True if within limit, False if exceeded
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        if key not in self._rate_limits:
            self._rate_limits[key] = []
        
        # Remove old entries
        self._rate_limits[key] = [
            t for t in self._rate_limits[key]
            if t > window_start
        ]
        
        # Check limit
        if len(self._rate_limits[key]) >= max_requests:
            self.log_violation(
                "rate_limit_exceeded",
                f"Rate limit exceeded for {key}",
                severity="medium"
            )
            return False
        
        # Add current request
        self._rate_limits[key].append(now)
        return True
    
    def get_recent_violations(
        self,
        limit: int = 100,
        severity: Optional[str] = None
    ) -> List[SecurityViolation]:
        """Get recent security violations."""
        violations = self._violations
        
        if severity:
            violations = [v for v in violations if v.severity == severity]
        
        return sorted(
            violations,
            key=lambda v: v.timestamp,
            reverse=True
        )[:limit]
    
    def get_violation_stats(self) -> Dict[str, Any]:
        """Get violation statistics."""
        total = len(self._violations)
        
        by_type = {}
        by_severity = {}
        
        for v in self._violations:
            by_type[v.violation_type] = by_type.get(v.violation_type, 0) + 1
            by_severity[v.severity] = by_severity.get(v.severity, 0) + 1
        
        return {
            "total": total,
            "by_type": by_type,
            "by_severity": by_severity
        }


# Import timedelta for rate limiting
from datetime import timedelta


# Global instances
_encryption_service: Optional[EncryptionService] = None
_security_monitor = SecurityMonitor()


def get_encryption_service(secret_key: Optional[str] = None) -> EncryptionService:
    """Get or create encryption service."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService(secret_key)
    return _encryption_service


def get_input_sanitizer(strict_mode: bool = True) -> InputSanitizer:
    """Create an InputSanitizer instance."""
    return InputSanitizer(strict_mode)


def get_security_monitor() -> SecurityMonitor:
    """Get the global security monitor."""
    return _security_monitor
