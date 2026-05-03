from __future__ import annotations

from pathlib import Path

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".pdf"})


class DrumSheet:
    """Wraps a drum sheet PDF file path for serving to the browser."""

    content_type: str = "application/pdf"

    def __init__(self, path: Path) -> None:
        self._path = path

    @classmethod
    def load(cls, path: str | Path) -> DrumSheet:
        """Validate and wrap *path*.

        Raises
        ------
        ValueError
            If the file extension is not a supported drum sheet format.
        FileNotFoundError
            If the file does not exist on disk.
        """
        path = Path(path)
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported drum sheet extension: {path.suffix!r}. "
                f"Expected one of {SUPPORTED_EXTENSIONS}."
            )
        if not path.is_file():
            raise FileNotFoundError(f"Drum sheet file not found: {path}")
        return cls(path)

    @property
    def path(self) -> Path:
        return self._path
