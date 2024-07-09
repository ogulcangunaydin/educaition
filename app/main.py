from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI
from . import models, db_operations, routers
from .database import engine
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
load_dotenv()  # take environment variables from .env.

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specified origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

app.include_router(routers.router)
app.include_router(routers.router_without_auth)

@app.on_event("startup")
async def startup_event():
    db_operations.create_initial_user()
