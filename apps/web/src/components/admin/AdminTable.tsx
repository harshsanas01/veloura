import type { ReactNode } from "react";

export interface AdminTableColumn<T> {
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
}

export function AdminTable<T extends { id: string }>({
  columns,
  rows,
  emptyMessage = "No records found.",
}: {
  columns: AdminTableColumn<T>[];
  rows: T[];
  emptyMessage?: string;
}) {
  if (rows.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border bg-surface py-16 text-center text-sm text-ink-secondary">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-surface">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead>
          <tr className="border-b border-border bg-background/60">
            {columns.map((col) => (
              <th key={col.header} className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-ink-secondary">
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map((row) => (
            <tr key={row.id} className="hover:bg-black/[0.02]">
              {columns.map((col) => (
                <td key={col.header} className={`px-4 py-3 text-ink ${col.className ?? ""}`}>
                  {col.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
