import { Link } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";

import {
  fetchSongsCount,
  fetchSongs,
  getCurrentSyncJob,
  getSyncJobStatus,
  startSyncJob,
  type SongRow,
  type SyncJob,
} from "./api/client";

const PAGE_SIZE = 50;

type SongViewMode = "playable" | "problematic";
type PaginationItem = number | "ellipsis-left" | "ellipsis-right";

function formatSync(job: SyncJob | null): string {
  if (!job) {
    return "No sync currently running";
  }
  return `Sync ${job.status} (job ${job.job_id.slice(0, 8)})`;
}

function SongCell({ song, value }: { song: SongRow; value: string | null }) {
  if (!value) {
    return <span className="muted">-</span>;
  }

  return (
    <Link className="plain-link" to={`/songs/${song.song_id}`}>
      {value}
    </Link>
  );
}

function App() {
  const [mode, setMode] = useState<SongViewMode>("playable");
  const [rows, setRows] = useState<SongRow[]>([]);
  const [totalSongs, setTotalSongs] = useState(0);
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [searchText, setSearchText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syncMessage, setSyncMessage] = useState<string>("");
  const [syncJobId, setSyncJobId] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);

  const offset = useMemo(() => (page - 1) * PAGE_SIZE, [page]);
  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(totalSongs / PAGE_SIZE)),
    [totalSongs],
  );
  const paginationItems = useMemo<PaginationItem[]>(() => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    const items: PaginationItem[] = [1];
    const start = Math.max(2, page - 1);
    const end = Math.min(totalPages - 1, page + 1);

    if (start > 2) {
      items.push("ellipsis-left");
    }

    for (let p = start; p <= end; p += 1) {
      items.push(p);
    }

    if (end < totalPages - 1) {
      items.push("ellipsis-right");
    }

    items.push(totalPages);
    return items;
  }, [page, totalPages]);

  useEffect(() => {
    let cancelled = false;

    async function loadSongs() {
      setLoading(true);
      setError(null);

      try {
        const [songs, total] = await Promise.all([
          fetchSongs({
            mode,
            searchText,
            limit: PAGE_SIZE,
            offset,
          }),
          fetchSongsCount({
            mode,
            searchText,
          }),
        ]);
        if (!cancelled) {
          setRows(songs);
          setTotalSongs(total);

          const maxPage = Math.max(1, Math.ceil(total / PAGE_SIZE));
          if (page > maxPage) {
            setPage(maxPage);
          }
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Failed to fetch songs.",
          );
          setRows([]);
          setTotalSongs(0);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadSongs();

    return () => {
      cancelled = true;
    };
  }, [mode, searchText, offset, page, refreshToken]);

  useEffect(() => {
    void getCurrentSyncJob()
      .then((job) => {
        setSyncMessage(formatSync(job));
        if (job && (job.status === "queued" || job.status === "running")) {
          setSyncJobId(job.job_id);
        }
      })
      .catch(() => {
        setSyncMessage("Unable to read current sync state");
      });
  }, []);

  useEffect(() => {
    if (!syncJobId) {
      return;
    }

    let cancelled = false;

    async function pollSyncStatus() {
      try {
        const job = await getSyncJobStatus(syncJobId);
        if (cancelled) {
          return;
        }

        setSyncMessage(formatSync(job));

        if (job.status === "queued" || job.status === "running") {
          return;
        }

        setSyncJobId(null);
        setRefreshToken((value) => value + 1);
      } catch (pollError) {
        if (cancelled) {
          return;
        }

        setSyncMessage(
          pollError instanceof Error
            ? pollError.message
            : "Unable to read sync job state",
        );
        setSyncJobId(null);
      }
    }

    void pollSyncStatus();
    const intervalId = window.setInterval(() => {
      void pollSyncStatus();
    }, 2000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [syncJobId]);

  async function onSyncLocalSongs() {
    try {
      const job = await startSyncJob();
      setSyncMessage(formatSync(job));
      setSyncJobId(job.job_id);
    } catch (syncError) {
      setSyncMessage(
        syncError instanceof Error
          ? syncError.message
          : "Failed to start sync job.",
      );
    }
  }

  function onSearch() {
    setPage(1);
    setSearchText(searchInput.trim());
  }

  function onResetSearch() {
    setSearchInput("");
    setSearchText("");
    setPage(1);
  }

  function onOpenProblematicSyncs() {
    setMode("problematic");
    setPage(1);
  }

  function onOpenPlayableSongs() {
    setMode("playable");
    setPage(1);
  }

  return (
    <main className="page-shell">
      <header className="topbar">
        <h1 className="title">Drum Sheet Manager</h1>
        <div className="button-row">
          <button className="button" type="button" onClick={onSyncLocalSongs}>
            Sync Local Songs
          </button>
          <button
            className={`button ${mode === "problematic" ? "active" : ""}`}
            type="button"
            onClick={onOpenProblematicSyncs}
          >
            View Problematic Syncs
          </button>
        </div>
      </header>

      <section className="panel">
        <div className="panel-header">
          <h2>{mode === "playable" ? "Playable Songs" : "Problematic Syncs"}</h2>
          {mode === "problematic" ? (
            <button className="button subtle" type="button" onClick={onOpenPlayableSongs}>
              Back To Playable Songs
            </button>
          ) : null}
        </div>

        <p className="sync-status">{syncMessage}</p>

        <div className="search-row">
          <input
            className="search-input"
            type="text"
            placeholder="Search genre, artist, or song"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
          />
          <button className="button" type="button" onClick={onSearch}>
            Search
          </button>
          <button className="button subtle" type="button" onClick={onResetSearch}>
            Reset Search
          </button>
        </div>

        {error ? <p className="error">{error}</p> : null}

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>genre</th>
                <th>artist_local</th>
                <th>song_name_local</th>
              </tr>
            </thead>
            <tbody>
              {!loading && rows.length === 0 ? (
                <tr>
                  <td colSpan={3} className="muted center">
                    No songs found.
                  </td>
                </tr>
              ) : null}

              {rows.map((song) => (
                <tr key={song.song_id}>
                  <td>
                    <SongCell song={song} value={song.genre} />
                  </td>
                  <td>
                    <SongCell song={song} value={song.artist_local} />
                  </td>
                  <td>
                    <SongCell song={song} value={song.song_name_local} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <footer className="pager">
          <button
            className="button subtle"
            type="button"
            disabled={page === 1 || loading}
            onClick={() => setPage(1)}
          >
            First
          </button>
          <button
            className="button subtle"
            type="button"
            disabled={page === 1 || loading}
            onClick={() => setPage((prev) => Math.max(1, prev - 1))}
          >
            Previous
          </button>
          <div className="page-list" role="navigation" aria-label="Pagination">
            {paginationItems.map((item) => {
              if (typeof item !== "number") {
                return (
                  <span key={item} className="ellipsis" aria-hidden="true">
                    ...
                  </span>
                );
              }

              return (
                <button
                  key={item}
                  className={`button subtle page-number ${item === page ? "active-page" : ""}`}
                  type="button"
                  disabled={loading}
                  onClick={() => setPage(item)}
                >
                  {item}
                </button>
              );
            })}
          </div>
          <span className="page-label">
            Page {page} of {totalPages}
          </span>
          <button
            className="button subtle"
            type="button"
            disabled={page >= totalPages || loading}
            onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
          >
            Next
          </button>
          <button
            className="button subtle"
            type="button"
            disabled={page >= totalPages || loading}
            onClick={() => setPage(totalPages)}
          >
            Last
          </button>
        </footer>
      </section>
    </main>
  );
}

export default App;
