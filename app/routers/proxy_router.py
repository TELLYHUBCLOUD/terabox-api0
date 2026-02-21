from fastapi import APIRouter, BackgroundTasks
from app.core.proxy_pool import proxy_pool
from app.utils.logger import log

router = APIRouter(prefix="/proxy", tags=["Proxy Management"])


@router.get("/stats", summary="Proxy pool statistics")
async def proxy_stats():
    """Current proxy pool ki stats dekho"""
    return proxy_pool.stats()


@router.post("/refresh", summary="Proxy pool manually refresh karo")
async def refresh_proxies(background_tasks: BackgroundTasks):
    """
    Background mein proxy pool refresh karo.
    Response turant aata hai, refresh background mein hoti hai.
    """
    background_tasks.add_task(proxy_pool.refresh_pool)
    return {
        "message": "Proxy refresh background mein start ho gayi!",
        "current_pool_size": proxy_pool.stats()["active_proxies"],
    }


@router.get("/current", summary="Current proxy URL dekho")
async def current_proxy():
    """Abhi kaunsa proxy use ho raha hai"""
    proxy = proxy_pool.get_proxy()
    return {
        "proxy": proxy or "DIRECT (no proxy)",
        "tor_enabled": proxy_pool.stats()["tor_enabled"],
    }


@router.post("/rotate", summary="Manually next proxy pe switch karo")
async def rotate_proxy():
    """Force proxy rotation"""
    old = proxy_pool.get_proxy()
    proxy_pool._index += 1
    new = proxy_pool.get_proxy()
    log.info(f"Manual rotation: {old} → {new}")
    return {"old_proxy": old, "new_proxy": new}
