# Components — Agent Guide

> **Parent**: [../AGENTS.md](../AGENTS.md) — frontend source

## Components

| Component | File | Props | Description |
|-----------|------|-------|-------------|
| `SearchBar` | [SearchBar.tsx](SearchBar.tsx) | `searchInput`, `onSearchInputChange`, `onReset`, `onRandom?`, `randomDisabled?` | Search input + reset + optional random-play button |
| `SongTable` | [SongTable.tsx](SongTable.tsx) | `rows`, `loading`, `mode`, `showLocal?` | Renders song rows with skeleton loading, missing-status badges, and Play links |
| `Pagination` | [Pagination.tsx](Pagination.tsx) | `page`, `totalPages`, `loading`, `items`, `onSetPage` | First/Prev/Next/Last + numbered page buttons with ellipsis |
| `SyncStatus` | [SyncStatus.tsx](SyncStatus.tsx) | `message` | Single-line sync status display |

## Key patterns

- All components are simple presentational/dumb components — no data fetching.
- `SongTable` shows skeleton rows when `loading && rows.length === 0`, and a translucent overlay when `loading && rows.length > 0`.
- `Pagination` accepts `items` as `(number | "ellipsis-left" | "ellipsis-right")[]` — the parent computes the pagination range.
- `SearchBar` conditionally renders the "Random Play" button only when `onRandom` is provided (playable mode only).