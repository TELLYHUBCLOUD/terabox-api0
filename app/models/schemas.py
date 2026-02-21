from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional, List
from datetime import datetime


# ─── Request Models ──────────────────────────────────────────────────────────

class LinkRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_terabox_url(cls, v):
        allowed = ["terabox.com", "teraboxapp.com", "1024terabox.com", "www.terabox.app"]
        if not any(domain in v for domain in allowed):
            raise ValueError("Sirf Terabox URLs allowed hain")
        return v


# ─── Response Models ─────────────────────────────────────────────────────────

class FileInfo(BaseModel):
    filename: str
    size_bytes: int
    size_mb: float
    thumbnail: Optional[str] = None
    fs_id: str


class LinkResponse(BaseModel):
    success: bool
    filename: str
    size_bytes: int
    size_mb: float
    thumbnail: Optional[str] = None
    direct_link: str
    share_url: str
    proxy_used: Optional[str] = None
    cached: bool = False
    generated_at: datetime = datetime.utcnow()


class BatchRequest(BaseModel):
    urls: List[str]

    @field_validator("urls")
    @classmethod
    def max_urls(cls, v):
        if len(v) > 10:
            raise ValueError("Ek baar mein max 10 URLs allowed hain")
        return v


class BatchResponse(BaseModel):
    total: int
    success: int
    failed: int
    results: List[dict]


class ProxyStats(BaseModel):
    total_proxies: int
    active_proxies: int
    failed_proxies: int
    current_proxy: Optional[str]
    last_refreshed: Optional[datetime]
    tor_enabled: bool
    requests_served: int


class HealthResponse(BaseModel):
    status: str
    version: str
    proxy_pool_size: int
    cache_enabled: bool
    uptime_seconds: float
