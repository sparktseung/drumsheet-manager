import { Link, useParams } from "react-router-dom";

import { API_BASE_URL } from "../api/client";

export default function SongDetailPage() {
    const { songId } = useParams<{ songId: string }>();

    if (!songId) {
        return (
            <main className="page-shell">
                <p>Missing song id.</p>
                <Link className="plain-link" to="/">
                    Back to songs
                </Link>
            </main>
        );
    }

    const safeBaseUrl = API_BASE_URL.replace(/\/$/, "");
    const drumSheetUrl = `${safeBaseUrl}/files/drum-sheet/${songId}`;
    const audioUrl = `${safeBaseUrl}/files/audio/${songId}`;

    return (
        <main className="page-shell">
            <header className="detail-header">
                <h1>Song Detail</h1>
                <Link className="button subtle" to="/">
                    Back to Song List
                </Link>
            </header>

            <section className="detail-card">
                <p className="detail-note">
                    This route is ready for the upcoming drumsheet playback view.
                </p>
                <p className="detail-id">song_id: {songId}</p>

                <div className="detail-actions">
                    <a className="button" href={drumSheetUrl} target="_blank" rel="noreferrer">
                        Open Drum Sheet PDF
                    </a>
                    <a className="button" href={audioUrl} target="_blank" rel="noreferrer">
                        Open Audio File
                    </a>
                </div>
            </section>
        </main>
    );
}
