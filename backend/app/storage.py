from typing import List, Optional, Dict, Tuple
from datetime import datetime
from collections import OrderedDict
import threading

from app.models import Article
from app.config import settings
from app.crawler.utils import normalize_url


class ArticleStore:
    def __init__(self, max_articles: int = None):
        self.max_articles = max_articles or settings.max_articles
        self._articles: Dict[str, Article] = {}
        self._url_index: Dict[str, str] = {}
        self._ordered_ids: List[str] = []
        self._lock = threading.Lock()

    def add_article(self, article: Article) -> bool:
        with self._lock:
            normalized = article.normalized_url

            if normalized in self._url_index:
                existing_id = self._url_index[normalized]
                existing = self._articles.get(existing_id)
                if existing:
                    if article.content and not existing.content:
                        existing.content = article.content
                        existing.crawled_at = article.crawled_at
                    if article.summary and not existing.summary:
                        existing.summary = article.summary
                    if article.heat is not None and existing.heat is None:
                        existing.heat = article.heat
                    if article.publish_time and not existing.publish_time:
                        existing.publish_time = article.publish_time
                    existing.error = None
                    return False

            self._articles[article.id] = article
            self._url_index[normalized] = article.id
            self._ordered_ids.append(article.id)

            self._evict_old()

            return True

    def add_articles(self, articles: List[Article]) -> int:
        new_count = 0
        for article in articles:
            if self.add_article(article):
                new_count += 1
        return new_count

    def _evict_old(self):
        while len(self._ordered_ids) > self.max_articles:
            oldest_id = self._ordered_ids.pop(0)
            article = self._articles.pop(oldest_id, None)
            if article:
                self._url_index.pop(article.normalized_url, None)

    def get_article(self, article_id: str) -> Optional[Article]:
        with self._lock:
            return self._articles.get(article_id)

    def get_articles(
        self,
        page: int = 1,
        size: int = 20,
        sources: Optional[List[str]] = None,
        keyword: Optional[str] = None,
        sort: str = "publish_time",
    ) -> Tuple[List[Article], int]:
        with self._lock:
            articles = list(self._articles.values())

            if sources and len(sources) > 0:
                articles = [a for a in articles if a.source in sources]

            if keyword:
                keyword_lower = keyword.lower()
                articles = [
                    a for a in articles
                    if keyword_lower in (a.title or "").lower()
                    or keyword_lower in (a.summary or "").lower()
                ]

            if sort == "publish_time":
                articles.sort(
                    key=lambda a: a.publish_time or a.crawled_at,
                    reverse=True
                )
            elif sort == "heat":
                articles.sort(
                    key=lambda a: (a.heat is not None, a.heat or 0),
                    reverse=True
                )
            elif sort == "crawled_at":
                articles.sort(key=lambda a: a.crawled_at, reverse=True)

            total = len(articles)

            start = (page - 1) * size
            end = start + size
            paginated = articles[start:end]

            return paginated, total

    def count_by_source(self) -> Dict[str, int]:
        with self._lock:
            counts: Dict[str, int] = {}
            for article in self._articles.values():
                counts[article.source] = counts.get(article.source, 0) + 1
            return counts

    def clear(self) -> int:
        with self._lock:
            count = len(self._articles)
            self._articles.clear()
            self._url_index.clear()
            self._ordered_ids.clear()
            return count

    @property
    def total(self) -> int:
        with self._lock:
            return len(self._articles)

    def update_article(self, article_id: str, **kwargs) -> Optional[Article]:
        with self._lock:
            article = self._articles.get(article_id)
            if not article:
                return None
            for key, value in kwargs.items():
                if hasattr(article, key):
                    setattr(article, key, value)
            return article


article_store = ArticleStore()
