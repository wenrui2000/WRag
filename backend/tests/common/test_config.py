import pytest
from pydantic import ValidationError
from common.config import Settings, load_settings

def test_settings_default_values():
    settings = Settings()
    assert settings.elasticsearch_url == "http://elasticsearch:9200"
    assert settings.elasticsearch_user == "elastic"
    assert settings.embedding_dim == 384
    assert settings.use_ollama is True
    assert settings.ollama_api_url == "http://ollama:11434"
    assert settings.default_model == "deepseek-r1:7b"
    assert settings.log_level == "INFO"
    assert settings.haystack_log_level == "INFO"

def test_settings_custom_values():
    custom_settings = {
        "elasticsearch_url": "http://custom:9200",
        "elasticsearch_user": "custom_user",
        "elasticsearch_password": "custom_pass",
        "embedding_dim": 768,
        "use_ollama": False,
        "ollama_api_url": "http://custom:11434",
        "default_model": "llama2",
        "log_level": "DEBUG",
        "haystack_log_level": "DEBUG"
    }
    settings = Settings(**custom_settings)
    
    for key, value in custom_settings.items():
        assert getattr(settings, key) == value

def test_invalid_log_level():
    with pytest.raises(ValidationError) as exc_info:
        Settings(log_level="INVALID")
    assert "Invalid log level" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        Settings(haystack_log_level="INVALID")
    assert "Invalid log level" in str(exc_info.value)

def test_valid_log_levels():
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    for level in valid_levels:
        settings = Settings(log_level=level, haystack_log_level=level)
        assert settings.log_level == level
        assert settings.haystack_log_level == level

def test_case_insensitive_log_levels():
    settings = Settings(log_level="debug", haystack_log_level="info")
    assert settings.log_level == "DEBUG"
    assert settings.haystack_log_level == "INFO" 