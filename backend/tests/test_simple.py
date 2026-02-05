import pytest


def test_basic_import():
    """Test that basic imports work."""
    from app.main import app
    from app.core.config import settings
    
    assert app is not None
    assert settings is not None


def test_config_exists():
    """Test configuration exists."""
    from app.core.config import settings
    
    assert settings.DATABASE_URL is not None
    assert settings.SECRET_KEY is not None
    assert settings.ALGORITHM == "HS256"
