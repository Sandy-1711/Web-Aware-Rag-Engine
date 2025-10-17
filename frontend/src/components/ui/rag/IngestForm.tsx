"use client";

import { useEffect, useRef, useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent } from "@/components/ui/card";
import { CloudUpload, Link2, Loader2 } from "lucide-react";
import { StatusBadge } from "./StatusBadge";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

type JobStatus = { job_id: string; status: "pending" | "processing" | "completed" | "failed"; progress?: number; error?: string; updated_at?: string };

export function IngestForm({ compact = false }: { compact?: boolean }) {
    const [url, setUrl] = useState("");
    const [posting, setPosting] = useState(false);
    const [job, setJob] = useState<JobStatus | null>(null);

    const submit = async () => {
        setPosting(true);
        const r = await fetch(`${API_BASE}/api/v1/ingest-url`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url }),
        });
        setPosting(false);
        if (!r.ok) return;
        const j = await r.json();
        setJob({ job_id: j.job_id, status: "pending" });
    };

    useEffect(() => {
        if (!job?.job_id) return;
        let i: NodeJS.Timeout | null = null;
        const poll = async () => {
            const r = await fetch(`${API_BASE}/api/v1/status/${job.job_id}`);
            if (!r.ok) return;
            const s: JobStatus = await r.json();
            setJob(s);
            if (s.status === "completed" || s.status === "failed") {
                if (i) clearInterval(i);
            }
        };
        poll();
        i = setInterval(poll, 2000);
        return () => { if (i) clearInterval(i); };
    }, [job?.job_id]);

    return (
        <div className="space-y-4">
            <div className="grid gap-3 md:grid-cols-5">
                <div className="md:col-span-4">
                    <div className="relative">
                        <Link2 className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input className="pl-8" placeholder="https://example.com/article" value={url} onChange={(e) => setUrl(e.target.value)} />
                    </div>
                </div>
                <Button className="w-full gap-2" onClick={submit} disabled={!url || posting}>
                    {posting ? <Loader2 className="h-4 w-4 animate-spin" /> : <CloudUpload className="h-4 w-4" />}
                    {posting ? "Submitting" : "Ingest"}
                </Button>
            </div>

            {job && (
                <Card>
                    <CardContent className="p-4 space-y-3">
                        <div className="flex items-center justify-between">
                            <div className="text-sm font-medium">Job</div>
                            <StatusBadge status={job.status} />
                        </div>
                        <Progress value={job.progress ?? (job.status === "completed" ? 100 : job.status === "failed" ? 100 : 50)} />
                        <div className="text-xs text-muted-foreground">
                            {job.updated_at ? new Date(job.updated_at).toLocaleString() : ""}
                        </div>
                        {job.error && <div className="text-sm text-destructive">{job.error}</div>}
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
