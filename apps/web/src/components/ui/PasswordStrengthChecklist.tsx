import { Check, X } from "lucide-react";

import { PASSWORD_RULES } from "@/schemas/auth";
import { cn } from "@/utils/cn";

export function PasswordStrengthChecklist({ password }: { password: string }) {
  return (
    <ul className="grid grid-cols-1 gap-1 text-xs sm:grid-cols-2" aria-live="polite">
      {PASSWORD_RULES.map((rule) => {
        const met = rule.test(password);
        return (
          <li
            key={rule.key}
            className={cn(
              "flex items-center gap-1.5 transition-colors",
              met ? "text-green-700" : "text-ink-secondary",
            )}
          >
            {met ? (
              <Check className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            ) : (
              <X className="h-3.5 w-3.5 shrink-0 opacity-40" aria-hidden="true" />
            )}
            {rule.label}
          </li>
        );
      })}
    </ul>
  );
}
