type SearchBarProps = {
    searchInput: string;
    onSearchInputChange: (value: string) => void;
    onSearch: () => void;
    onReset: () => void;
    onRandom?: () => void;
    randomDisabled?: boolean;
};

function SearchBar({
    searchInput,
    onSearchInputChange,
    onSearch,
    onReset,
    onRandom,
    randomDisabled,
}: SearchBarProps) {
    return (
        <div className="search-row">
            <input
                className="search-input"
                type="text"
                placeholder="Search genre, artist, or song"
                value={searchInput}
                onChange={(event) => onSearchInputChange(event.target.value)}
                onKeyDown={(event) => {
                    if (event.key === "Enter") {
                        onSearch();
                    }
                }}
            />
            <button className="button" type="button" onClick={onSearch}>
                Search
            </button>
            <button className="button subtle" type="button" onClick={onReset}>
                Reset Search
            </button>
            {onRandom ? (
                <button
                    className="button subtle"
                    type="button"
                    onClick={onRandom}
                    disabled={randomDisabled}
                >
                    {randomDisabled ? "Random..." : "Random"}
                </button>
            ) : null}
        </div>
    );
}

export default SearchBar;
