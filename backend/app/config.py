from pydantic_settings import BaseSettings
from typing import List, Dict


class Settings(BaseSettings):
    app_name: str = "News Aggregator"
    debug: bool = True

    frontend_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    max_articles: int = 10000

    concurrency_limit: int = 5
    request_timeout: int = 30
    retry_max_attempts: int = 3
    rate_limit_interval: float = 2.0

    default_crawl_interval_minutes: int = 30

    sources_config: Dict[str, Dict] = {
        "huxiu": {
            "name": "虎嗅",
            "url": "https://www.huxiu.com",
            "enabled": True,
            "interval_minutes": 30,
        },
        "36kr": {
            "name": "36氪",
            "url": "https://36kr.com",
            "enabled": True,
            "interval_minutes": 30,
        },
        "infoq": {
            "name": "InfoQ",
            "url": "https://www.infoq.cn",
            "enabled": True,
            "interval_minutes": 60,
        },
        "juejin": {
            "name": "掘金",
            "url": "https://juejin.cn",
            "enabled": True,
            "interval_minutes": 30,
        },
    }

    whitelist_domains: List[str] = []
    blacklist_domains: List[str] = []

    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    class Config:
        env_file = ".env"


settings = Settings()
