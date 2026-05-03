from __future__ import annotations

from pathlib import Path

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".mp3", ".wav"})

_CONTENT_TYPES: dict[str, str] = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
}


class Audio:
    """Wraps an audio file path for streaming to the browser.

    ``FileResponse`` (starlette) handles ``Range`` request headers
    automatically, so ``<audio>`` seek works without extra code.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._content_type = _CONTENT_TYPES[path.suffix.lower()]

    @classmethod
    def load(cls, path: str | Path) -> Audio:
        """Validate and wrap *path*.

        Raises
        ------
        ValueError
            If the file extension is not a supported audio format.
        FileNotFoundError
            If the file does not exist on disk.
        """
        path = Path(path)
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported audio extension: {path.suffix!r}. "
                f"Expected one of {SUPPORTED_EXTENSIONS}."
            )
        if not path.is_file():
            raise FileNotFoundError(f"Audio file not found: {path}")
        return cls(path)

    @property
    def path(self) -> Path:
        return self._path

    @property
    def content_type(self) -> str:
        return self._content_type
