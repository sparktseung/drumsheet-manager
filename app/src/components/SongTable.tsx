import type { SongRow, SongViewMode } from "../api/client";

type SongTableProps = {
    rows: SongRow[];
    loading: boolean;
    mode: SongViewMode;
    onPlaySong: (songId: string) => void;
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

function SongTable({ rows, loading, mode, onPlaySong }: SongTableProps) {
    return (
        <div className="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>genre</th>
                        <th>artist</th>
                        <th>song name</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    {!loading && rows.length === 0 ? (
                        <tr>
                            <td colSpan={4} className="muted center">
                                No songs found.
                            </td>
                        </tr>
                    ) : null}

                    {rows.map((song) => (
                        <tr key={song.song_id}>
                            <td>{song.genre ?? <span className="muted">-</span>}</td>
                            <td>{song.artist_local ?? <span className="muted">-</span>}</td>
                            <td>{song.song_name_local ?? <span className="muted">-</span>}</td>
                            <td className="col-play">
                                {mode === "playable" ? (
                                    <button
                                        className="button row-action-button"
                                        type="button"
                                        onClick={() => onPlaySong(song.song_id)}
                                    >
                                        Play
                                    </button>
                                ) : (
                                    <span>{getMissingStatus(song)}</span>
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default SongTable;
