import type { SongRow } from "../api/client";

type SongTableProps = {
    rows: SongRow[];
    loading: boolean;
    onPlaySong: (songId: string) => void;
};

function SongTable({ rows, loading, onPlaySong }: SongTableProps) {
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
                                <button
                                    className="button row-action-button"
                                    type="button"
                                    onClick={() => onPlaySong(song.song_id)}
                                >
                                    Play
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default SongTable;
