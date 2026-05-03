type SyncStatusProps = {
    message: string;
};

function SyncStatus({ message }: SyncStatusProps) {
    return <p className="sync-status">{message}</p>;
}

export default SyncStatus;
