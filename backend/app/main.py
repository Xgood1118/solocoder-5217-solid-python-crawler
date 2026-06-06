from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api.articles import router as articles_router
from app.api.crawl import router as crawl_router
from app.scheduler.scheduler import init_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles_router)
app.include_router(crawl_router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name}


@app.get("/")
async def root():
    return {"message": "News Aggregator API", "version": "1.0.0"}
