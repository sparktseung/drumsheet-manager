from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .dependencies import close_engine
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

app.include_router(health_router)
app.include_router(songs_router)
