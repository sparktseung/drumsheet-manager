import { useCallback, useEffect, useRef, useState } from "react";

import {
    fetchStagingFiles,
    insertDiscoveredSong,
    validateDiscovery,
    type DiscoveryInsertRequest,
    type DiscoveryInsertResponse,
    type StagingFile,
} from "../api/client";

interface ConfirmDialog {
    message: string;
    onConfirm: () => void;
    onCancel: () => void;
}

function ConfirmPopup({ message, onConfirm, onCancel }: ConfirmDialog) {
    return (
        <div className="discovery-overlay">
            <div className="discovery-dialog">
                <p>{message}</p>
                <div className="discovery-dialog-buttons">
                    <button
                        className="button"
                        type="button"
                        onClick={onConfirm}
                    >
                        Confirm
                    </button>
                    <button
                        className="button subtle"
                        type="button"
                        onClick={onCancel}
                    >
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    );
}

/** Best-effort parse a file stem into artist/song name parts. */
function parseStem(stem: string): {
    artistEn: string;
    songNameEn: string;
    artistLocal: string;
    songNameLocal: string;
} {
    const parts = stem.split(" - ").map((s) => s.trim()).filter(Boolean);
    if (parts.length >= 4) {
        // Has local names: local_artist - local_song - artist_en - song_name_en
        return {
            artistLocal: parts[0],
            songNameLocal: parts[1],
            artistEn: parts[parts.length - 2],
            songNameEn: parts[parts.length - 1],
        };
    }
    if (parts.length >= 2) {
        // Only two segments — treat as local names (user will fill English).
        return {
            artistLocal: parts[parts.length - 2],
            songNameLocal: parts[parts.length - 1],
            artistEn: "",
            songNameEn: "",
        };
    }
    return { artistEn: "", songNameEn: "", artistLocal: "", songNameLocal: "" };
}

