import { ChevronDown } from "lucide-react";
import { useState } from "react";

export interface AccordionSection {
  title: string;
  content: React.ReactNode;
}

export function Accordion({ sections, defaultOpen = 0 }: { sections: AccordionSection[]; defaultOpen?: number | null }) {
  const [openIndex, setOpenIndex] = useState<number | null>(defaultOpen);

  return (
    <div className="divide-y divide-border border-t border-border">
      {sections.map((section, i) => {
        const isOpen = openIndex === i;
        return (
          <div key={section.title}>
            <button
              type="button"
              onClick={() => setOpenIndex(isOpen ? null : i)}
              aria-expanded={isOpen}
              className="flex w-full items-center justify-between py-4 text-left text-sm font-medium text-ink"
            >
              {section.title}
              <ChevronDown className={`h-4 w-4 shrink-0 text-ink-secondary transition-transform ${isOpen ? "rotate-180" : ""}`} />
            </button>
            {isOpen && <div className="pb-4 text-sm leading-relaxed text-ink-secondary">{section.content}</div>}
          </div>
        );
      })}
    </div>
  );
}
