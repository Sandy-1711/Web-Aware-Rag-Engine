"use client";

import { Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";

export function ChatBubble({ role, content, streaming, error }: { role: "user" | "assistant"; content: string; streaming?: boolean; error?: boolean }) {
    const isUser = role === "user";
    return (
        <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
            <div className={cn("flex gap-3 max-w-[85%]", isUser ? "flex-row-reverse" : "flex-row")}>
                <div className={cn("flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center", isUser ? "bg-primary text-primary-foreground" : "bg-muted text-primary")}>
                    {isUser ? <User className="h-5 w-5" /> : <Bot className="h-5 w-5" />}
                </div>
                <div
                    className={cn(
                        "rounded-2xl px-4 py-3 text-sm border",
                        isUser ? "bg-primary text-primary-foreground border-primary" : error ? "bg-destructive/10 text-destructive border-destructive" : "bg-background text-foreground border-border"
                    )}
                >
                    <div className="whitespace-pre-wrap break-words">
                        {content}
                        {streaming && <span className="inline-block w-2 h-4 bg-primary ml-1 animate-pulse align-middle" />}
                    </div>
                </div>
            </div>
        </div>
    );
}
