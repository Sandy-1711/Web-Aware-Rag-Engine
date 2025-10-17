"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DocumentsTable } from "@/components/ui/rag/DocumentsTable";
import { IngestForm } from "@/components/ui/rag/IngestForm";

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Quick Ingest</CardTitle>
        </CardHeader>
        <CardContent>
          <IngestForm compact />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Recent Documents</CardTitle>
        </CardHeader>
        <CardContent>
          <DocumentsTable initialLimit={10} />
        </CardContent>
      </Card>
    </div>
  );
}
