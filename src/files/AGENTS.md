# Files — Agent Guide

> **Parent**: [../AGENTS.md](../AGENTS.md) — backend source

## Files

| File | Class | Description |
|------|-------|-------------|
| [audio.py](audio.py) | `Audio` | Wraps an audio file path for streaming |
| [drum_sheet.py](drum_sheet.py) | `DrumSheet` | Wraps a drum sheet PDF path for streaming |

## `Audio` — [audio.py](audio.py)

Wraps an audio file path for serving via `FileResponse`.

- **Supported extensions**: `.mp3`, `.wav`
- **Content types**: `audio/mpeg` (`.mp3`), `audio/wav` (`.wav`)
- **`load(path)`**: Validates the file exists and has a supported extension. Returns an `Audio` instance.
- **Properties**: `path` (`Path`), `content_type` (`str`)

## `DrumSheet` — [drum_sheet.py](drum_sheet.py)

Wraps a drum sheet PDF path for serving via `FileResponse`.

- **Supported extensions**: `.pdf`
- **Content type**: `application/pdf`
- **`load(path)`**: Validates the file exists and has a supported extension. Returns a `DrumSheet` instance.
- **Properties**: `path` (`Path`), `content_type` (`str`)

## Usage in routes

Both are used in [src/api/routes/files.py](../api/routes/files.py):
- `Audio.load(file_path)` / `DrumSheet.load(file_path)` validate the file exists before returning a `FileResponse`.
- `FileResponse` (Starlette) handles `Range` request headers automatically for audio seeking.