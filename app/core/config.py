from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Terabox Direct Link API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Proxy
    PROXY_REFRESH_INTERVAL: int = 300
    PROXY_TEST_TIMEOUT: int = 5
    PROXY_MAX_FAILURES: int = 3
    PROXY_POOL_MIN_SIZE: int = 10
    USE_TOR: bool = False
    TOR_SOCKS_PORT: int = 9050
    TOR_CONTROL_PORT: int = 9051
    TOR_ROTATE_EVERY: int = 60

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 30
    RATE_LIMIT_WINDOW: int = 60

    # Cache
    CACHE_TTL: int = 300
    USE_REDIS: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"

    # Terabox
    TERABOX_APP_ID: int = 250528
    TERABOX_TIMEOUT: int = 15
    TERABOX_MAX_RETRIES: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
