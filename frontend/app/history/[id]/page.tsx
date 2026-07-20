"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/RequireAuth";
import { ScanResultView } from "@/components/ScanResultView";
import { ApiError, api } from "@/lib/api";
import { formatDate } from "@/lib/bands";
import { useAuth } from "@/lib/auth";
import type { ScanRecord } from "@/lib/types";

function Detail({ id }: { id: string }) {
  const { user } = useAuth();
  const [record, setRecord] = useState<ScanRecord | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    api
      .getScan(id)
      .then(setRecord)
      .catch((e) =>
        setError(e instanceof ApiError ? e.message : "Failed to load scan."),
      );
  }, [id, user]);

  if (error) return <p className="text-sm text-ink-muted">{error}</p>;
  if (!record) return <p className="text-sm text-ink-muted">Loading scan…</p>;

  return (
    <div className="flex flex-col gap-4">
      <p className="m-0 text-sm text-ink-muted">
        Scanned {formatDate(record.created_at)}
      </p>
      <ScanResultView result={record.result} />
    </div>
  );
}

export default function ScanDetailPage({ params }: { params: { id: string } }) {
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="m-0 text-xl font-semibold tracking-tight">Scan detail</h1>
        <Link href="/history" className="text-sm text-accent">
          ← Back to history
        </Link>
      </div>
      <RequireAuth>
        <Detail id={params.id} />
      </RequireAuth>
    </div>
  );
}
