"""Property-based tests for HRMS configuration security.

**Feature: hrms-integration, Property 12: Configuration Security Storage**
**Validates: Requirements 1.1**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base, HRMSConfiguration
from app.services.hrms_import import ConfigurationManager
from app.core.config import Settings
from contextlib import contextmanager
import tempfile
import os


@contextmanager
def create_test_db():
    """Create a temporary test database."""
    # Use in-memory SQLite database for simplicity
    engine = create_engine("sqlite:///:memory:")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()


# Hypothesis strategies for generating test data
config_key_strategy = st.text(
    min_size=1, 
    max_size=50, 
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-.")
)

config_value_strategy = st.text(
    min_size=1, 
    max_size=200, 
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs"), whitelist_characters="@#$%^&*()_+-=[]{}|;:,.<>?")
)

sensitive_config_strategy = st.text(
    min_size=8, 
    max_size=100, 
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="@#$%^&*()_+-=")
)


@given(
    config_key=config_key_strategy,
    config_value=sensitive_config_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_sensitive_config_encryption_round_trip(config_key, config_value):
    """
    **Feature: hrms-integration, Property 12: Configuration Security Storage**
    **Validates: Requirements 1.1**
    
    For any sensitive HRMS configuration, storing then retrieving should return 
    the original value while keeping it encrypted in storage.
    """
    with create_test_db() as test_db:
        # Create configuration manager
        config_manager = ConfigurationManager(test_db)
        
        # Store sensitive configuration
        config_manager.store_config(
            key=config_key,
            value=config_value,
            is_sensitive=True,
            description="Test sensitive config"
        )
        
        # Retrieve the configuration
        retrieved_value = config_manager.get_config(config_key)
        
        # Verify round-trip consistency
        assert retrieved_value == config_value
        
        # Verify that the stored value is actually encrypted (different from original)
        stored_config = test_db.query(HRMSConfiguration).filter(
            HRMSConfiguration.config_key == config_key
        ).first()
        
        assert stored_config is not None
        assert stored_config.is_encrypted == True
        assert stored_config.config_value != config_value  # Should be encrypted
        assert len(stored_config.config_value) > len(config_value)  # Encrypted data is longer


@given(
    config_key=config_key_strategy,
    config_value=config_value_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_non_sensitive_config_storage(config_key, config_value):
    """
    **Feature: hrms-integration, Property 12: Configuration Security Storage**
    **Validates: Requirements 1.1**
    
    For any non-sensitive HRMS configuration, storing then retrieving should return 
    the original value without encryption.
    """
    with create_test_db() as test_db:
        # Create configuration manager
        config_manager = ConfigurationManager(test_db)
        
        # Store non-sensitive configuration
        config_manager.store_config(
            key=config_key,
            value=config_value,
            is_sensitive=False,
            description="Test non-sensitive config"
        )
        
        # Retrieve the configuration
        retrieved_value = config_manager.get_config(config_key)
        
        # Verify round-trip consistency
        assert retrieved_value == config_value
        
        # Verify that the stored value is not encrypted (same as original)
        stored_config = test_db.query(HRMSConfiguration).filter(
            HRMSConfiguration.config_key == config_key
        ).first()
        
        assert stored_config is not None
        assert stored_config.is_encrypted == False
        assert stored_config.config_value == config_value  # Should not be encrypted


@given(
    configs=st.lists(
        st.tuples(
            config_key_strategy,
            config_value_strategy,
            st.booleans()  # is_sensitive flag
        ),
        min_size=1,
        max_size=10,
        unique_by=lambda x: x[0]  # Unique by config key
    )
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_multiple_config_security_consistency(configs):
    """
    **Feature: hrms-integration, Property 12: Configuration Security Storage**
    **Validates: Requirements 1.1**
    
    For any set of HRMS configurations with mixed sensitivity levels, 
    all configurations should maintain their security properties correctly.
    """
    with create_test_db() as test_db:
        # Create configuration manager
        config_manager = ConfigurationManager(test_db)
        
        # Store all configurations
        for config_key, config_value, is_sensitive in configs:
            config_manager.store_config(
                key=config_key,
                value=config_value,
                is_sensitive=is_sensitive,
                description=f"Test config - sensitive: {is_sensitive}"
            )
        
        # Verify all configurations
        for config_key, expected_value, is_sensitive in configs:
            # Retrieve the configuration
            retrieved_value = config_manager.get_config(config_key)
            
            # Verify round-trip consistency
            assert retrieved_value == expected_value
            
            # Verify encryption status
            stored_config = test_db.query(HRMSConfiguration).filter(
                HRMSConfiguration.config_key == config_key
            ).first()
            
            assert stored_config is not None
            assert stored_config.is_encrypted == is_sensitive
            
            if is_sensitive:
                # Sensitive configs should be encrypted in storage
                assert stored_config.config_value != expected_value
            else:
                # Non-sensitive configs should be stored as-is
                assert stored_config.config_value == expected_value


@given(
    config_key=config_key_strategy,
    original_value=sensitive_config_strategy,
    updated_value=sensitive_config_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_config_update_security_preservation(config_key, original_value, updated_value):
    """
    **Feature: hrms-integration, Property 12: Configuration Security Storage**
    **Validates: Requirements 1.1**
    
    For any sensitive HRMS configuration update, the security properties 
    should be preserved across updates.
    """
    # Skip if values are the same to ensure we're testing actual updates
    if original_value == updated_value:
        return
    
    with create_test_db() as test_db:
        # Create configuration manager
        config_manager = ConfigurationManager(test_db)
        
        # Store initial sensitive configuration
        config_manager.store_config(
            key=config_key,
            value=original_value,
            is_sensitive=True,
            description="Test sensitive config - original"
        )
        
        # Update the configuration
        config_manager.store_config(
            key=config_key,
            value=updated_value,
            is_sensitive=True,
            description="Test sensitive config - updated"
        )
        
        # Retrieve the updated configuration
        retrieved_value = config_manager.get_config(config_key)
        
        # Verify the update worked correctly
        assert retrieved_value == updated_value
        assert retrieved_value != original_value
        
        # Verify encryption is still maintained
        stored_config = test_db.query(HRMSConfiguration).filter(
            HRMSConfiguration.config_key == config_key
        ).first()
        
        assert stored_config is not None
        assert stored_config.is_encrypted == True
        assert stored_config.config_value != updated_value  # Should be encrypted
        assert stored_config.config_value != original_value  # Should be different from original


@given(config_key=config_key_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_nonexistent_config_retrieval(config_key):
    """
    **Feature: hrms-integration, Property 12: Configuration Security Storage**
    **Validates: Requirements 1.1**
    
    For any configuration key that doesn't exist, retrieval should return None 
    without causing security issues.
    """
    with create_test_db() as test_db:
        # Create configuration manager
        config_manager = ConfigurationManager(test_db)
        
        # Try to retrieve non-existent configuration
        retrieved_value = config_manager.get_config(config_key)
        
        # Should return None for non-existent keys
        assert retrieved_value is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])