"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/RequireAuth";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ApiError, api } from "@/lib/api";
import { bandVar, formatDate } from "@/lib/bands";
import { useAuth } from "@/lib/auth";
import type { ScanSummary } from "@/lib/types";

function HistoryTable() {
  const router = useRouter();
  const { user } = useAuth();
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    api
      .listScans()
      .then(setScans)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load."))
      .finally(() => setLoading(false));
  }, [user]);

  function toggle(id: string) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id].slice(-2),
    );
  }

  if (loading) return <p className="text-sm text-ink-muted">Loading history…</p>;
  if (error) return <p className="text-sm text-ink-muted">{error}</p>;

  return (
    <Card>
      <CardHeader
        title="Your scans"
        subtitle={`${scans.length} saved · select two to compare`}
        right={
          <Button
            size="sm"
            disabled={selected.length !== 2}
            onClick={() =>
              router.push(`/compare?a=${selected[0]}&b=${selected[1]}`)
            }
          >
            Compare
          </Button>
        }
      />
      <CardBody className="px-0 py-0">
        {scans.length === 0 ? (
          <p className="m-0 px-5 py-6 text-sm text-ink-muted">
            No scans yet.{" "}
            <Link href="/scan" className="text-accent">
              Run your first scan
            </Link>
            .
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-ink-muted">
                  <th className="px-5 py-2 font-medium" />
                  <th className="px-3 py-2 font-medium">Date</th>
                  <th className="px-3 py-2 font-medium">Subject</th>
                  <th className="px-3 py-2 font-medium">Sender</th>
                  <th className="px-3 py-2 font-medium">Score</th>
                  <th className="px-5 py-2 font-medium" />
                </tr>
              </thead>
              <tbody>
                {scans.map((s) => (
                  <tr key={s.id} className="border-b border-line last:border-0">
                    <td className="px-5 py-3">
                      <input
                        type="checkbox"
                        checked={selected.includes(s.id)}
                        onChange={() => toggle(s.id)}
                        aria-label={`Select scan ${s.id}`}
                      />
                    </td>
                    <td className="whitespace-nowrap px-3 py-3 text-ink-muted">
                      {formatDate(s.created_at)}
                    </td>
                    <td className="max-w-[22ch] truncate px-3 py-3">
                      {s.subject ?? "(no subject)"}
                    </td>
                    <td className="mono max-w-[18ch] truncate px-3 py-3 text-ink-muted">
                      {s.sender_domain ?? "—"}
                    </td>
                    <td className="px-3 py-3">
                      <Badge color={bandVar[s.band]}>
                        {s.score} · {s.band}
                      </Badge>
                    </td>
                    <td className="px-5 py-3 text-right">
                      <Link href={`/history/${s.id}`} className="text-accent">
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardBody>
    </Card>
  );
}

export default function HistoryPage() {
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-4">
      <h1 className="m-0 text-xl font-semibold tracking-tight">Scan history</h1>
      <RequireAuth>
        <HistoryTable />
      </RequireAuth>
    </div>
  );
}
