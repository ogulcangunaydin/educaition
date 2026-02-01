import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.database import Base, engine
from .middleware import RateLimitMiddleware
from .modules.auth.router import router as auth_router
from .modules.users.router import router as users_router
from .modules.rooms.router import router as rooms_router
from .modules.players.router import router as players_router, players_public_router
from .modules.games.router import router as games_router
from .modules.dissonance_test.router import (
    router as dissonance_test_router,
    dissonance_test_public_router,
)
from .modules.high_school_rooms.router import router as high_school_rooms_router
from .modules.program_suggestion.router import (
    router as program_suggestion_router,
    program_suggestion_public_router,
)
from . import models

log_level = logging.DEBUG if settings.DEBUG else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

models.User  # Ensure models are loaded
Base.metadata.create_all(bind=engine)

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

if not settings.is_development:
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=60,
        requests_per_hour=1000,
        auth_requests_per_minute=10,
    )

app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(users_router, prefix="/api", tags=["users"])
app.include_router(rooms_router, prefix="/api", tags=["rooms"])
app.include_router(players_router, prefix="/api", tags=["players"])
app.include_router(games_router, prefix="/api", tags=["games"])
app.include_router(dissonance_test_public_router, prefix="/api", tags=["dissonance_test"])
app.include_router(dissonance_test_router, prefix="/api", tags=["dissonance_test"])
app.include_router(high_school_rooms_router, prefix="/api", tags=["high_school_rooms"])
app.include_router(program_suggestion_public_router, prefix="/api", tags=["program_suggestion"])
app.include_router(program_suggestion_router, prefix="/api", tags=["program_suggestion"])
