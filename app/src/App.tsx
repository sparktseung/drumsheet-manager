import { useCallback, useMemo, useState } from "react";

import {
  type SongViewMode,
} from "./api/client";
import Pagination from "./components/Pagination.tsx";
import SearchBar from "./components/SearchBar.tsx";
import SongTable from "./components/SongTable.tsx";
import SyncStatus from "./components/SyncStatus.tsx";
import { useSongsData } from "./hooks/useSongsData.ts";
import { useSyncStatus } from "./hooks/useSyncStatus.ts";

const PAGE_SIZE = 50;

type PaginationItem = number | "ellipsis-left" | "ellipsis-right";

function App() {
  const [mode, setMode] = useState<SongViewMode>("playable");
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [searchText, setSearchText] = useState("");
  const [refreshToken, setRefreshToken] = useState(0);

  const handlePageOverflow = useCallback((nextPage: number) => {
    setPage(nextPage);
  }, []);

  const { rows, totalSongs, loading, error } = useSongsData({
    mode,
    searchText,
    page,
    pageSize: PAGE_SIZE,
    refreshToken,
    onPageOverflow: handlePageOverflow,
  });

  const handleSyncFinished = useCallback(() => {
    setRefreshToken((value) => value + 1);
  }, []);

  const { syncMessage, onSyncLocalSongs } = useSyncStatus({
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

  function onSearch() {
    setPage(1);
    setSearchText(searchInput.trim());
  }

  function onResetSearch() {
    setSearchInput("");
    setSearchText("");
    setPage(1);
  }

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
          <button className="button" type="button" onClick={onSyncLocalSongs}>
            Sync Local Songs
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
          {mode === "unplayable" ? (
            <button className="button subtle" type="button" onClick={onOpenPlayableSongs}>
              Back To Playable Songs
            </button>
          ) : null}
        </div>

        <SyncStatus message={syncMessage} />

        <SearchBar
          searchInput={searchInput}
          onSearchInputChange={setSearchInput}
          onSearch={onSearch}
          onReset={onResetSearch}
        />

        {error ? <p className="error">{error}</p> : null}

        <SongTable
          rows={rows}
          loading={loading}
          mode={mode}
          onPlaySong={(songId) => window.open(`/songs/${songId}`, "_blank")}
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
