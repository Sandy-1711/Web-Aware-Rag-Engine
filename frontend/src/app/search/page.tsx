"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Send, Loader2 } from "lucide-react";
import { ChatBubble } from "@/components/ui/rag/ChatBubble";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:80";

type Msg = { role: "user" | "assistant"; content: string; streaming?: boolean; error?: boolean };

export default function SearchPage() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [provider, setProvider] = useState("default");
  const [topk, setTopk] = useState(5 as number | string);
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement | null>(null);

  const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!canSend) return;

    const userText = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userText }, { role: "assistant", content: "", streaming: true }]);
    setLoading(true);

    try {
      const r = await fetch(`${API_BASE}/api/v1/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userText, top_k: typeof topk === "string" ? Number(topk) : topk, provider }),
      });

      if (!r.ok) {
        let detail = "Failed to query";
        try {
          const j = await r.json();
          if (j?.detail) detail = j.detail;
        } catch {}
        throw new Error(detail);
      }

      const ct = r.headers.get("content-type") || "";
      if (ct.includes("application/json")) {
        const j = await r.json();
        const answer = typeof j?.answer === "string" ? j.answer : JSON.stringify(j);
        setMessages((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          next[next.length - 1] = { ...last, content: answer, streaming: false };
          return next;
        });
      } else {
        const reader = r.body?.getReader();
        const decoder = new TextDecoder();
        if (!reader) throw new Error("No stream");

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            next[next.length - 1] = { ...last, content: (last.content || "") + chunk, streaming: true };
            return next;
          });
        }
        setMessages((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          next[next.length - 1] = { ...last, streaming: false };
          return next;
        });
      }
    } catch (err: any) {
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = { role: "assistant", content: `Error: ${err?.message || "Unknown error"}`, error: true, streaming: false };
        return next;
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ask</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* <div className="grid gap-3 md:grid-cols-4">
          <div className="md:col-span-2">
            <div className="text-sm text-muted-foreground mb-1">Provider</div>
            <Select value={provider} onValueChange={setProvider}>
              <SelectTrigger><SelectValue placeholder="Provider" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="default">Default</SelectItem>
                <SelectItem value="gemini">Gemini</SelectItem>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="anthropic">Anthropic</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <div className="text-sm text-muted-foreground mb-1">Top K</div>
            <Input type="number" min={1} max={50} value={topk} onChange={(e) => setTopk(e.target.value)} />
          </div>
        </div> */}

        <div className="rounded-lg border bg-muted/30 h-[70vh] overflow-y-auto p-4">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center text-sm text-muted-foreground">Ask a question about your documents</div>
          ) : (
            <div className="space-y-4">
              {messages.map((m, i) => (
                <ChatBubble key={i} role={m.role} content={m.content} streaming={m.streaming} error={m.error} />
              ))}
              <div ref={endRef} />
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            placeholder="Ask a question..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <Button type="submit" disabled={!canSend} className="gap-2">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            {loading ? "Sending" : "Send"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
