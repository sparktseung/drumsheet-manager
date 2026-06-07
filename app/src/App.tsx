import { useCallback, useDeferredValue, useMemo, useState } from "react";

import {
  fetchRandomPlayableSong,
  type SongViewMode,
} from "./api/client";
import Pagination from "./components/Pagination.tsx";
import SearchBar from "./components/SearchBar.tsx";
import SongTable from "./components/SongTable.tsx";
import SyncStatus from "./components/SyncStatus.tsx";
import { useSongsData } from "./hooks/useSongsData.ts";
import { useSyncStatus } from "./hooks/useSyncStatus.ts";

const PAGE_SIZE = 10;

type PaginationItem = number | "ellipsis-left" | "ellipsis-right";

function App() {
  const [mode, setMode] = useState<SongViewMode>("playable");
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const deferredSearch = useDeferredValue(searchInput.trim());
  const [showLocal, setShowLocal] = useState(true);
  const [refreshToken, setRefreshToken] = useState(0);
  const [randomLoading, setRandomLoading] = useState(false);
  const [randomError, setRandomError] = useState<string | null>(null);

  const handlePageOverflow = useCallback((nextPage: number) => {
    setPage(nextPage);
  }, []);

  const { rows, totalSongs, loading, error } = useSongsData({
    mode,
    searchText: deferredSearch,
    page,
    pageSize: PAGE_SIZE,
    refreshToken,
    onPageOverflow: handlePageOverflow,
  });

  const handleSyncFinished = useCallback(() => {
    setRefreshToken((value) => value + 1);
  }, []);

  const { syncMessage, isSyncing, onSyncLocalSongs } = useSyncStatus({
    onSyncFinished: handleSyncFinished,
  });

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

  function onResetSearch() {
    setSearchInput("");
    setPage(1);
  }

  const onRandomSong = useCallback(async () => {
    setRandomError(null);

    const newTab = window.open("", "_blank");
    if (!newTab) {
      setRandomError("Unable to open new tab for a random song.");
      return;
    }

    setRandomLoading(true);
    try {
      const randomSong = await fetchRandomPlayableSong(searchInput);
      newTab.location.href = `/songs/${randomSong.song_id}`;
    } catch (randomError_) {
      newTab.close();
      setRandomError(
        randomError_ instanceof Error
          ? randomError_.message
          : "Failed to open a random song.",
      );
    } finally {
      setRandomLoading(false);
    }
  }, [searchInput]);

  function onOpenUnplayableSongs() {
    setMode("unplayable");
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
          <button
            className="button"
            type="button"
            onClick={onSyncLocalSongs}
            disabled={isSyncing}
          >
            {isSyncing ? "Syncing..." : "Sync Local Songs"}
          </button>
          <button
            className={`button ${mode === "unplayable" ? "active" : ""}`}
            type="button"
            onClick={onOpenUnplayableSongs}
          >
            View Unplayable Songs
          </button>
        </div>
      </header>

      <section className="panel">
        <div className="panel-header">
          <h2>{mode === "playable" ? "Playable Songs" : "Unplayable Songs"}</h2>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            {mode === "unplayable" ? (
              <button className="button subtle" type="button" onClick={onOpenPlayableSongs}>
                Back To Playable Songs
              </button>
            ) : null}
            <button
              className="button subtle"
              type="button"
              onClick={() => setShowLocal((v) => !v)}
            >
              {showLocal ? "Show English" : "Show Local"}
            </button>
          </div>
        </div>

        <SyncStatus message={syncMessage} />

        <SearchBar
          searchInput={searchInput}
          onSearchInputChange={setSearchInput}
          onReset={onResetSearch}
          onRandom={mode === "playable" ? onRandomSong : undefined}
          randomDisabled={randomLoading}
        />

        {error ? <p className="error">{error}</p> : null}
        {randomError ? <p className="error">{randomError}</p> : null}

        <SongTable
          rows={rows}
          loading={loading}
          mode={mode}
          showLocal={showLocal}
        />

        <Pagination
          page={page}
          totalPages={totalPages}
          loading={loading}
          items={paginationItems}
          onSetPage={setPage}
        />
      </section>
    </main>
  );
}

export default App;
