// @ts-ignore
import "@/app/globals.css";
import { ReactNode } from "react";

export const metadata = {
  title: "RAG Engine Console",
  description: "Web-aware RAG Engine",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-dvh bg-background text-foreground antialiased">
        <div className="mx-auto max-w-6xl px-4">
          <header className="sticky top-0 z-40 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="flex items-center justify-between py-4">
              <a href="/" className="text-xl font-semibold">RAG Engine</a>
              <nav className="flex items-center gap-3 text-sm">
                <a href="/" className="hover:underline">Dashboard</a>
                <a href="/ingest" className="hover:underline">Ingest</a>
                <a href="/documents" className="hover:underline">Documents</a>
                <a href="/search" className="hover:underline">Search</a>
              </nav>
            </div>
          </header>
          <main className="py-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
