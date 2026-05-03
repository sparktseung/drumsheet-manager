const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL?.trim() || DEFAULT_API_BASE_URL;

export type SongRow = {
    song_id: string;
    in_master: boolean;
    artist_en: string | null;
    song_name_en: string | null;
    genre: string | null;
    artist_local: string | null;
    song_name_local: string | null;
    updated_at: string | null;
    audio_available: boolean;
    audio_file_path: string | null;
    drum_sheet_available: boolean;
    drum_sheet_file_path: string | null;
    source_available: boolean;
    source_file_path: string | null;
};

export type SyncJob = {
    job_id: string;
    status: "queued" | "running" | "succeeded" | "failed";
    created_at: string;
    started_at: string | null;
    finished_at: string | null;
    error: string | null;
};

type SongViewMode = "playable" | "problematic";

type FetchSongsArgs = {
    mode: SongViewMode;
    searchText: string;
    limit: number;
    offset: number;
};

type FetchSongsCountArgs = {
    mode: SongViewMode;
    searchText: string;
};

function buildUrl(path: string, query?: URLSearchParams): string {
    const base = API_BASE_URL.replace(/\/$/, "");
    const queryPart = query && query.toString() ? `?${query.toString()}` : "";
    return `${base}${path}${queryPart}`;
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
    const response = await fetch(url, {
        ...init,
        headers: {
            "Content-Type": "application/json",
            ...(init?.headers ?? {}),
        },
    });

    if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Request failed with status ${response.status}`);
    }

    return (await response.json()) as T;
}

export async function fetchSongs({
    mode,
    searchText,
    limit,
    offset,
}: FetchSongsArgs): Promise<SongRow[]> {
    const query = new URLSearchParams();
    query.set("limit", String(limit));
    query.set("offset", String(offset));

    if (searchText.trim()) {
        query.set("q", searchText.trim());
    }

    const endpoint = mode === "playable" ? "/songs/playable" : "/songs/incomplete";
    return requestJson<SongRow[]>(buildUrl(endpoint, query));
}

export async function fetchSongsCount({
    mode,
    searchText,
}: FetchSongsCountArgs): Promise<number> {
    const query = new URLSearchParams();

    if (searchText.trim()) {
        query.set("q", searchText.trim());
    }

    const endpoint =
        mode === "playable" ? "/songs/playable/count" : "/songs/incomplete/count";
    const data = await requestJson<{ total: number }>(buildUrl(endpoint, query));
    return data.total;
}

export async function startSyncJob(): Promise<SyncJob> {
    return requestJson<SyncJob>(buildUrl("/admin/sync"), {
        method: "POST",
    });
}

export async function getCurrentSyncJob(): Promise<SyncJob | null> {
    return requestJson<SyncJob | null>(buildUrl("/admin/sync/current"));
}

export async function getSyncJobStatus(jobId: string): Promise<SyncJob> {
    return requestJson<SyncJob>(buildUrl(`/admin/sync/${jobId}`));
}
