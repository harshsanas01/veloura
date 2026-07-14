import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";

import { useToastStore } from "@/store/toastStore";

const iconMap = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
};

const colorMap = {
  success: "border-success/30 text-success",
  error: "border-error/30 text-error",
  info: "border-border text-ink",
};

export function Toaster() {
  const toasts = useToastStore((s) => s.toasts);
  const dismiss = useToastStore((s) => s.dismiss);

  return (
    <div className="pointer-events-none fixed bottom-5 right-5 z-[100] flex flex-col gap-2">
      <AnimatePresence>
        {toasts.map((toast) => {
          const Icon = iconMap[toast.variant];
          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 12, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              className={`pointer-events-auto flex items-center gap-2 rounded-lg border bg-surface px-4 py-3 text-sm shadow-elevated ${colorMap[toast.variant]}`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="text-ink">{toast.message}</span>
              <button onClick={() => dismiss(toast.id)} aria-label="Dismiss" className="ml-2 text-ink-secondary hover:text-ink">
                <X className="h-3.5 w-3.5" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
