type PaginationItem = number | "ellipsis-left" | "ellipsis-right";

type PaginationProps = {
    page: number;
    totalPages: number;
    loading: boolean;
    items: PaginationItem[];
    onSetPage: (page: number | ((current: number) => number)) => void;
};

function Pagination({
    page,
    totalPages,
    loading,
    items,
    onSetPage,
}: PaginationProps) {
    return (
        <footer className="pager">
            <button
                className="button subtle"
                type="button"
                disabled={page === 1 || loading}
                onClick={() => onSetPage(1)}
            >
                First
            </button>
            <button
                className="button subtle"
                type="button"
                disabled={page === 1 || loading}
                onClick={() => onSetPage((prev) => Math.max(1, prev - 1))}
            >
                Previous
            </button>
            <div className="page-list" role="navigation" aria-label="Pagination">
                {items.map((item) => {
                    if (typeof item !== "number") {
                        return (
                            <span key={item} className="ellipsis" aria-hidden="true">
                                ...
                            </span>
                        );
                    }

                    return (
                        <button
                            key={item}
                            className={`button subtle page-number ${item === page ? "active-page" : ""}`}
                            type="button"
                            disabled={loading}
                            onClick={() => onSetPage(item)}
                        >
                            {item}
                        </button>
                    );
                })}
            </div>
            <span className="page-label">
                Page {page} of {totalPages}
            </span>
            <button
                className="button subtle"
                type="button"
                disabled={page >= totalPages || loading}
                onClick={() => onSetPage((prev) => Math.min(totalPages, prev + 1))}
            >
                Next
            </button>
            <button
                className="button subtle"
                type="button"
                disabled={page >= totalPages || loading}
                onClick={() => onSetPage(totalPages)}
            >
                Last
            </button>
        </footer>
    );
}

export default Pagination;
