import asyncio
import time
from typing import Optional, Dict
from urllib.parse import urlparse

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from robotexclusionrulesparser import RobotExclusionRulesParser

from app.config import settings
from app.crawler.utils import extract_domain


class CrawlerEngine:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(settings.concurrency_limit)
        self._domain_locks: Dict[str, asyncio.Lock] = {}
        self._last_request_time: Dict[str, float] = {}
        self._robots_parsers: Dict[str, RobotExclusionRulesParser] = {}

    async def __aenter__(self):
        await self.init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()

    async def init_session(self):
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=settings.request_timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"User-Agent": settings.user_agent}
            )

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    def _get_domain_lock(self, domain: str) -> asyncio.Lock:
        if domain not in self._domain_locks:
            self._domain_locks[domain] = asyncio.Lock()
        return self._domain_locks[domain]

    async def _rate_limit(self, domain: str):
        lock = self._get_domain_lock(domain)
        async with lock:
            last_time = self._last_request_time.get(domain, 0)
            elapsed = time.time() - last_time
            if elapsed < settings.rate_limit_interval:
                wait_time = settings.rate_limit_interval - elapsed
                await asyncio.sleep(wait_time)
            self._last_request_time[domain] = time.time()

    async def _fetch_robots_txt(self, url: str) -> RobotExclusionRulesParser:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        domain = parsed.netloc.lower()

        if domain in self._robots_parsers:
            return self._robots_parsers[domain]

        robots_url = f"{base_url}/robots.txt"
        rp = RobotExclusionRulesParser()

        try:
            async with self.semaphore:
                await self._rate_limit(domain)
                async with self.session.get(robots_url) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        rp.parse(text.splitlines())
                    else:
                        rp.parse(["User-agent: *", "Allow: /"])
        except Exception:
            rp = RobotExclusionRulesParser()
            rp.parse(["User-agent: *", "Allow: /"])

        self._robots_parsers[domain] = rp
        return rp

    async def is_allowed_by_robots(self, url: str) -> bool:
        domain = extract_domain(url)
        if domain in settings.blacklist_domains:
            return False

        try:
            rp = await self._fetch_robots_txt(url)
            return rp.is_allowed("*", url)
        except Exception:
            return True

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True,
    )
    async def fetch(self, url: str, **kwargs) -> str:
        if not self.session:
            await self.init_session()

        domain = extract_domain(url)

        if domain in settings.blacklist_domains:
            raise Exception(f"Domain {domain} is in blacklist")

        if not await self.is_allowed_by_robots(url):
            raise Exception(f"URL {url} is disallowed by robots.txt")

        async with self.semaphore:
            await self._rate_limit(domain)
            async with self.session.get(url, **kwargs) as response:
                if response.status >= 500:
                    raise aiohttp.ClientError(f"Server error: {response.status}")
                if response.status == 404:
                    raise Exception(f"Not found: {url}")
                if response.status == 429:
                    raise aiohttp.ClientError(f"Rate limited: {response.status}")
                response.raise_for_status()
                return await response.text()

    async def fetch_html(self, url: str, **kwargs) -> str:
        return await self.fetch(url, **kwargs)
