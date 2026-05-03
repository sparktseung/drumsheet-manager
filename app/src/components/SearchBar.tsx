type SearchBarProps = {
    searchInput: string;
    onSearchInputChange: (value: string) => void;
    onSearch: () => void;
    onReset: () => void;
};

function SearchBar({
    searchInput,
    onSearchInputChange,
    onSearch,
    onReset,
}: SearchBarProps) {
    return (
        <div className="search-row">
            <input
                className="search-input"
                type="text"
                placeholder="Search genre, artist, or song"
                value={searchInput}
                onChange={(event) => onSearchInputChange(event.target.value)}
            />
            <button className="button" type="button" onClick={onSearch}>
                Search
            </button>
            <button className="button subtle" type="button" onClick={onReset}>
                Reset Search
            </button>
        </div>
    );
}

export default SearchBar;