export default function SongDiscovery() {
    const [files, setFiles] = useState<StagingFile[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [validationErrors, setValidationErrors] = useState<string[]>([]);
    const [warnings, setWarnings] = useState<string[]>([]);
    const [inserting, setInserting] = useState(false);

    // Selection
    const [selectedAudio, setSelectedAudio] = useState<StagingFile | null>(null);
    const [selectedDrumSheet, setSelectedDrumSheet] = useState<StagingFile | null>(null);
    const [selectedSource, setSelectedSource] = useState<StagingFile | null>(null);

    // Metadata
    const [artistEn, setArtistEn] = useState("");
    const [songNameEn, setSongNameEn] = useState("");
    const [genre, setGenre] = useState("");
    const [artistLocal, setArtistLocal] = useState("");
    const [songNameLocal, setSongNameLocal] = useState("");

    // Confirmation dialog
    const [confirmDialog, setConfirmDialog] = useState<ConfirmDialog | null>(null);

    // Result
    const [result, setResult] = useState<DiscoveryInsertResponse | null>(null);

    const didLoad = useRef(false);

    const loadFiles = useCallback(async () => {
        setError(null);
        try {
            const stagingFiles = await fetchStagingFiles();
            setFiles(stagingFiles);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load staging files");
        }
    }, []);

    useEffect(() => {
        if (!didLoad.current) {
            didLoad.current = true;
            loadFiles();
        }
    }, [loadFiles]);

    const audioFiles = files.filter((f) => f.file_type === "audio");
    const drumSheetFiles = files.filter((f) => f.file_type === "drum_sheet");
    const sourceFiles = files.filter((f) => f.file_type === "source");

    /** Auto-parse the selected file's stem into metadata fields. */
    function autoParseFromSelection(
        audio: StagingFile | null,
        drumSheet: StagingFile | null,
    ) {
        // Prefer drum sheet name (often more descriptive), fall back to audio.
        const source = drumSheet ?? audio;
        if (!source) return;

        const stem = source.file_name.replace(/\.[^.]+$/, "");
        const parsed = parseStem(stem);

        if (parsed.artistEn) setArtistEn(parsed.artistEn);
        if (parsed.songNameEn) setSongNameEn(parsed.songNameEn);
        if (parsed.artistLocal) setArtistLocal(parsed.artistLocal);
        if (parsed.songNameLocal) setSongNameLocal(parsed.songNameLocal);
    }

    function handleSelectAudio(f: StagingFile | null) {
        setSelectedAudio(f);
        setWarnings([]);
        if (f) autoParseFromSelection(f, selectedDrumSheet);
    }

    function handleSelectDrumSheet(f: StagingFile | null) {
        setSelectedDrumSheet(f);
        setWarnings([]);
        if (f) autoParseFromSelection(selectedAudio, f);
    }

    function normalizedStem(): string {
        const hasLocal = artistLocal.trim() && songNameLocal.trim();
        if (hasLocal) {
            return `${artistLocal.trim()} - ${songNameLocal.trim()} - ${artistEn.trim()} - ${songNameEn.trim()}`;
        }
        return `${artistEn.trim()} - ${songNameEn.trim()}`;
    }

    function canInsert(): boolean {
        return (
            selectedAudio !== null
            && selectedDrumSheet !== null
            && artistEn.trim().length > 0
            && songNameEn.trim().length > 0
        );
    }

    function buildRequest(): DiscoveryInsertRequest {
        return {
            artist_en: artistEn.trim(),
            song_name_en: songNameEn.trim(),
            genre: genre.trim() || null,
            artist_local: artistLocal.trim() || null,
            song_name_local: songNameLocal.trim() || null,
            audio_file_path: selectedAudio?.file_path ?? null,
            drum_sheet_file_path: selectedDrumSheet?.file_path ?? null,
            source_file_path: selectedSource?.file_path ?? null,
        };
    }

    async function handleInsert() {
        setError(null);
        setValidationErrors([]);
        setWarnings([]);

        // Validate first.
        try {
            const validation = await validateDiscovery(buildRequest());
            if (validation.errors.length > 0) {
                setValidationErrors(validation.errors);
                return;
            }
            if (validation.warnings.length > 0) {
                setWarnings(validation.warnings);
                return;
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Validation failed");
            return;
        }

        // Three-step confirmation.
        const req = buildRequest();
        const stem = normalizedStem();
        const displayName = req.artist_local && req.song_name_local
            ? `${req.artist_local} - ${req.song_name_local} (${req.artist_en} - ${req.song_name_en})`
            : `${req.artist_en} - ${req.song_name_en}`;
        setConfirmDialog({
            message: `Insert "${displayName}" into the master spreadsheet?`,
            onConfirm: () => {
                setConfirmDialog(null);
                setConfirmDialog({
                    message: `Rename selected files to "${stem}"?`,
                    onConfirm: () => {
                        setConfirmDialog(null);
                        setConfirmDialog({
                            message: `Move renamed files to the song data folder?`,
                            onConfirm: () => {
                                setConfirmDialog(null);
                                doInsert();
                            },
                            onCancel: () => setConfirmDialog(null),
                        });
                    },
                    onCancel: () => setConfirmDialog(null),
                });
            },
            onCancel: () => setConfirmDialog(null),
        });
    }

    async function doInsert() {
        setInserting(true);
        setError(null);
        setValidationErrors([]);
        try {
            const response = await insertDiscoveredSong(buildRequest());
            setResult(response);
            setArtistEn("");
            setSongNameEn("");
            setGenre("");
            setArtistLocal("");
            setSongNameLocal("");
            setSelectedAudio(null);
            setSelectedDrumSheet(null);
            setSelectedSource(null);
            loadFiles();
        } catch (err) {
            if (err instanceof Error) {
                try {
                    const parsed = JSON.parse(err.message);
                    if (parsed.validation_errors && Array.isArray(parsed.validation_errors)) {
                        setValidationErrors(parsed.validation_errors);
                        return;
                    }
                } catch {
                    // Not JSON.
                }
                setError(err.message);
            } else {
                setError("Insert failed");
            }
        } finally {
            setInserting(false);
        }
    }

    function renderFileList(
        label: string,
        fileList: StagingFile[],
        selected: StagingFile | null,
        onSelect: (f: StagingFile | null) => void,
    ) {
        return (
            <div className="discovery-file-column">
                <h4>{label} ({fileList.length})</h4>
                {fileList.length === 0 ? (
                    <p className="muted">No files</p>
                ) : (
                    <ul className="discovery-file-list">
                        {fileList.map((f) => (
                            <li
                                key={f.file_path}
                                className={
                                    selected?.file_path === f.file_path
                                        ? "selected"
                                        : ""
                                }
                            >
                                <label>
                                    <input
                                        type="radio"
                                        name={label}
                                        checked={selected?.file_path === f.file_path}
                                        onChange={() => onSelect(f)}
                                    />
                                    <span className="discovery-file-name">
                                        {f.file_name}
                                    </span>
                                </label>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        );
    }

    return (
        <section className="panel discovery-panel">
            <div className="panel-header">
                <h2>Song Discovery</h2>
                <div className="button-row">
                    <button
                        className="button subtle"
                        type="button"
                        onClick={loadFiles}
                        disabled={false}
                    >
                        Refresh
                    </button>
                </div>
            </div>

            {error ? <p className="error">{error}</p> : null}

            {validationErrors.length > 0 ? (
                <div className="discovery-validation-errors">
                    <h4>Validation Errors</h4>
                    <ul>
                        {validationErrors.map((msg, i) => (
                            <li key={i}>{msg}</li>
                        ))}
                    </ul>
                </div>
            ) : null}

            {warnings.length > 0 ? (
                <div className="discovery-validation-warnings">
                    <h4>⚠ Duplicate Detected</h4>
                    <ul>
                        {warnings.map((msg, i) => (
                            <li key={i}>{msg}</li>
                        ))}
                    </ul>
                    <p>
                        Edit the song name above to disambiguate
                        (e.g. add "-2"), then click Insert Song again.
                    </p>
                </div>
            ) : null}

            {result ? (
                <div className="discovery-result">
                    <p>
                        ✅ Inserted{" "}
                        <strong>
                            {result.artist_en} - {result.song_name_en}
                        </strong>
                    </p>
                </div>
            ) : null}

            <div className="discovery-layout">
                {/* ── Metadata form ── */}
                <div className="discovery-metadata-section">
                    <div className="discovery-metadata-form">
                        <label>
                            Artist (English) *
                            <input
                                className="search-input"
                                type="text"
                                value={artistEn}
                                onChange={(e) => { setArtistEn(e.target.value); setWarnings([]); }}
                                placeholder="e.g. YOASOBI"
                            />
                        </label>
                        <label>
                            Song Name (English) *
                            <input
                                className="search-input"
                                type="text"
                                value={songNameEn}
                                onChange={(e) => { setSongNameEn(e.target.value); setWarnings([]); }}
                                placeholder="e.g. Idol"
                            />
                        </label>
                        <label>
                            Genre
                            <input
                                className="search-input"
                                type="text"
                                value={genre}
                                onChange={(e) => setGenre(e.target.value)}
                                placeholder="e.g. JPOP"
                            />
                        </label>
                        <label>
                            Artist (Local)
                            <input
                                className="search-input"
                                type="text"
                                value={artistLocal}
                                onChange={(e) => setArtistLocal(e.target.value)}
                                placeholder="e.g. YOASOBI"
                            />
                        </label>
                        <label>
                            Song Name (Local)
                            <input
                                className="search-input"
                                type="text"
                                value={songNameLocal}
                                onChange={(e) => setSongNameLocal(e.target.value)}
                                placeholder="e.g. アイドル"
                            />
                        </label>
                    </div>

                    {/* ── Normalized preview ── */}
                    {artistEn.trim() && songNameEn.trim() ? (
                        <div className="discovery-preview">
                            <h4>Normalized File Names</h4>
                            <ul>
                                {selectedAudio ? (
                                    <li>
                                        🎵 {normalizedStem()}{selectedAudio.extension}
                                    </li>
                                ) : null}
                                {selectedDrumSheet ? (
                                    <li>
                                        📄 {normalizedStem()}{selectedDrumSheet.extension}
                                    </li>
                                ) : null}
                                {selectedSource ? (
                                    <li>
                                        🎼 {normalizedStem()}{selectedSource.extension}
                                    </li>
                                ) : null}
                            </ul>
                        </div>
                    ) : null}
                </div>

                <div className="discovery-actions">
                    <button
                        className="button burnished"
                        type="button"
                        disabled={!canInsert() || inserting}
                        onClick={handleInsert}
                    >
                        {inserting ? "Inserting..." : "Insert Song"}
                    </button>
                </div>

                {/* ── File selection ── */}
                <div className="discovery-files-section">
                    <p className="muted">
                        Select one audio file and one drum sheet file.
                        Optionally select a MuseScore source file.
                    </p>
                    <div className="discovery-file-grid">
                        {renderFileList("Audio", audioFiles, selectedAudio, handleSelectAudio)}
                        {renderFileList("Drum Sheet", drumSheetFiles, selectedDrumSheet, handleSelectDrumSheet)}
                        {renderFileList("Source (.mscz)", sourceFiles, selectedSource, setSelectedSource)}
                    </div>
                </div>
            </div>

            {confirmDialog ? (
                <ConfirmPopup
                    message={confirmDialog.message}
                    onConfirm={confirmDialog.onConfirm}
                    onCancel={confirmDialog.onCancel}
                />
            ) : null}
        </section>
    );
}