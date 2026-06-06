from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List

from app.models import Article, ArticleListResponse, ArticleListItem, RefreshArticleResponse
from app.storage import article_store
from app.scheduler.manager import crawl_manager

router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.get("", response_model=ArticleListResponse)
async def get_articles(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    source: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    sort: str = Query("publish_time", pattern="^(publish_time|heat|crawled_at)$"),
):
    sources: Optional[List[str]] = None
    if source:
        sources = [s.strip() for s in source.split(",") if s.strip()]

    articles, total = article_store.get_articles(
        page=page,
        size=size,
        sources=sources,
        keyword=keyword,
        sort=sort,
    )

    items = [
        ArticleListItem(
            id=a.id,
            title=a.title,
            source=a.source,
            source_name=a.source_name,
            url=a.url,
            author=a.author,
            publish_time=a.publish_time,
            summary=a.summary,
            tags=a.tags,
            heat=a.heat,
            crawled_at=a.crawled_at,
        )
        for a in articles
    ]

    return ArticleListResponse(
        total=total,
        page=page,
        size=size,
        items=items,
    )


@router.get("/{article_id}", response_model=Article)
async def get_article_detail(article_id: str):
    article = article_store.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post("/{article_id}/refresh", response_model=RefreshArticleResponse)
async def refresh_article(article_id: str):
    article = article_store.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    updated = await crawl_manager.refresh_article(article_id)
    if not updated:
        return RefreshArticleResponse(
            success=False,
            message="Refresh failed",
            article=None,
        )

    return RefreshArticleResponse(
        success=True,
        message="Article refreshed successfully",
        article=updated,
    )
