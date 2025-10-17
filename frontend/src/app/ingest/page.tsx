"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { IngestForm } from "@/components/ui/rag/IngestForm";

export default function IngestPage() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Ingest URL</CardTitle>
      </CardHeader>
      <CardContent>
        <IngestForm />
      </CardContent>
    </Card>
  );
}
