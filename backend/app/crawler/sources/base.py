from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup

from app.models import Article
from app.crawler.utils import generate_article_id, normalize_url, clean_html, generate_summary, parse_datetime
from app.config import settings


class BaseSource(ABC):
    source_id: str = ""
    source_name: str = ""
    base_url: str = ""
    list_url: str = ""

    def __init__(self):
        self.config = settings.sources_config.get(self.source_id, {})

    @property
    def enabled(self) -> bool:
        return self.config.get("enabled", True)

    @property
    def interval_minutes(self) -> int:
        return self.config.get("interval_minutes", settings.default_crawl_interval_minutes)

    @abstractmethod
    async def parse_list(self, html: str) -> List[Dict[str, Any]]:
        pass

    async def parse_detail(self, html: str, article_data: Dict[str, Any]) -> Dict[str, Any]:
        return article_data

    async def fetch_detail(self, engine, article_data: Dict[str, Any]) -> Dict[str, Any]:
        url = article_data.get("url", "")
        try:
            html = await engine.fetch_html(url)
            return await self.parse_detail(html, article_data)
        except Exception as e:
            article_data["error"] = str(e)
            return article_data

    def _create_article(self, data: Dict[str, Any]) -> Article:
        url = data.get("url", "")
        normalized_url = normalize_url(url)
        article_id = data.get("id") or generate_article_id(url)

        publish_time = data.get("publish_time")
        if isinstance(publish_time, str):
            publish_time = parse_datetime(publish_time)

        summary = data.get("summary", "")
        content = data.get("content", "")

        if not summary and content:
            summary = generate_summary(content)

        if content:
            content = clean_html(content) if "<" in content else content

        return Article(
            id=article_id,
            title=data.get("title", "").strip(),
            source=self.source_id,
            source_name=self.source_name,
            url=url,
            normalized_url=normalized_url,
            author=data.get("author"),
            publish_time=publish_time,
            summary=summary,
            content=content,
            tags=data.get("tags", []),
            heat=data.get("heat"),
            crawled_at=datetime.now(),
            error=data.get("error"),
        )

    async def crawl_list(self, engine) -> List[Article]:
        if not self.enabled:
            return []

        try:
            html = await engine.fetch_html(self.list_url)
            items = await self.parse_list(html)

            articles = []
            for item in items:
                try:
                    article = self._create_article(item)
                    articles.append(article)
                except Exception:
                    continue

            return articles
        except Exception as e:
            raise Exception(f"Crawl list failed: {str(e)}") from e
