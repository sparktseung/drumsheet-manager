import { useCallback, useEffect, useState } from "react";

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
    onSyncLocalSongs: () => Promise<void>;
};

function formatSync(job: SyncJob | null): string {
    if (!job) {
        return "No sync currently running";
    }
    return `Sync ${job.status} (job ${job.job_id.slice(0, 8)})`;
}

export function useSyncStatus({
    onSyncFinished,
}: UseSyncStatusArgs): UseSyncStatusResult {
    const [syncMessage, setSyncMessage] = useState<string>("");
    const [syncJobId, setSyncJobId] = useState<string | null>(null);

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
        const activeJobId = syncJobId;

        let cancelled = false;

        async function pollSyncStatus() {
            try {
                const job = await getSyncJobStatus(activeJobId);
                if (cancelled) {
                    return;
                }

                setSyncMessage(formatSync(job));

                if (job.status === "queued" || job.status === "running") {
                    return;
                }

                setSyncJobId(null);
                onSyncFinished();
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
    }, [syncJobId, onSyncFinished]);

    const onSyncLocalSongs = useCallback(async () => {
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
    }, []);

    return {
        syncMessage,
        onSyncLocalSongs,
    };
}
