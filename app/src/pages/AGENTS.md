# Pages — Agent Guide

> **Parent**: [../AGENTS.md](../AGENTS.md) — frontend source

## Pages

| Page | File | Route | Description |
|------|------|-------|-------------|
| `SongDetailPage` | [SongDetailPage.tsx](SongDetailPage.tsx) | `/songs/:songId` | PDF drum sheet viewer + audio player with loudness normalization |

## `SongDetailPage`

### Features
- **PDF viewer**: Renders drum sheet via `react-pdf` `<Document>` + `<Page>`. Supports zoom (20%–120%) via +/- buttons.
- **Audio player**: Streams audio via `<audio>` element with Web Audio API gain node for loudness normalization.
- **Delayed start**: Configurable 0–10s countdown before playback begins (gives drummer time to get ready).
- **Seek controls**: -10s/+10s skip buttons, progress slider, reset button.
- **Responsive**: PDF page height adjusts to viewport minus the control bar.

### Audio graph
1. Creates an `AudioContext` and `MediaElementSource` from the `<audio>` element.
2. Inserts a `GainNode` with gain set to `10^(loudness_gain_db / 20)`.
3. Resumes suspended context on user interaction (browser autoplay policy).
4. Falls back to direct `<audio>` playback if Web Audio setup fails.

### State
- `playing`, `pendingStart`, `delaySeconds`, `countdownSeconds` — playback state
- `currentTime`, `duration` — audio position
- `gainDb` — fetched from song API, applied to gain node
- `zoomScale`, `viewportHeight`, `numPages` — PDF display