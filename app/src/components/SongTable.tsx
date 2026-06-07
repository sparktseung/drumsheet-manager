import type { SongRow, SongViewMode } from "../api/client";

const SKELETON_ROWS = 5;

type SongTableProps = {
    rows: SongRow[];
    loading: boolean;
    mode: SongViewMode;
    showLocal?: boolean;
};

function getMissingStatus(song: SongRow): string {
    const missingAudio = !song.audio_available;
    const missingDrumSheet = !song.drum_sheet_available;

    if (missingAudio && missingDrumSheet) {
        return "Missing Both";
    }

    if (missingAudio) {
        return "Missing Audio";
    }

    if (missingDrumSheet) {
        return "Missing Drumsheet";
    }

    return "Ready";
}

function SkeletonRow() {
    return (
        <tr aria-hidden="true">
            <td><span className="skeleton-box" /></td>
            <td><span className="skeleton-box" /></td>
            <td><span className="skeleton-box" /></td>
            <td><span className="skeleton-box" style={{ width: "4.75rem" }} /></td>
        </tr>
    );
}

function SongTable({ rows, loading, mode, showLocal }: SongTableProps) {
    const artistHeader = showLocal ? "Artist (local)" : "Artist";
    const songHeader = showLocal ? "Song (local)" : "Song";

    return (
        <div className="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th scope="col">Genre</th>
                        <th scope="col">{artistHeader}</th>
                        <th scope="col">{songHeader}</th>
                        <th scope="col" />
                    </tr>
                </thead>
                <tbody>
                    {loading && rows.length === 0 ? (
                        Array.from({ length: SKELETON_ROWS }, (_, i) => (
                            <SkeletonRow key={i} />
                        ))
                    ) : rows.length === 0 ? (
                        <tr>
                            <td colSpan={4} className="muted center">
                                No songs found.
                            </td>
                        </tr>
                    ) : (
                        rows.map((song) => (
                            <tr key={song.song_id}>
                                <td>{song.genre ?? <span className="muted">-</span>}</td>
                                <td>
                                    {showLocal
                                        ? (song.artist_local ?? <span className="muted">-</span>)
                                        : (song.artist_en ?? <span className="muted">-</span>)}
                                </td>
                                <td>
                                    {showLocal
                                        ? (song.song_name_local ?? <span className="muted">-</span>)
                                        : (song.song_name_en ?? <span className="muted">-</span>)}
                                </td>
                                <td className="col-play">
                                    {mode === "playable" ? (
                                        <a
                                            className="button row-action-button"
                                            href={`/songs/${song.song_id}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            Play
                                        </a>
                                    ) : (
                                        <span>{getMissingStatus(song)}</span>
                                    )}
                                </td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
            {loading && rows.length > 0 ? (
                <div className="loading-overlay" aria-label="Updating results" />
            ) : null}
        </div>
    );
}

export default SongTable;
