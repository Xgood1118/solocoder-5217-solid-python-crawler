import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque
import threading

from app.models import CrawlStatus, CrawlSourceStatus, CrawlLogEntry
from app.config import settings
from app.crawler.sources.huxiu import HuXiuSource
from app.crawler.sources.kr36 import Kr36Source
from app.crawler.sources.infoq import InfoQSource
from app.crawler.sources.juejin import JueJinSource
from app.crawler.engine import CrawlerEngine
from app.storage import article_store


class CrawlManager:
    def __init__(self):
        self._sources = {
            "huxiu": HuXiuSource(),
            "36kr": Kr36Source(),
            "infoq": InfoQSource(),
            "juejin": JueJinSource(),
        }

        self._source_status: Dict[str, CrawlSourceStatus] = {}
        for source_id, source in self._sources.items():
            cfg = settings.sources_config.get(source_id, {})
            self._source_status[source_id] = CrawlSourceStatus(
                source=source_id,
                source_name=cfg.get("name", source_id),
            )

        self._recent_logs: deque = deque(maxlen=10)
        self._is_running = False
        self._current_source: Optional[str] = None
        self._progress = 0.0
        self._total_sources = 0
        self._completed_sources = 0
        self._last_crawl_time: Optional[datetime] = None
        self._last_crawl_duration: Optional[float] = None

        self._skip_until: Dict[str, datetime] = {}
        self._consecutive_failures: Dict[str, int] = {}

        self._lock = threading.Lock()
        self._sse_listeners: List = []

    def get_status(self) -> CrawlStatus:
        source_counts = article_store.count_by_source()
        sources = {}
        for source_id, status in self._source_status.items():
            status.article_count = source_counts.get(source_id, 0)
            sources[source_id] = status

        return CrawlStatus(
            is_running=self._is_running,
            current_source=self._current_source,
            progress=self._progress,
            total_sources=self._total_sources,
            completed_sources=self._completed_sources,
            last_crawl_time=self._last_crawl_time,
            last_crawl_duration=self._last_crawl_duration,
            total_articles=article_store.total,
            sources=sources,
            recent_logs=list(self._recent_logs),
        )

    def _add_log(self, source: str, status: str, duration: float, article_count: int = 0, error: str = None):
        entry = CrawlLogEntry(
            source=source,
            timestamp=datetime.now(),
            status=status,
            duration_seconds=duration,
            article_count=article_count,
            error=error,
        )
        self._recent_logs.appendleft(entry)

    def _update_source_status(self, source_id: str, **kwargs):
        if source_id in self._source_status:
            status = self._source_status[source_id]
            for key, value in kwargs.items():
                if hasattr(status, key):
                    setattr(status, key, value)

    def _should_skip_source(self, source_id: str) -> bool:
        if source_id in self._skip_until:
            if datetime.now() < self._skip_until[source_id]:
                return True
            else:
                del self._skip_until[source_id]
        return False

    def _record_failure(self, source_id: str, error: str):
        failures = self._consecutive_failures.get(source_id, 0) + 1
        self._consecutive_failures[source_id] = failures

        if failures >= 3:
            self._skip_until[source_id] = datetime.now() + timedelta(hours=1)
            self._consecutive_failures[source_id] = 0

    def _record_success(self, source_id: str):
        self._consecutive_failures[source_id] = 0
        if source_id in self._skip_until:
            del self._skip_until[source_id]

    async def _crawl_source(self, engine: CrawlerEngine, source_id: str) -> int:
        source = self._sources.get(source_id)
        if not source:
            return 0

        if self._should_skip_source(source_id):
            self._update_source_status(
                source_id,
                status="skipped",
            )
            return 0

        self._current_source = source_id
        self._update_source_status(source_id, status="running")

        start_time = time.time()
        article_count = 0
        error_msg = None

        try:
            articles = await source.crawl_list(engine)
            article_count = article_store.add_articles(articles)

            self._update_source_status(
                source_id,
                last_crawl_time=datetime.now(),
                last_success_time=datetime.now(),
                status="success",
                last_error=None,
                consecutive_failures=0,
            )
            self._record_success(source_id)

        except Exception as e:
            error_msg = str(e)
            self._update_source_status(
                source_id,
                last_crawl_time=datetime.now(),
                last_failure_time=datetime.now(),
                last_error=error_msg,
                status="failed",
                consecutive_failures=self._consecutive_failures.get(source_id, 0) + 1,
            )
            self._record_failure(source_id, error_msg)

        finally:
            duration = time.time() - start_time
            status_str = "success" if error_msg is None else "failed"
            self._add_log(
                source=source_id,
                status=status_str,
                duration=duration,
                article_count=article_count,
                error=error_msg,
            )

        return article_count

    async def crawl_all(self, mode: str = "incremental") -> int:
        if self._is_running:
            return 0

        if mode == "full":
            article_store.clear()

        self._is_running = True
        total_articles = 0
        start_time = time.time()

        enabled_sources = [
            sid for sid, src in self._sources.items()
            if src.enabled
        ]
        self._total_sources = len(enabled_sources)
        self._completed_sources = 0
        self._progress = 0.0

        try:
            async with CrawlerEngine() as engine:
                for source_id in enabled_sources:
                    count = await self._crawl_source(engine, source_id)
                    total_articles += count
                    self._completed_sources += 1
                    self._progress = self._completed_sources / self._total_sources if self._total_sources > 0 else 0
        finally:
            self._is_running = False
            self._current_source = None
            self._last_crawl_time = datetime.now()
            self._last_crawl_duration = time.time() - start_time

        return total_articles

    async def refresh_article(self, article_id: str) -> Optional:
        article = article_store.get_article(article_id)
        if not article:
            return None

        source = self._sources.get(article.source)
        if not source:
            return None

        async with CrawlerEngine() as engine:
            try:
                article_data = {"url": article.url, "title": article.title}
                updated_data = await source.fetch_detail(engine, article_data)
                article_data.update(updated_data)

                if article_data.get("content"):
                    article_store.update_article(
                        article_id,
                        content=article_data["content"],
                        summary=article_data.get("summary") or article.summary,
                        crawled_at=datetime.now(),
                        error=None,
                    )
                return article_store.get_article(article_id)
            except Exception as e:
                article_store.update_article(article_id, error=str(e))
                return article_store.get_article(article_id)

    def trigger_crawl(self, mode: str = "incremental") -> bool:
        if self._is_running:
            return False
        loop = asyncio.new_event_loop()

        def run():
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.crawl_all(mode))
            loop.close()

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return True


crawl_manager = CrawlManager()
