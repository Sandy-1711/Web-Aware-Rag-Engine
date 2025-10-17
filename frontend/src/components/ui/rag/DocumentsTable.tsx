"use client";

import { useEffect, useMemo, useState } from "react";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "./StatusBadge";
import { Download, Eye, RefreshCw, Search, Trash2 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:80";

type DocStatus = "pending" | "processing" | "completed" | "failed";

type DocItem = {
  id: string;
  title?: string;
  url?: string;
  status?: DocStatus;
  created_at?: string;
  num_chunks?: number;
};

type DocsResponse = {
  total: number;
  page: number;
  limit: number;
  total_pages: number;
  documents: DocItem[];
};

const sortables = [
  { key: "created_at", label: "Created" },
  { key: "title", label: "Title" },
  { key: "status", label: "Status" },
  { key: "chunks", label: "Chunks" },
] as const;

export function DocumentsTable({ initialLimit = 10 }: { initialLimit?: number }) {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<DocStatus | "all">("all");
  const [sortBy, setSortBy] = useState<typeof sortables[number]["key"]>("created_at");
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(initialLimit);
  const [data, setData] = useState<DocsResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const params = useMemo(() => {
    const p = new URLSearchParams();
    p.set("page", String(page));
    p.set("limit", String(limit));
    p.set("sort_by", sortBy);
    p.set("order", order);
    if (status !== "all") p.set("status", status);
    return p.toString();
  }, [page, limit, sortBy, order, status]);

  const load = async () => {
    setLoading(true);
    const r = await fetch(`${API_BASE}/api/v1/documents?${params}`);
    if (r.ok) {
      const j: DocsResponse = await r.json();
      setData(j);
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, [params]);

  const filtered = useMemo(() => {
    if (!data) return [];
    if (!search) return data.documents;
    const q = search.toLowerCase();
    return data.documents.filter((i) => (i.title || i.url || "").toLowerCase().includes(q));
  }, [data, search]);

  const del = async (id: string) => {
    await fetch(`${API_BASE}/api/v1/documents/${id}`, { method: "DELETE" });
    load();
  };

  return (
    <div className="space-y-4">
      <div className="grid gap-2 md:grid-cols-4">
        <div className="md:col-span-2 flex items-center gap-2">
          <div className="relative w-full">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input placeholder="Search title or URL" className="pl-8" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <Button variant="outline" className="gap-2" onClick={load}>
            <RefreshCw className="h-4 w-4" /> Refresh
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Select value={status} onValueChange={(v) => { setPage(1); setStatus(v as any); }}>
            <SelectTrigger className="w-full"><SelectValue placeholder="All statuses" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="processing">Processing</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
            </SelectContent>
          </Select>
          <Select value={sortBy} onValueChange={(v) => setSortBy(v as any)}>
            <SelectTrigger className="w-full"><SelectValue placeholder="Sort by" /></SelectTrigger>
            <SelectContent>
              {sortables.map((s) => <SelectItem key={s.key} value={s.key}>{s.label}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={order} onValueChange={(v) => setOrder(v as "asc" | "desc")}>
            <SelectTrigger className="w-full"><SelectValue placeholder="Order" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="asc">Asc</SelectItem>
              <SelectItem value="desc">Desc</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="overflow-x-auto rounded-md border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Title</th>
              <th className="px-4 py-3 text-left font-medium">Status</th>
              <th className="px-4 py-3 text-left font-medium">Created</th>
              <th className="px-4 py-3 text-right font-medium">Chunks</th>
              <th className="px-4 py-3 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={5} className="px-4 py-6 text-center text-muted-foreground">Loading</td></tr>
            )}
            {!loading && filtered?.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-6 text-center text-muted-foreground">No results</td></tr>
            )}
            {filtered?.map((d) => (
              <tr key={d.id} className="border-t">
                <td className="px-4 py-3 align-top">
                  <div className="font-medium break-all">{d.title || d.url || d.id}</div>
                  {d.url && <div className="text-xs text-muted-foreground break-all">{d.url}</div>}
                </td>
                <td className="px-4 py-3 align-top"><StatusBadge status={d.status || "pending"} /></td>
                <td className="px-4 py-3 align-top">{d.created_at ? new Date(d.created_at).toLocaleString() : "-"}</td>
                <td className="px-4 py-3 align-top text-right">{d.num_chunks ?? "-"}</td>
                <td className="px-4 py-3 align-top">
                  <div className="flex justify-end gap-2">
                    <a href={`/documents/${d.id}`}><Button size="sm" className="gap-2"><Eye className="h-4 w-4" /> Details</Button></a>
                    <Button variant="outline" size="sm" className="gap-2" onClick={() => window.open(d.url || "#", "_blank")}>
                      <Download className="h-4 w-4" /> Open
                    </Button>
                    <Button variant="destructive" size="sm" className="gap-2" onClick={() => del(d.id)}>
                      <Trash2 className="h-4 w-4" /> Delete
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
          {data && data.total_pages > 1 && (
            <tfoot>
              <tr>
                <td colSpan={5} className="px-4 py-3">
                  <div className="flex items-center justify-between">
                    <div className="text-xs text-muted-foreground">Page {data.page} of {data.total_pages} • {data.total} items</div>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm" disabled={data.page <= 1} onClick={() => setPage(p => Math.max(1, p - 1))}>Prev</Button>
                      <Button variant="outline" size="sm" disabled={data.page >= data.total_pages} onClick={() => setPage(p => Math.min(data.total_pages, p + 1))}>Next</Button>
                      <Select value={String(limit)} onValueChange={(v) => { setPage(1); setLimit(Number(v)); }}>
                        <SelectTrigger className="w-24"><SelectValue placeholder="Page size" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="5">5</SelectItem>
                          <SelectItem value="10">10</SelectItem>
                          <SelectItem value="20">20</SelectItem>
                          <SelectItem value="50">50</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </td>
              </tr>
            </tfoot>
          )}
        </table>
      </div>
    </div>
  );
}
