import { Sparkles, User } from "lucide-react";

import { OutfitCard } from "@/components/ai/OutfitCard";
import type { StylistOutfit } from "@/types";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  outfits?: StylistOutfit[];
}

export function ChatMessage({ role, content, outfits }: ChatMessageProps) {
  const isUser = role === "user";
  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          isUser ? "bg-ink text-surface" : "bg-burgundy text-surface"
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
      </div>
      <div className={`flex max-w-[85%] flex-col gap-4 ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`rounded-lg px-4 py-3 text-sm leading-relaxed ${
            isUser ? "bg-ink text-surface" : "bg-rose/30 text-ink"
          }`}
        >
          {content}
        </div>
        {outfits && outfits.length > 0 && (
          <div className="flex w-full flex-col gap-4">
            {outfits.map((outfit, i) => (
              <OutfitCard key={outfit.id ?? i} outfit={outfit} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
