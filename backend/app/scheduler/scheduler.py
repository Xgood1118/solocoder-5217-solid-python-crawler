from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio
import threading

from app.scheduler.manager import crawl_manager
from app.config import settings


scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def _run_crawl_job():
    if crawl_manager._is_running:
        return
    loop = asyncio.new_event_loop()

    def run():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(crawl_manager.crawl_all(mode="incremental"))
        loop.close()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()


def init_scheduler():
    sources_config = settings.sources_config

    for source_id, config in sources_config.items():
        if not config.get("enabled", True):
            continue

        interval = config.get("interval_minutes", settings.default_crawl_interval_minutes)

        scheduler.add_job(
            _run_crawl_job,
            trigger=IntervalTrigger(minutes=interval),
            id=f"crawl_{source_id}",
            name=f"Crawl {source_id}",
            replace_existing=True,
            misfire_grace_time=60,
            coalesce=True,
            max_instances=1,
        )

    scheduler.start()


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
