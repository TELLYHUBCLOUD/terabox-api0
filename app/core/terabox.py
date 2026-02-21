import re
import time
from typing import Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.core.proxy_pool import proxy_pool
from app.utils.logger import log


# ─── Constants ────────────────────────────────────────────────────────────────

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.terabox.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

TERABOX_DOMAINS = [
    "www.terabox.com",
    "teraboxapp.com",
    "1024terabox.com",
    "www.terabox.app",
]


# ─── Helper Functions ─────────────────────────────────────────────────────────

def extract_surl(url: str) -> Optional[str]:
    """Share URL se surl/shortkey extract karo"""
    patterns = [
        r"/s/([a-zA-Z0-9_-]+)",
        r"surl=([a-zA-Z0-9_-]+)",
        r"sharing/link\?surl=([a-zA-Z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def normalize_terabox_url(url: str) -> str:
    """URL normalize karo — sab domains ko www.terabox.com pe route"""
    for domain in TERABOX_DOMAINS:
        if domain in url:
            return url.replace(domain, "www.terabox.com")
    return url


def bytes_to_mb(size: int) -> float:
    return round(size / (1024 * 1024), 2)


def build_client(proxy_url: Optional[str]) -> httpx.AsyncClient:
    """httpx client banao with/without proxy"""
    proxies = None
    if proxy_url:
        proxies = {
            "https://": proxy_url,
            "http://": proxy_url,
        }
    return httpx.AsyncClient(
        headers=BASE_HEADERS,
        proxies=proxies,
        timeout=settings.TERABOX_TIMEOUT,
        follow_redirects=True,
        verify=False,  # SSL ignore (proxy compatibility)
    )


# ─── Core Terabox Fetcher ─────────────────────────────────────────────────────

class TeraboxFetcher:

    async def get_direct_link(self, share_url: str) -> dict:
        """
        Main method — share URL se direct download link nikalo.
        Auto proxy rotation + retry included.
        """
        surl = extract_surl(share_url)
        if not surl:
            return {"error": "Invalid Terabox URL — surl extract nahi hua"}

        last_proxy = None
        start_time = time.time()

        for attempt in range(1, settings.TERABOX_MAX_RETRIES + 1):
            proxy_url = proxy_pool.get_proxy()
            last_proxy = proxy_url

            log.info(f"🔄 Attempt {attempt}/{settings.TERABOX_MAX_RETRIES} | Proxy: {proxy_url or 'DIRECT'}")

            try:
                result = await self._fetch(surl, share_url, proxy_url)

                elapsed = time.time() - start_time
                if proxy_url:
                    proxy_pool.report_success(proxy_url, elapsed)

                result["proxy_used"] = proxy_url
                log.info(f"✅ Link generated in {elapsed:.2f}s via {proxy_url or 'DIRECT'}")
                return result

            except httpx.ProxyError as e:
                log.warning(f"Proxy error ({proxy_url}): {e}")
                if proxy_url:
                    proxy_pool.report_failure(proxy_url)

            except httpx.TimeoutException as e:
                log.warning(f"Timeout ({proxy_url}): {e}")
                if proxy_url:
                    proxy_pool.report_failure(proxy_url)

            except Exception as e:
                log.error(f"Unexpected error attempt {attempt}: {e}")
                if proxy_url:
                    proxy_pool.report_failure(proxy_url)

        return {"error": f"Sabhi {settings.TERABOX_MAX_RETRIES} attempts fail ho gaye"}

    async def _fetch(self, surl: str, share_url: str, proxy_url: Optional[str]) -> dict:
        """Actual Terabox API calls"""
        async with build_client(proxy_url) as client:

            # ── Step 1: shorturlinfo ──────────────────────────────────────────
            info_url = (
                f"https://www.terabox.com/api/shorturlinfo"
                f"?app_id={settings.TERABOX_APP_ID}"
                f"&shorturl={surl}&root=1"
            )
            info_res = await client.get(info_url)
            info_res.raise_for_status()
            info = info_res.json()

            log.debug(f"shorturlinfo response errno: {info.get('errno')}")

            if info.get("errno") != 0:
                errno = info.get("errno")
                messages = {
                    -6: "Login required (private file)",
                    -1: "Invalid share link",
                    2: "Link expired",
                    105: "Illegal link",
                }
                raise ValueError(messages.get(errno, f"Terabox error: {errno}"))

            shareid   = info["shareid"]
            uk        = info["uk"]
            sign      = info["sign"]
            timestamp = info["timestamp"]
            file_list = info.get("list", [])

            if not file_list:
                raise ValueError("File list empty hai — folder ya deleted file")

            # ── Step 2: File metadata ─────────────────────────────────────────
            file = file_list[0]
            fs_id    = file["fs_id"]
            filename = file.get("server_filename", "unknown")
            size     = file.get("size", 0)
            thumb    = file.get("thumbs", {}).get("url3", "") or \
                       file.get("thumbs", {}).get("url2", "")

            log.debug(f"File: {filename} | Size: {bytes_to_mb(size)} MB | fs_id: {fs_id}")

            # ── Step 3: Download link ─────────────────────────────────────────
            dl_url = (
                f"https://www.terabox.com/api/dlink"
                f"?app_id={settings.TERABOX_APP_ID}"
                f"&shareid={shareid}&uk={uk}"
                f"&sign={sign}&timestamp={timestamp}"
                f"&fs_id={fs_id}&type=3"
            )
            dl_res = await client.get(dl_url)
            dl_res.raise_for_status()
            dl_data = dl_res.json()

            dlink = dl_data.get("dlink") or dl_data.get("list", [{}])[0].get("dlink")
            if not dlink:
                raise ValueError("dlink response mein nahi mila")

            return {
                "success": True,
                "filename": filename,
                "size_bytes": size,
                "size_mb": bytes_to_mb(size),
                "thumbnail": thumb,
                "direct_link": dlink,
                "share_url": share_url,
                "shareid": str(shareid),
                "fs_id": str(fs_id),
            }

    async def get_batch_links(self, urls: list) -> list:
        """Multiple URLs process karo"""
        tasks = [self.get_direct_link(url) for url in urls]
        import asyncio
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                output.append({"url": url, "error": str(result), "success": False})
            else:
                output.append({**result, "url": url})
        return output


# Global fetcher instance
terabox = TeraboxFetcher()
