import { useEffect, useMemo, useState } from "react";

import {
    fetchSongs,
    fetchSongsCount,
    type SongRow,
    type SongViewMode,
} from "../api/client";

type UseSongsDataArgs = {
    mode: SongViewMode;
    searchText: string;
    page: number;
    pageSize: number;
    refreshToken: number;
    onPageOverflow: (nextPage: number) => void;
};

type UseSongsDataResult = {
    rows: SongRow[];
    totalSongs: number;
    loading: boolean;
    error: string | null;
};

export function useSongsData({
    mode,
    searchText,
    page,
    pageSize,
    refreshToken,
    onPageOverflow,
}: UseSongsDataArgs): UseSongsDataResult {
    const [rows, setRows] = useState<SongRow[]>([]);
    const [totalSongs, setTotalSongs] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const offset = useMemo(() => (page - 1) * pageSize, [page, pageSize]);

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
                        limit: pageSize,
                        offset,
                    }),
                    fetchSongsCount({
                        mode,
                        searchText,
                    }),
                ]);

                if (cancelled) {
                    return;
                }

                setRows(songs);
                setTotalSongs(total);

                const maxPage = Math.max(1, Math.ceil(total / pageSize));
                if (page > maxPage) {
                    onPageOverflow(maxPage);
                }
            } catch (loadError) {
                if (cancelled) {
                    return;
                }

                setError(
                    loadError instanceof Error
                        ? loadError.message
                        : "Failed to fetch songs.",
                );
                setRows([]);
                setTotalSongs(0);
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
    }, [mode, searchText, pageSize, offset, page, refreshToken, onPageOverflow]);

    return {
        rows,
        totalSongs,
        loading,
        error,
    };
}
