import { FilterSidebar } from "@/components/product/FilterSidebar";
import { Drawer } from "@/components/ui/Drawer";
import type { ProductFilters } from "@/types";

interface MobileFilterDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  filters: ProductFilters;
  onChange: (filters: ProductFilters) => void;
  resultCount?: number;
}

export function MobileFilterDrawer({ isOpen, onClose, filters, onChange, resultCount }: MobileFilterDrawerProps) {
  return (
    <Drawer isOpen={isOpen} onClose={onClose} title="Filters" side="left">
      <div className="p-6">
        <FilterSidebar filters={filters} onChange={onChange} />
      </div>
      <div className="sticky bottom-0 border-t border-border bg-surface p-4">
        <button onClick={onClose} className="btn-primary w-full">
          Show {resultCount ?? ""} Results
        </button>
      </div>
    </Drawer>
  );
}
