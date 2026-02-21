# 🚀 Terabox Direct Link API

Terabox share URLs se **direct download links** generate karo — FastAPI + Auto Proxy Rotation.

---

## 📁 Project Structure

```
terabox-api/
├── main.py                          # FastAPI app entry point
├── requirements.txt
├── .env                             # Config
├── Dockerfile
├── docker-compose.yml
└── app/
    ├── core/
    │   ├── config.py                # Settings (pydantic-settings)
    │   ├── proxy_pool.py            # 🔄 Proxy Pool Manager
    │   └── terabox.py               # 🎯 Core Terabox fetcher
    ├── models/
    │   └── schemas.py               # Pydantic request/response models
    ├── routers/
    │   ├── terabox_router.py        # /api/* endpoints
    │   └── proxy_router.py          # /proxy/* endpoints
    └── utils/
        ├── logger.py                # Loguru logger
        ├── cache.py                 # In-memory TTL cache
        └── rate_limiter.py          # IP-based rate limiter
```

---

## ⚡ Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Run
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 3. Use
curl "http://localhost:8000/api/get-link?url=https://terabox.com/s/XXXXX"
```

---

## 🐳 Docker

```bash
docker-compose up -d
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/get-link?url=URL` | Single link generate karo |
| POST | `/api/get-link` | POST body se link |
| POST | `/api/batch` | Multiple links (max 10) |
| DELETE | `/api/cache` | Cache clear karo |
| GET | `/api/cache/stats` | Cache stats |
| GET | `/proxy/stats` | Proxy pool stats |
| POST | `/proxy/refresh` | Proxy pool refresh karo |
| POST | `/proxy/rotate` | Next proxy pe switch |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |

---

## 📥 Response Example

```json
{
  "success": true,
  "filename": "movie.mp4",
  "size_bytes": 866901140,
  "size_mb": 826.74,
  "thumbnail": "https://...",
  "direct_link": "https://d.terabox.app/file/abc...",
  "share_url": "https://terabox.com/s/XXXXX",
  "proxy_used": "http://103.152.x.x:80",
  "cached": false,
  "response_time_ms": 1243
}
```

---

## 🔄 Proxy Features

- **4 Free Sources** se automatically proxies fetch hote hain
- **Parallel testing** — sirf alive proxies pool mein jaate hain
- **Round-robin rotation** — har request pe proxy change
- **Auto failure tracking** — bad proxies automatically remove
- **Background refresh** — har 5 min mein fresh proxies
- **Tor support** — `.env` mein `USE_TOR=True` karo

---

## ⚙️ Configuration (.env)

```env
PROXY_REFRESH_INTERVAL=300     # Proxy refresh interval (seconds)
PROXY_MAX_FAILURES=3           # Kitni fails ke baad proxy hata dein
RATE_LIMIT_REQUESTS=30         # Per IP rate limit
CACHE_TTL=300                  # Cache TTL (seconds)
USE_TOR=False                  # Tor enable karo
TERABOX_MAX_RETRIES=3          # Retry attempts
```

---

## ⚠️ Disclaimer

Yeh project **educational/personal use** ke liye hai.
Terabox ke Terms of Service ka respect karein.
Commercial use ke liye official API use karein.
