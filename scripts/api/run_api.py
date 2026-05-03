from __future__ import annotations

import os

import uvicorn

if __name__ == "__main__":
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    reload_enabled = os.getenv("API_RELOAD", "1") == "1"

    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload_enabled,
    )
