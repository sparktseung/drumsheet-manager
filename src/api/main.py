from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .dependencies import close_engine
from .routes.admin import router as admin_router
from .routes.files import router as files_router
from .routes.health import router as health_router
from .routes.songs import router as songs_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    close_engine()


app = FastAPI(
    title="Drum Sheet Manager API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_settings().cors_origins),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(songs_router)
app.include_router(files_router)
app.include_router(admin_router)
