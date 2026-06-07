type SearchBarProps = {
    searchInput: string;
    onSearchInputChange: (value: string) => void;
    onReset: () => void;
    onRandom?: () => void;
    randomDisabled?: boolean;
};

function SearchBar({
    searchInput,
    onSearchInputChange,
    onReset,
    onRandom,
    randomDisabled,
}: SearchBarProps) {
    return (
        <div className="search-row">
            <input
                className="search-input"
                type="text"
                placeholder="Search artist or song name (local/english)"
                value={searchInput}
                onChange={(event) => onSearchInputChange(event.target.value)}
            />
            <button className="button subtle" type="button" onClick={onReset}>
                Reset Search
            </button>
            {onRandom ? (
                <button
                    className="button burnished"
                    type="button"
                    onClick={onRandom}
                    disabled={randomDisabled}
                >
                    {randomDisabled ? "Loading..." : "Random Play"}
                </button>
            ) : null}
        </div>
    );
}

export default SearchBar;
