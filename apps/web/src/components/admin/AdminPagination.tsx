export function AdminPagination({
  page,
  totalPages,
  onChange,
}: {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
}) {
  if (totalPages <= 1) return null;

  return (
    <div className="mt-4 flex items-center justify-center gap-2">
      {Array.from({ length: totalPages }).map((_, i) => (
        <button
          key={i}
          onClick={() => onChange(i + 1)}
          className={`h-8 w-8 rounded text-sm font-medium ${
            page === i + 1 ? "bg-burgundy text-surface" : "text-ink-secondary hover:bg-black/5"
          }`}
        >
          {i + 1}
        </button>
      ))}
    </div>
  );
}
