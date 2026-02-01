import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .config import settings
from .custom_session_middleware import CustomSessionMiddleware
from .core.database import engine
from .middleware import RateLimitMiddleware
from .modules.auth import auth_router
from .modules.users import users_router
from .modules.rooms import rooms_router
from .modules.players import players_router, players_public_router
from .modules.games import games_router
from .modules.dissonance_test import dissonance_test_router, dissonance_test_public_router
from .modules.high_school_rooms import high_school_rooms_router
from .modules.program_suggestion import program_suggestion_router, program_suggestion_public_router

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

if not settings.is_development:
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=60,
        requests_per_hour=1000,
        auth_requests_per_minute=10,
    )

# New modular routes
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
