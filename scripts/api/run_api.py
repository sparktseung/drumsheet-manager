from __future__ import annotations

import os

import uvicorn

from src.env import load_root_dotenv

if __name__ == "__main__":
    load_root_dotenv()
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    reload_enabled = os.getenv("API_RELOAD", "1") == "1"

    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload_enabled,
    )
