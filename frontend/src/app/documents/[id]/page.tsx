"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ArrowLeft, RefreshCw, Trash2 } from "lucide-react";
import { StatusBadge } from "@/components/ui/rag/StatusBadge";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:80";

type DocStatus = "pending" | "processing" | "completed" | "failed";

type Doc = {
    id: string;
    title?: string;
    url?: string;
    created_at?: string;
    status?: DocStatus;
    num_chunks?: number;
    // preview?: string;
    error_message?: string;
};

export default function DocDetailsPage() {
    const { id } = useParams<{ id: string }>();
    const router = useRouter();
    const [doc, setDoc] = useState<Doc | null>(null);
    const [loading, setLoading] = useState(true);

    const load = async () => {
        const r = await fetch(`${API_BASE}/api/v1/documents/${id}`);
        if (r.ok) {
            const j = await r.json();
            setDoc(j);
        }
        setLoading(false);
    };

    useEffect(() => {
        load();
        const i = setInterval(load, 2000);
        return () => clearInterval(i);
    }, [id]);

    const del = async () => {
        await fetch(`${API_BASE}/api/v1/documents/${id}`, { method: "DELETE" });
        router.push("/documents");
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <Button variant="ghost" onClick={() => router.back()} className="gap-2">
                    <ArrowLeft className="h-4 w-4" /> Back
                </Button>
                <div className="flex items-center gap-2">
                    <Button variant="outline" onClick={() => router.refresh()} className="gap-2">
                        <RefreshCw className="h-4 w-4" /> Refresh
                    </Button>
                    <Button variant="destructive" className="gap-2" onClick={del}>
                        <Trash2 className="h-4 w-4" /> Delete
                    </Button>
                </div>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Document</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                    {doc?.status && <StatusBadge status={doc.status} />}
                    <div className="grid gap-6 md:grid-cols-2">
                        <Field label="Title" value={doc?.title || "-"} />
                        <Field label="URL" value={doc?.url || "-"} mono />
                        <Field label="Created" value={doc?.created_at ? new Date(doc.created_at).toLocaleString() : "-"} />
                        <Field label="Chunks" value={String(doc?.num_chunks ?? "-")} />
                        {doc?.error_message && <Field label="Error" value={doc.error_message} />}
                    </div>
                    {/* {doc?.preview && (
                        <div className="space-y-2">
                            <div className="text-sm text-muted-foreground">Preview</div>
                            <pre className="rounded-md border bg-muted/30 p-3 text-xs whitespace-pre-wrap">{doc.preview}</pre>
                        </div>
                    )} */}
                    {/* {doc?.meta && Object.keys(doc.meta).length > 0 && (
                        <div className="space-y-2">
                            <div className="text-sm text-muted-foreground">Metadata</div>
                            <KV obj={doc.meta} />
                        </div>
                    )} */}
                    {loading && <Progress value={60} />}
                </CardContent>
            </Card>
        </div>
    );
}

function Field({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
    return (
        <div className="space-y-1.5">
            <div className="text-sm text-muted-foreground">{label}</div>
            <div className={["text-sm font-medium break-words", mono ? "font-mono" : ""].join(" ")}>{value}</div>
        </div>
    );
}

function KV({ obj }: { obj: Record<string, any> }) {
    const entries = Object.entries(obj).filter(([, v]) => v !== undefined && v !== null && v !== "");
    if (!entries.length) return <div className="text-sm text-muted-foreground">No data</div>;
    return (
        <dl className="grid gap-3">
            {entries.map(([k, v]) => (
                <div key={k} className="grid grid-cols-3 gap-2">
                    <dt className="col-span-1 text-sm text-muted-foreground">{labelize(k)}</dt>
                    <dd className="col-span-2 text-sm break-words">{renderVal(v)}</dd>
                </div>
            ))}
        </dl>
    );
}

function labelize(s: string) {
    return s.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}
function renderVal(v: any) {
    if (typeof v === "boolean") return v ? "Yes" : "No";
    if (Array.isArray(v)) return v.join(", ");
    if (typeof v === "object") return JSON.stringify(v);
    return String(v);
}
