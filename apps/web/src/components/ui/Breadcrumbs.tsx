import { ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";

export interface Crumb {
  label: string;
  to?: string;
}

export function Breadcrumbs({ items }: { items: Crumb[] }) {
  return (
    <nav aria-label="Breadcrumb" className="mb-6 flex items-center gap-1.5 text-xs text-ink-secondary">
      {items.map((item, i) => {
        const isLast = i === items.length - 1;
        return (
          <span key={`${item.label}-${i}`} className="flex items-center gap-1.5">
            {item.to && !isLast ? (
              <Link to={item.to} className="hover:text-ink">
                {item.label}
              </Link>
            ) : (
              <span aria-current={isLast ? "page" : undefined} className={isLast ? "text-ink" : ""}>
                {item.label}
              </span>
            )}
            {!isLast && <ChevronRight className="h-3 w-3" />}
          </span>
        );
      })}
    </nav>
  );
}
