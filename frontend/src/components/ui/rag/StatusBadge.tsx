"use client";

import { Badge } from "@/components/ui/badge";

export function StatusBadge({ status }: { status: "pending" | "processing" | "completed" | "failed" }) {
    if (status === "completed") return <Badge className="bg-emerald-600 hover:bg-emerald-600">Completed</Badge>;
    if (status === "processing") return <Badge className="bg-amber-600 hover:bg-amber-600">Processing</Badge>;
    if (status === "failed") return <Badge variant="destructive">Failed</Badge>;
    return <Badge variant="secondary">Pending</Badge>;
}
