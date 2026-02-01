import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models, routers
from .config import settings
from .custom_session_middleware import CustomSessionMiddleware
from .database import engine

log_level = logging.DEBUG if settings.DEBUG else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Educaition API in {settings.APP_ENV.value} mode")
    logger.info(f"Debug: {settings.DEBUG}")

    if settings.is_development:
        logger.info("To seed the database, run: python -m app.seeds.seed")

    yield

    logger.info("Shutting down Educaition API")


app = FastAPI(
    title="Educaition API",
    description="EducAItional platform API",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

if settings.is_development:
    origins = ["*"]
else:
    origins = [
        "http://localhost:8080",
        "http://192.168.1.106:8080",
        "http://ec2-54-173-57-250.compute-1.amazonaws.com",
        "http://educaition.com.tr",
        "https://educaition.com.tr",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CustomSessionMiddleware, secret_key=settings.SECRET_KEY)

app.include_router(routers.router, prefix="/api")
app.include_router(routers.router_without_auth, prefix="/api")
