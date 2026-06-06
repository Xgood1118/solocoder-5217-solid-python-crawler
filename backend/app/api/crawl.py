from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
import json

from app.models import (
    CrawlStatus,
    CrawlTriggerRequest,
    CrawlTriggerResponse,
    ClearDataResponse,
)
from app.scheduler.manager import crawl_manager
from app.storage import article_store

router = APIRouter(prefix="/api/crawl", tags=["crawl"])


@router.get("/status", response_model=CrawlStatus)
async def get_crawl_status():
    return crawl_manager.get_status()


@router.post("/trigger", response_model=CrawlTriggerResponse)
async def trigger_crawl(request: CrawlTriggerRequest):
    if request.mode not in ("incremental", "full"):
        raise HTTPException(status_code=400, detail="Invalid mode. Use 'incremental' or 'full'")

    if crawl_manager._is_running:
        return CrawlTriggerResponse(
            success=False,
            message="Crawl is already running",
            task_id=None,
        )

    success = crawl_manager.trigger_crawl(mode=request.mode)
    return CrawlTriggerResponse(
        success=success,
        message="Crawl triggered successfully" if success else "Failed to trigger crawl",
        task_id="manual_crawl" if success else None,
    )


@router.post("/clear", response_model=ClearDataResponse)
async def clear_data():
    count = article_store.clear()
    return ClearDataResponse(
        success=True,
        message=f"Cleared {count} articles",
        cleared_count=count,
    )


@router.get("/progress")
async def crawl_progress():
    async def event_generator():
        last_status = None
        while True:
            status = crawl_manager.get_status()
            status_dict = {
                "is_running": status.is_running,
                "current_source": status.current_source,
                "progress": status.progress,
                "total_sources": status.total_sources,
                "completed_sources": status.completed_sources,
                "total_articles": status.total_articles,
                "last_crawl_time": status.last_crawl_time.isoformat() if status.last_crawl_time else None,
                "last_crawl_duration": status.last_crawl_duration,
            }
            current = json.dumps(status_dict, sort_keys=True)
            if current != last_status:
                yield f"data: {current}\n\n"
                last_status = current
            await asyncio.sleep(2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
