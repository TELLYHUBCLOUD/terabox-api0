from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from app.core.terabox import terabox
from app.core.proxy_pool import proxy_pool
from app.utils.cache import cache
from app.models.schemas import LinkRequest, LinkResponse, BatchRequest, BatchResponse
from app.utils.logger import log
import time

router = APIRouter(prefix="/api", tags=["Terabox"])


# ── Single Link ───────────────────────────────────────────────────────────────

@router.get(
    "/get-link",
    summary="Terabox direct link generate karo",
    description="Terabox share URL se direct download link nikalo. Auto proxy rotation included.",
)
async def get_direct_link(
    url: str = Query(..., description="Terabox share URL", example="https://terabox.com/s/1AbCdEf"),
    force: bool = Query(False, description="Cache ignore karo aur fresh link lo"),
):
    # Validate
    allowed_domains = ["terabox.com", "teraboxapp.com", "1024terabox.com"]
    if not any(d in url for d in allowed_domains):
        raise HTTPException(status_code=400, detail="Sirf Terabox URLs allowed hain")

    # Cache check
    if not force:
        cached = cache.get(url)
        if cached:
            cached["cached"] = True
            return cached

    # Fetch
    start = time.time()
    result = await terabox.get_direct_link(url)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    # Cache mein save karo
    cache.set(url, result)

    result["cached"] = False
    result["response_time_ms"] = round((time.time() - start) * 1000)
    return result


@router.post(
    "/get-link",
    summary="POST method se link generate karo",
)
async def get_direct_link_post(body: LinkRequest):
    return await get_direct_link(url=body.url, force=False)


# ── Batch Links ───────────────────────────────────────────────────────────────

@router.post(
    "/batch",
    summary="Multiple Terabox links ek baar mein",
    response_model=BatchResponse,
)
async def batch_links(body: BatchRequest):
    results = await terabox.get_batch_links(body.urls)

    success = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    return {
        "total": len(results),
        "success": len(success),
        "failed": len(failed),
        "results": results,
    }


# ── Cache Control ─────────────────────────────────────────────────────────────

@router.delete("/cache", summary="Cache clear karo")
async def clear_cache():
    stats = cache.stats()
    cache.clear()
    return {"message": "Cache cleared!", "cleared_entries": stats["active_keys"]}


@router.get("/cache/stats", summary="Cache statistics")
async def cache_stats():
    return cache.stats()
