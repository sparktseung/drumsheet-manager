import { type ChangeEvent, useEffect, useRef, useState } from "react";
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

function formatTime(seconds: number): string {
    if (!Number.isFinite(seconds) || seconds < 0) {
        return "0:00";
    }

    const totalSeconds = Math.floor(seconds);
    const minutes = Math.floor(totalSeconds / 60);
    const remainingSeconds = totalSeconds % 60;
    return `${minutes}:${String(remainingSeconds).padStart(2, "0")}`;
}

export default function SongDetailPage() {
    const { songId } = useParams<{ songId: string }>();
    const audioRef = useRef<HTMLAudioElement>(null);
    const startTimeoutRef = useRef<number | null>(null);
    const countdownIntervalRef = useRef<number | null>(null);
    const [playing, setPlaying] = useState(false);
    const [pendingStart, setPendingStart] = useState(false);
    const [delaySeconds, setDelaySeconds] = useState(5);
    const [countdownSeconds, setCountdownSeconds] = useState<number | null>(null);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [numPages, setNumPages] = useState(0);

    useEffect(() => {
        return () => {
            if (startTimeoutRef.current !== null) {
                window.clearTimeout(startTimeoutRef.current);
            }
            if (countdownIntervalRef.current !== null) {
                window.clearInterval(countdownIntervalRef.current);
            }
        };
    }, []);

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

    function clearPendingStart() {
        if (startTimeoutRef.current !== null) {
            window.clearTimeout(startTimeoutRef.current);
            startTimeoutRef.current = null;
        }
        if (countdownIntervalRef.current !== null) {
            window.clearInterval(countdownIntervalRef.current);
            countdownIntervalRef.current = null;
        }
        setPendingStart(false);
        setCountdownSeconds(null);
    }

    function togglePlay() {
        const audio = audioRef.current;
        if (!audio) return;

        if (pendingStart) {
            clearPendingStart();
            return;
        }

        if (playing) {
            audio.pause();
            setPlaying(false);
            clearPendingStart();
        } else {
            const isAtBeginning = audio.currentTime <= 0.05;
            const shouldDelayStart = delaySeconds > 0 && isAtBeginning;

            if (!shouldDelayStart) {
                void audio.play().catch(() => {
                    setPlaying(false);
                });
                return;
            }

            setPendingStart(true);
            setCountdownSeconds(delaySeconds);
            const startAt = Date.now() + delaySeconds * 1000;

            countdownIntervalRef.current = window.setInterval(() => {
                const nextSeconds = Math.max(0, Math.ceil((startAt - Date.now()) / 1000));
                setCountdownSeconds(nextSeconds);
            }, 100);

            startTimeoutRef.current = window.setTimeout(() => {
                clearPendingStart();
                void audio.play().catch(() => {
                    setPlaying(false);
                });
            }, delaySeconds * 1000);
        }
    }

    function setPlaybackPosition(nextTime: number) {
        const audio = audioRef.current;
        if (!audio) return;

        const safeDuration = Number.isFinite(audio.duration) ? audio.duration : 0;
        const clampedTime = Math.min(Math.max(nextTime, 0), safeDuration);
        audio.currentTime = clampedTime;
        setCurrentTime(clampedTime);
    }

    function skipBy(secondsDelta: number) {
        const audio = audioRef.current;
        if (!audio) return;
        setPlaybackPosition(audio.currentTime + secondsDelta);
    }

    function resetPlayback() {
        const audio = audioRef.current;
        if (!audio) return;

        clearPendingStart();
        audio.pause();
        setPlaying(false);
        setPlaybackPosition(0);
    }

    function onSeek(event: ChangeEvent<HTMLInputElement>) {
        const nextTime = Number(event.target.value);
        setPlaybackPosition(nextTime);
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
                <div className="viewer-bar-side viewer-bar-side-left">
                    <label className="viewer-delay-control" htmlFor="viewer-delay-seconds">
                        <span>Start Song in {delaySeconds}s</span>
                        <input
                            id="viewer-delay-seconds"
                            type="range"
                            min="0"
                            max="10"
                            step="1"
                            value={delaySeconds}
                            onChange={(event) => setDelaySeconds(Number(event.target.value))}
                        />
                    </label>
                </div>
                <div className="viewer-bar-center">
                    <button
                        className={`button viewer-play-btn ${playing ? "is-playing" : ""}`}
                        type="button"
                        onClick={togglePlay}
                        aria-label={playing ? "Pause" : pendingStart ? "Cancel delayed start" : "Play"}
                    >
                        {playing ? "Pause" : pendingStart ? `Start in ${countdownSeconds ?? delaySeconds}s` : "Play"}
                    </button>
                    <button
                        className="button viewer-play-btn viewer-reset-btn"
                        type="button"
                        onClick={resetPlayback}
                    >
                        Reset
                    </button>
                </div>
                <div className="viewer-bar-side viewer-bar-side-right">
                    <div className="viewer-progress-control">
                        <button
                            className="button subtle viewer-seek-btn"
                            type="button"
                            onClick={() => skipBy(-10)}
                            aria-label="Rewind 10 seconds"
                        >
                            -10s
                        </button>
                        <span>{formatTime(currentTime)}</span>
                        <input
                            id="viewer-progress-seconds"
                            type="range"
                            min="0"
                            max={duration || 0}
                            step="0.1"
                            value={Math.min(currentTime, duration || 0)}
                            onChange={onSeek}
                        />
                        <span>{formatTime(duration)}</span>
                        <button
                            className="button subtle viewer-seek-btn"
                            type="button"
                            onClick={() => skipBy(10)}
                            aria-label="Fast-forward 10 seconds"
                        >
                            +10s
                        </button>
                    </div>
                </div>
                <audio
                    ref={audioRef}
                    src={audioUrl}
                    onLoadedMetadata={(event) => {
                        setDuration(event.currentTarget.duration || 0);
                    }}
                    onTimeUpdate={(event) => {
                        setCurrentTime(event.currentTarget.currentTime);
                    }}
                    onPlay={() => setPlaying(true)}
                    onPause={() => setPlaying(false)}
                    onEnded={() => {
                        setPlaying(false);
                        setCurrentTime(0);
                    }}
                />
            </div>
        </div>
    );
}
