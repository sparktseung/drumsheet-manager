import { useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/TextLayer.css";
import "react-pdf/dist/Page/AnnotationLayer.css";

import { API_BASE_URL } from "../api/client";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
    "pdfjs-dist/build/pdf.worker.min.mjs",
    import.meta.url,
).toString();

const BAR_HEIGHT = 56;

export default function SongDetailPage() {
    const { songId } = useParams<{ songId: string }>();
    const audioRef = useRef<HTMLAudioElement>(null);
    const [playing, setPlaying] = useState(false);
    const [numPages, setNumPages] = useState(0);

    if (!songId) {
        return (
            <div className="viewer-shell">
                <p style={{ padding: "2rem", color: "#fff" }}>Missing song id.</p>
            </div>
        );
    }

    const safeBaseUrl = API_BASE_URL.replace(/\/$/, "");
    const drumSheetUrl = `${safeBaseUrl}/files/drum-sheet/${songId}`;
    const audioUrl = `${safeBaseUrl}/files/audio/${songId}`;
    const pageHeight = window.innerHeight - BAR_HEIGHT;

    function onDocumentLoadSuccess({ numPages: n }: { numPages: number }) {
        setNumPages(n);
    }

    function togglePlay() {
        const audio = audioRef.current;
        if (!audio) return;
        if (playing) {
            audio.pause();
            setPlaying(false);
        } else {
            void audio.play();
            setPlaying(true);
        }
    }

    return (
        <div className="viewer-shell">
            <div className="viewer-scroll-area">
                <Document
                    file={drumSheetUrl}
                    onLoadSuccess={onDocumentLoadSuccess}
                    className="viewer-pages-row"
                >
                    {Array.from({ length: numPages }, (_, i) => (
                        <Page
                            key={i + 1}
                            pageNumber={i + 1}
                            height={pageHeight}
                            renderTextLayer={false}
                            renderAnnotationLayer={false}
                        />
                    ))}
                </Document>
            </div>
            <div className="viewer-bar">
                <button
                    className={`button viewer-play-btn ${playing ? "is-playing" : ""}`}
                    type="button"
                    onClick={togglePlay}
                    aria-label={playing ? "Pause" : "Play"}
                >
                    {playing ? "Pause" : "Play"}
                </button>
                <audio
                    ref={audioRef}
                    src={audioUrl}
                    onEnded={() => setPlaying(false)}
                />
            </div>
        </div>
    );
}
