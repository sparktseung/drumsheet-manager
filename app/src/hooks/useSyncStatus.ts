import { useCallback, useEffect, useRef, useState } from "react";

import {
    getCurrentSyncJob,
    getSyncJobStatus,
    startSyncJob,
    type SyncJob,
} from "../api/client";

type UseSyncStatusArgs = {
    onSyncFinished: () => void;
};

type UseSyncStatusResult = {
    syncMessage: string;
    isSyncing: boolean;
    onSyncLocalSongs: () => Promise<void>;
};

function formatSync(job: SyncJob | null): string {
    if (!job) {
        return "No sync currently running";
    }
    const base = `Sync ${job.status} (job ${job.job_id.slice(0, 8)})`;
    if (job.status === "failed" && job.error) {
        return `${base} — ${job.error}`;
    }
    return base;
}

export function useSyncStatus({
    onSyncFinished,
}: UseSyncStatusArgs): UseSyncStatusResult {
    const [syncMessage, setSyncMessage] = useState<string>("");
    const [syncJobId, setSyncJobId] = useState<string | null>(null);
    const [isSyncing, setIsSyncing] = useState(false);
    const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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

        async function poll() {
            try {
                const job = await getSyncJobStatus(syncJobId);
                if (cancelled) return;

                setSyncMessage(formatSync(job));

                if (job.status === "queued" || job.status === "running") {
                    timeoutRef.current = setTimeout(poll, 2000);
                } else {
                    setSyncJobId(null);
                    setIsSyncing(false);
                    onSyncFinished();
                }
            } catch (pollError) {
                if (cancelled) return;

                setSyncMessage(
                    pollError instanceof Error
                        ? pollError.message
                        : "Unable to read sync job state",
                );
                setSyncJobId(null);
                setIsSyncing(false);
            }
        }

        poll();

        return () => {
            cancelled = true;
            if (timeoutRef.current !== null) {
                clearTimeout(timeoutRef.current);
                timeoutRef.current = null;
            }
        };
    }, [syncJobId, onSyncFinished]);

    const onSyncLocalSongs = useCallback(async () => {
        try {
            const job = await startSyncJob();
            setSyncMessage(formatSync(job));
            setSyncJobId(job.job_id);
            setIsSyncing(true);
        } catch (syncError) {
            setSyncMessage(
                syncError instanceof Error
                    ? syncError.message
                    : "Failed to start sync job.",
            );
        }
    }, []);

    return {
        syncMessage,
        isSyncing,
        onSyncLocalSongs,
    };
}
