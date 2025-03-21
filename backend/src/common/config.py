import logging
import os
import sys
import yaml
from enum import Enum
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import (
    Field,
    ValidationError,
    model_validator,
    field_validator
)


class OllamaModel(str, Enum):
    DEEPSEEK_1_5B = "deepseek-r1:1.5b"
    DEEPSEEK_7B = "deepseek-r1:7b"


class Settings(BaseSettings):
    # Elasticsearch settings
    elasticsearch_url: str = Field(default="http://elasticsearch:9200", description="Elasticsearch host URL")
    elasticsearch_user: str = Field(default="elastic", description="Elasticsearch username")
    elasticsearch_password: str = Field(default="", description="Elasticsearch password")
    
    # Qdrant settings
    qdrant_url: str = Field(default="http://qdrant:6333", description="Qdrant host URL")
    qdrant_collection_name: str = Field(default="semantic_search", description="Qdrant collection name")
    
    # MySQL settings
    mysql_host: str = Field(default="localhost", description="MySQL host")
    mysql_user: str = Field(default="root", description="MySQL username")
    mysql_password: str = Field(default="", description="MySQL password")
    mysql_database: str = Field(default="wrag", description="MySQL database name")
    mysql_port: int = Field(default=3306, description="MySQL port")
    mysql_enabled: bool = Field(default=False, description="Whether to use MySQL for document storage")
    
    # LLM settings
    generator: str = Field(default="ollama", description="Generator to use")
    use_ollama: bool = Field(default=True, description="Use Ollama for LLM")
    ollama_api_url: str = Field(default="http://ollama:11434", description="Ollama API URL")
    default_model: str = Field(
        default=OllamaModel.DEEPSEEK_7B.value, 
        description="Default Ollama model to use for inference"
    )
    # List of Ollama models to pull during build
    ollama_models: List[str] = Field(
        default=["deepseek-r1:1.5b", "deepseek-r1:7b"],
        description="Ollama models to pull during build"
    )
    
    # Generation parameters for LLM
    generation_kwargs: Dict[str, Any] = Field(
        default_factory=lambda: {"temperature": 0.7, "num_predict": 2048},
        description="Generation parameters for LLM"
    )
    
    # Embedding settings
    embedding_model: str = Field(default="intfloat/multilingual-e5-base", description="Model to use for embeddings")
    embedding_dim: int = Field(default=768, description="Embedding dimension")
    
    # Document processing settings
    split_by: str = Field(default="word", description="How to split documents")
    split_length: int = Field(default=250, description="Maximum split length")
    split_overlap: int = Field(default=30, description="Overlap between splits")
    
    # Application settings
    index_on_startup: bool = Field(default=True, description="Always index files on startup")
    pipelines_from_yaml: bool = Field(default=False, description="Load pipelines from YAML files")
    
    # Logging settings
    tokenizers_parallelism: bool = Field(default=False, description="Use tokenizers parallelism")
    log_level: str = Field(default="INFO", description="Logging level")
    haystack_log_level: str = Field(default="INFO", description="Wrag logging level")
    
    # Metrics settings
    metrics_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    prometheus_exporter: bool = Field(default=True, description="Enable Prometheus exporter for FastAPI")
    metrics_service_name: str = Field(default="wrag-app", description="Service name for metrics")
    
    # Tracing settings
    tracing_enabled: bool = Field(default=False, description="Enable OpenTelemetry tracing")
    jaeger_host: str = Field(default="jaeger", description="Jaeger host")
    jaeger_port: int = Field(default=6831, description="Jaeger port")
    tracing_content_enabled: bool = Field(default=True, description="Enable content tracing for Haystack")
    
    # Path settings
    pipelines_dir: Path = Field(
        default=Path(__file__).resolve().parent.parent / "pipelines",
        description="Path to pipelines directory"
    )
    file_storage_path: Path = Field(
        default=Path(__file__).resolve().parent.parent / "files",
        description="Path to file storage"
    )
    
    # Raw YAML config for custom settings
    raw_yaml_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw YAML configuration"
    )

    @field_validator('log_level', 'haystack_log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {', '.join(valid_levels)}")
        return upper_v
        
    @field_validator('default_model')
    @classmethod
    def validate_default_model(cls, v: str) -> str:
        # This allows any model from the ollama_models list
        # No longer using the hardcoded enum as the source of truth
        return v

    class Config:
        # env_file = Path(__file__).resolve().parent.parent / ".env"
        # env_file_encoding = 'utf-8'
        case_sensitive = False  # This allows case-insensitive matching of env vars


def find_config_file() -> Optional[Path]:
    """Find the config.yml file in standard locations."""
    locations = [
        # Current directory
        Path.cwd() / "config.yml",
        # Project root (up two directories from this file)
        Path(__file__).resolve().parent.parent.parent.parent / "config.yml",
        # /etc directory for system-wide configs
        Path("/etc/wrag-app/config.yml"),
        # User's home directory
        Path.home() / ".wrag-app/config.yml",
    ]
    
    for location in locations:
        if location.exists() and location.is_file():
            return location
    
    return None


def load_yaml_config() -> Dict[str, Any]:
    """Load configuration from YAML file."""
    config_file = find_config_file()
    
    if not config_file:
        print("Warning: No config.yml file found. Using default configuration.")
        return {}
    
    try:
        with open(config_file, 'r') as f:
            yaml_config = yaml.safe_load(f)
            print(f"Loaded configuration from {config_file}")
            return yaml_config or {}
    except Exception as e:
        print(f"Error loading config file: {e}")
        return {}


def yaml_to_env_vars(yaml_config: Dict[str, Any]) -> None:
    """Convert nested YAML config to flat environment variables."""
    if not yaml_config:
        return
    
    conversion_map = {
        "elasticsearch.url": "ELASTICSEARCH_URL",
        "elasticsearch.user": "ELASTICSEARCH_USER",
        "elasticsearch.password": "ELASTICSEARCH_PASSWORD",
        "qdrant.url": "QDRANT_URL",
        "qdrant.collection_name": "QDRANT_COLLECTION_NAME",
        "mysql.host": "MYSQL_HOST",
        "mysql.user": "MYSQL_USER",
        "mysql.password": "MYSQL_PASSWORD",
        "mysql.database": "MYSQL_DATABASE",
        "mysql.port": "MYSQL_PORT",
        "mysql.enabled": "MYSQL_ENABLED",
        "llm.generator": "GENERATOR",
        "llm.use_ollama": "USE_OLLAMA",
        "llm.ollama_api_url": "OLLAMA_API_URL",
        "llm.default_model": "DEFAULT_MODEL",
        "embedding.model": "EMBEDDING_MODEL",
        "embedding.dim": "EMBEDDING_DIM",
        "document.split_by": "SPLIT_BY",
        "document.split_length": "SPLIT_LENGTH",
        "document.split_overlap": "SPLIT_OVERLAP",
        "app.index_on_startup": "INDEX_ON_STARTUP",
        "app.pipelines_from_yaml": "PIPELINES_FROM_YAML",
        "logging.level": "LOG_LEVEL",
        "logging.wrag_level": "WRAG_LOG_LEVEL",
        "logging.tokenizers_parallelism": "TOKENIZERS_PARALLELISM",
        "metrics.enabled": "METRICS_ENABLED",
        "metrics.prometheus_exporter": "PROMETHEUS_EXPORTER",
        "metrics.service_name": "METRICS_SERVICE_NAME",
        "tracing.enabled": "TRACING_ENABLED",
        "tracing.jaeger_host": "JAEGER_HOST",
        "tracing.jaeger_port": "JAEGER_PORT",
        "tracing.content_enabled": "TRACING_CONTENT_ENABLED",
    }
    
    # Set environment variables from nested YAML config
    for yaml_path, env_var in conversion_map.items():
        keys = yaml_path.split(".")
        value = yaml_config
        
        # Navigate through nested structure
        for key in keys:
            if key in value:
                value = value[key]
            else:
                value = None
                break
        
        # Only set if value was found
        if value is not None:
            # Convert boolean and other types to string
            if isinstance(value, bool):
                value = str(value).lower()
            elif not isinstance(value, str):
                value = str(value)
                
            os.environ[env_var] = value


def load_settings():
    try:
        # First load config from YAML file
        yaml_config = load_yaml_config()
        
        # Convert YAML config to environment variables
        yaml_to_env_vars(yaml_config)
        
        # Also load .env file if it exists (for backward compatibility)
        # load_dotenv(Settings.Config.env_file)
        
        # Create settings object (will use environment variables)
        settings_obj = Settings()
        
        # Store the raw YAML config for any custom settings
        settings_obj.raw_yaml_config = yaml_config
        
        # Handle nested dictionaries like generation_kwargs
        if 'llm' in yaml_config and 'generation_kwargs' in yaml_config['llm']:
            settings_obj.generation_kwargs = yaml_config['llm']['generation_kwargs']
            print(f"Loaded generation_kwargs from config: {settings_obj.generation_kwargs}")
        
        return settings_obj
    except ValidationError as e:
        print("Error: Failed to load configuration settings.", file=sys.stderr)
        print("\nMissing or invalid settings:", file=sys.stderr)
        for error in e.errors():
            if "loc" in error and error["loc"]:
                field = ".".join(str(item) for item in error["loc"])
            else:
                field = "Unknown field"
            message = error.get("msg", "No error message provided")
            print(f"- {field}: {message}", file=sys.stderr)
        print("\nPlease check your config.yml file or environment variables.", file=sys.stderr)
        sys.exit(1)

# This will read from YAML config and environment variables
settings = load_settings()
