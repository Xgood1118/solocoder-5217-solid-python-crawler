from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Article(BaseModel):
    id: str
    title: str
    source: str
    source_name: str
    url: str
    normalized_url: str
    author: Optional[str] = None
    publish_time: Optional[datetime] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    heat: Optional[int] = None
    crawled_at: datetime
    error: Optional[str] = None

    class Config:
        from_attributes = True


class ArticleListItem(BaseModel):
    id: str
    title: str
    source: str
    source_name: str
    url: str
    author: Optional[str] = None
    publish_time: Optional[datetime] = None
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    heat: Optional[int] = None
    crawled_at: datetime


class ArticleListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[ArticleListItem]


class CrawlSourceStatus(BaseModel):
    source: str
    source_name: str
    last_crawl_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    article_count: int = 0
    status: str = "idle"


class CrawlLogEntry(BaseModel):
    source: str
    timestamp: datetime
    status: str
    duration_seconds: float
    article_count: int = 0
    error: Optional[str] = None


class CrawlStatus(BaseModel):
    is_running: bool
    current_source: Optional[str] = None
    progress: float = 0.0
    total_sources: int = 0
    completed_sources: int = 0
    last_crawl_time: Optional[datetime] = None
    last_crawl_duration: Optional[float] = None
    total_articles: int = 0
    sources: Dict[str, CrawlSourceStatus] = Field(default_factory=dict)
    recent_logs: List[CrawlLogEntry] = Field(default_factory=list)


class CrawlTriggerRequest(BaseModel):
    mode: str = "incremental"


class CrawlTriggerResponse(BaseModel):
    success: bool
    message: str
    task_id: Optional[str] = None


class ClearDataResponse(BaseModel):
    success: bool
    message: str
    cleared_count: int


class RefreshArticleResponse(BaseModel):
    success: bool
    message: str
    article: Optional[Article] = None
