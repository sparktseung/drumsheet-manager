import { useEffect, useMemo, useRef, useState } from "react";

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

function cacheKey(mode: SongViewMode, searchText: string): string {
    return `${mode}::${searchText}`;
}

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
    const cachedCountKey = useRef<string | null>(null);
    const totalSongsRef = useRef(totalSongs);

    useEffect(() => {
        totalSongsRef.current = totalSongs;
    }, [totalSongs]);

    const offset = useMemo(() => (page - 1) * pageSize, [page, pageSize]);

    useEffect(() => {
        let cancelled = false;

        async function loadSongs() {
            setLoading(true);
            setError(null);

            const currentKey = cacheKey(mode, searchText);
            const countChanged = cachedCountKey.current !== currentKey;
            const count = totalSongsRef.current;

            try {
                const [songs, total] = await Promise.all([
                    fetchSongs({
                        mode,
                        searchText,
                        limit: pageSize,
                        offset,
                    }),
                    countChanged
                        ? fetchSongsCount({ mode, searchText })
                        : Promise.resolve(count),
                ]);

                if (cancelled) {
                    return;
                }

                setRows(songs);
                if (countChanged) {
                    setTotalSongs(total);
                    cachedCountKey.current = currentKey;
                }

                const resolvedCount = countChanged ? total : count;
                const maxPage = Math.max(1, Math.ceil(resolvedCount / pageSize));
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
