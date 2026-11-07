# Frontend Source — Agent Guide

> **Parent**: [../AGENTS.md](../AGENTS.md) — frontend root
> **Deeper**: [api/](api/AGENTS.md), [components/](components/AGENTS.md), [hooks/](hooks/AGENTS.md), [pages/](pages/AGENTS.md)

## Structure

```
src/
├── api/            # API client (fetch wrappers, type re-exports)
├── components/     # Reusable UI components
├── hooks/          # Custom React hooks
├── pages/          # Route-level page components
├── generated/      # Auto-generated OpenAPI types + spec
├── App.tsx         # Root component (song list, search, pagination)
├── main.tsx        # Entry point, BrowserRouter + routes
└── index.css       # Global styles
```

## Routing

| Path | Component | Description |
|------|-----------|-------------|
| `/` | `App` | Song list with search, pagination, mode toggle |
| `/songs/:songId` | `SongDetailPage` | PDF viewer + audio player |

## Data flow

1. `App.tsx` manages view mode (`playable`/`unplayable`), search text, page number.
2. `useSongsData` hook fetches songs + count from the API, handles loading/error states.
3. `useSyncStatus` hook polls sync job status and triggers a data refresh on completion.
4. `SongDetailPage` fetches a single song to get `loudness_gain_db`, then streams PDF + audio via `/files/` endpoints.

## Key patterns

- **No global state**: Each page/hook owns its state. Data refresh is triggered by incrementing a `refreshToken`.
- **Deferred search**: `useDeferredValue` on search input to avoid excessive API calls during typing.
- **Pagination**: Client-side pagination with ellipsis logic for large page counts.
- **Audio graph**: `SongDetailPage` creates a Web Audio `AudioContext` with a `GainNode` for loudness normalization.