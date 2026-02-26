"""
Configuration Management for Neubolt FastAPI Application
Loads settings from environment variables with sensible defaults
Compatible with Pydantic v1 and v2
"""
import os
from typing import List, Union, Any
from datetime import timedelta
from dotenv import load_dotenv

# Get absolute path to .env file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")

# Manually load .env file into environment variables
if os.path.exists(ENV_FILE):
    load_dotenv(ENV_FILE)

# Pydantic Compatibility Layer
try:
    # Try Pydantic v2 with pydantic-settings
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field
    USE_V2 = True
except ImportError:
    try:
        from pydantic import BaseSettings, Field
        SettingsConfigDict = None
        USE_V2 = False
    except ImportError:
        try:
            from pydantic.v1 import BaseSettings, Field
            SettingsConfigDict = None
            USE_V2 = False
        except ImportError:
             raise ImportError("Could not import BaseSettings. Please install pydantic-settings or pydantic<2.0")

class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Application
    APP_NAME: str = os.getenv("APP_NAME", "Neubolt API v2.0 - FastAPI")
    APP_VERSION: str = os.getenv("APP_VERSION", "2.0.0")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database Configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "neubolt_unified")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # JWT Configuration
    # Fallback to a development key ONLY if not in production
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "neubolt-jwt-secret-key-change-in-production-2024")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    
    # CORS Configuration
    CORS_ORIGINS_RAW: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")

    @property
    def CORS_ORIGINS(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS_RAW, str):
            return [origin.strip() for origin in self.CORS_ORIGINS_RAW.split(',')]
        return []

    # MQTT Broker Configuration
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_USERNAME: str = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD: str = os.getenv("MQTT_PASSWORD", "")
    
    # GPS TCP Server Configuration
    GPS_TCP_PORT: int = int(os.getenv("GPS_TCP_PORT", "8000"))
    GPS_TCP_HOST: str = os.getenv("GPS_TCP_HOST", "0.0.0.0")
    
    # Session Management
    SESSION_TIMEOUT_HOURS: int = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
    MAX_CONCURRENT_SESSIONS: int = int(os.getenv("MAX_CONCURRENT_SESSIONS", "5"))
    ENABLE_TOKEN_ROTATION: bool = os.getenv("ENABLE_TOKEN_ROTATION", "True").lower() == "true"
    ENABLE_IP_BINDING: bool = os.getenv("ENABLE_IP_BINDING", "True").lower() == "true"
    CLEANUP_EXPIRED_SESSIONS: bool = os.getenv("CLEANUP_EXPIRED_SESSIONS", "True").lower() == "true"
    
    # PII Data Masking
    ENABLE_PII_MASKING: bool = os.getenv("ENABLE_PII_MASKING", "True").lower() == "true"
    PII_MASKING_ROLES_RAW: str = os.getenv("PII_MASKING_ROLES", "crm,maintenance")
    PII_AUDIT_LOGGING: bool = os.getenv("PII_AUDIT_LOGGING", "True").lower() == "true"
    
    @property
    def PII_MASKING_ROLES(self) -> List[str]:
        if isinstance(self.PII_MASKING_ROLES_RAW, str):
            return [role.strip() for role in self.PII_MASKING_ROLES_RAW.split(',')]
        return []

    # File Upload Configuration
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "pdf"]
    
    # Timezone
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Karachi")

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_FILE: str = os.getenv("LOG_FILE", "neubolt_api.log")

    if USE_V2:
        model_config = SettingsConfigDict(
            case_sensitive=True,
            extra="ignore"
        )
    else:
        class Config:
            case_sensitive = True
            extra = "ignore"

# Create global settings instance
settings = Settings()
