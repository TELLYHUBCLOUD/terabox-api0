import time
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.proxy_pool import proxy_pool
from app.routers import terabox_router, proxy_router
from app.utils.rate_limiter import rate_limit_middleware
from app.utils.logger import log

# Logs directory
os.makedirs("logs", exist_ok=True)

# ─── App Start/Stop ───────────────────────────────────────────────────────────

START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup aur shutdown events"""
    log.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    await proxy_pool.start()
    log.info("✅ All systems go!")
    yield
    log.info("🛑 Shutting down...")
    await proxy_pool.stop()


# ─── App Init ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 🚀 Terabox Direct Link Generator API

Terabox share URLs se **direct download links** generate karo — with:
- ⚡ Auto proxy rotation
- 🔄 Retry logic
- 💾 Response caching
- 🛡️ Rate limiting
- 📊 Live proxy stats

### Quick Start
```
GET /api/get-link?url=https://terabox.com/s/XXXXX
```
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ─── Middleware ───────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(rate_limit_middleware)


# ─── Exception Handlers ───────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# ─── Routers ─────────────────────────────────────────────────────────────────

app.include_router(terabox_router.router)
app.include_router(proxy_router.router)


# ─── Root Endpoints ───────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "get_link": "GET /api/get-link?url=TERABOX_URL",
            "batch":    "POST /api/batch",
            "proxy_stats": "GET /proxy/stats",
            "proxy_refresh": "POST /proxy/refresh",
            "cache_stats": "GET /api/cache/stats",
        },
    }


@app.get("/health", tags=["Info"])
async def health():
    stats = proxy_pool.stats()
    uptime = round(time.time() - START_TIME, 2)

    status = "healthy"
    if stats["active_proxies"] == 0:
        status = "degraded (no proxies)"

    return {
        "status": status,
        "version": settings.APP_VERSION,
        "uptime_seconds": uptime,
        "proxy_pool_size": stats["active_proxies"],
        "tor_enabled": stats["tor_enabled"],
    }
