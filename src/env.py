from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


@lru_cache(maxsize=1)
def get_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def load_root_dotenv() -> Path:
    dotenv_path = get_repo_root() / ".env"
    load_dotenv(dotenv_path=dotenv_path)
    return dotenv_path
