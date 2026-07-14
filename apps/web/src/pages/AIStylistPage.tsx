import { Sparkles } from "lucide-react";
import { useRef, useState } from "react";

import { ChatMessage } from "@/components/ai/ChatMessage";
import { useStylistRecommend } from "@/hooks/useAIStylist";
import { getApiErrorMessage } from "@/services/apiClient";
import type { StylistOutfit } from "@/types";

const EXAMPLE_PROMPTS = [
  "I am going to a pool party. Suggest an outfit under $150.",
  "I am going on a late-night date. Suggest an all-black outfit.",
  "Suggest a casual summer outfit using blue and white.",
  "I need a business-casual outfit for an office event.",
];

interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  outfits?: StylistOutfit[];
  followUps?: string[];
}

export function AIStylistPage() {
  const [messages, setMessages] = useState<DisplayMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hi, I'm your Veloura AI stylist. Tell me the occasion, mood, colors, or budget, and I'll build a complete look from pieces in our collection.",
    },
  ]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const scrollRef = useRef<HTMLDivElement>(null);
  const recommend = useStylistRecommend();

  function scrollToBottom() {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
    });
  }

  function sendMessage(message: string) {
    if (!message.trim() || recommend.isPending) return;

    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", content: message }]);
    setInput("");
    scrollToBottom();

    recommend.mutate(
      { message, sessionId },
      {
        onSuccess: (data) => {
          setSessionId(data.session_id);
          setMessages((prev) => [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content: data.summary,
              outfits: data.outfits,
              followUps: data.follow_up_suggestions,
            },
          ]);
          scrollToBottom();
        },
        onError: (error) => {
          setMessages((prev) => [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content: getApiErrorMessage(error, "I couldn't put together a look just now. Please try again."),
            },
          ]);
          scrollToBottom();
        },
      },
    );
  }

  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");

  return (
    <div className="container-veloura flex flex-col py-8">
      <div className="mb-6 flex items-center gap-2.5">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-burgundy/10">
          <Sparkles className="h-5 w-5 text-burgundy" />
        </div>
        <div>
          <h1 className="font-display text-2xl text-ink">AI Stylist</h1>
          <p className="text-xs text-ink-secondary">Outfits built only from pieces in our live collection</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_260px]">
        <div className="flex h-[70vh] flex-col rounded-lg border border-border bg-surface shadow-card">
          <div ref={scrollRef} className="flex-1 space-y-6 overflow-y-auto p-5">
            {messages.map((m) => (
              <ChatMessage key={m.id} role={m.role} content={m.content} outfits={m.outfits} />
            ))}
            {recommend.isPending && (
              <div className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-burgundy text-surface">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div className="flex items-center gap-1.5 rounded-lg bg-rose/30 px-4 py-3">
                  {[0, 1, 2].map((i) => (
                    <span
                      key={i}
                      className="h-1.5 w-1.5 animate-pulse rounded-full bg-burgundy"
                      style={{ animationDelay: `${i * 150}ms` }}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          {lastAssistant?.followUps && lastAssistant.followUps.length > 0 && !recommend.isPending && (
            <div className="flex flex-wrap gap-2 border-t border-border px-5 py-3">
              {lastAssistant.followUps.map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => sendMessage(suggestion)}
                  className="rounded-full border border-burgundy/30 px-3 py-1.5 text-xs font-medium text-burgundy hover:bg-rose/30"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}

          <form
            onSubmit={(e) => {
              e.preventDefault();
              sendMessage(input);
            }}
            className="flex items-center gap-3 border-t border-border p-4"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Describe the occasion, mood, colors, and budget..."
              className="input-veloura flex-1"
            />
            <button type="submit" className="btn-primary" disabled={recommend.isPending}>
              Send
            </button>
          </form>
        </div>

        <aside className="flex flex-col gap-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-ink-secondary">Try asking</span>
          {EXAMPLE_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              onClick={() => sendMessage(prompt)}
              className="rounded-lg border border-border bg-surface p-3.5 text-left text-sm text-ink-secondary transition-colors hover:border-burgundy hover:text-ink"
            >
              {prompt}
            </button>
          ))}
        </aside>
      </div>
    </div>
  );
}
