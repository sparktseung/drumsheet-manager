# Hooks — Agent Guide

> **Parent**: [../AGENTS.md](../AGENTS.md) — frontend source

## Hooks

| Hook | File | Description |
|------|------|-------------|
| `useSongsData` | [useSongsData.ts](useSongsData.ts) | Fetches paginated song rows + total count from the API |
| `useSyncStatus` | [useSyncStatus.ts](useSyncStatus.ts) | Manages sync job lifecycle: start, poll, completion callback |

## `useSongsData`

**Args**: `{ mode, searchText, page, pageSize, refreshToken, onPageOverflow }`

**Returns**: `{ rows, totalSongs, loading, error }`

**Behavior**:
- Fetches songs and count in parallel via `Promise.all`.
- Caches the count key (`mode::searchText`) to avoid re-fetching the count when only the page changes.
- Calls `onPageOverflow(maxPage)` when the current page exceeds the available pages (e.g. after search narrows results).
- Re-fetches when `mode`, `searchText`, `page`, `pageSize`, or `refreshToken` changes.

## `useSyncStatus`

**Args**: `{ onSyncFinished }`

**Returns**: `{ syncMessage, isSyncing, onSyncLocalSongs }`

**Behavior**:
- On mount, checks for an already-running sync job via `GET /admin/sync/current`.
- `onSyncLocalSongs()` calls `POST /admin/sync` to start a new job.
- Polls `GET /admin/sync/{jobId}` every 2s while the job is queued/running.
- Calls `onSyncFinished` when the job completes (succeeded or failed).
- Cleans up polling on unmount.