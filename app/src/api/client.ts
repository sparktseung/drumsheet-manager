import type { components } from "../generated/openapi-types";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL?.trim() || DEFAULT_API_BASE_URL;

export type SongRow = components["schemas"]["SongRow"];
export type SongCount = components["schemas"]["SongCount"];
export type SyncJob = components["schemas"]["SyncJob"];

export type SongViewMode = "playable" | "unplayable";

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

    const endpoint = mode === "playable" ? "/songs/playable" : "/songs/unplayable";
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
        mode === "playable" ? "/songs/playable/count" : "/songs/unplayable/count";
    const data = await requestJson<SongCount>(buildUrl(endpoint, query));
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
