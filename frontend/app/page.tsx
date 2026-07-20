"use client";

import { Bot, Database, ScanLine, Shield } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { API_BASE, api } from "@/lib/api";
import { bandVar, formatDate } from "@/lib/bands";
import { useAuth } from "@/lib/auth";
import type { ScanSummary } from "@/lib/types";

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <CardBody>
        <div className="text-xs uppercase tracking-wide text-ink-muted">{label}</div>
        <div className="mt-1 text-2xl font-semibold">{value}</div>
      </CardBody>
    </Card>
  );
}

const LAYERS = [
  {
    icon: Shield,
    title: "Email forensics",
    body: "Headers, SPF/DKIM/DMARC, links, and attachment metadata — deterministic and auditable.",
  },
  {
    icon: Database,
    title: "Machine learning",
    body: "A calibrated classifier trained on the same features it scores in production.",
  },
  {
    icon: Bot,
    title: "AI analyst",
    body: "Explains the verdict in plain English. It never decides — it can only escalate.",
  },
];

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const [apiOk, setApiOk] = useState<boolean | null>(null);
  const [scans, setScans] = useState<ScanSummary[]>([]);

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((r) => setApiOk(r.ok))
      .catch(() => setApiOk(false));
  }, []);

  useEffect(() => {
    if (!user) return;
    api.listScans(100).then(setScans).catch(() => setScans([]));
  }, [user]);

  const critical = scans.filter((s) => s.band === "critical").length;
  const avg =
    scans.length > 0
      ? Math.round(scans.reduce((sum, s) => sum + s.score, 0) / scans.length)
      : 0;

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="m-0 text-xl font-semibold tracking-tight">Dashboard</h1>
          <p className="mt-1 mb-0 text-sm text-ink-muted">
            Explainable phishing detection — forensics + ML + LLM analyst.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="h-2.5 w-2.5 rounded-full"
            style={{
              background:
                apiOk === null
                  ? "var(--ink-muted)"
                  : apiOk
                    ? bandVar.low
                    : bandVar.critical,
            }}
            aria-hidden
          />
          <span className="mono text-xs text-ink-muted">
            {apiOk === null ? "checking API…" : apiOk ? "API online" : "API unreachable"}
          </span>
          <Link href="/scan" className="no-underline">
            <Button size="sm">
              <ScanLine size={16} />
              New scan
            </Button>
          </Link>
        </div>
      </div>

      {loading ? null : user ? (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard label="Scans saved" value={scans.length} />
            <StatCard label="Average score" value={avg} />
            <StatCard label="Critical" value={critical} />
          </div>

          <Card>
            <CardHeader
              title="Recent scans"
              right={
                <Link href="/history" className="text-sm text-accent">
                  View all
                </Link>
              }
            />
            <CardBody className="px-0 py-0">
              {scans.length === 0 ? (
                <p className="m-0 px-5 py-6 text-sm text-ink-muted">
                  Nothing yet —{" "}
                  <Link href="/scan" className="text-accent">
                    run your first scan
                  </Link>
                  .
                </p>
              ) : (
                <ul className="m-0 list-none p-0">
                  {scans.slice(0, 5).map((s) => (
                    <li
                      key={s.id}
                      className="flex items-center justify-between gap-3 border-b border-line px-5 py-3 last:border-0"
                    >
                      <div className="min-w-0">
                        <div className="truncate text-sm">
                          {s.subject ?? "(no subject)"}
                        </div>
                        <div className="mono text-xs text-ink-muted">
                          {s.sender_domain ?? "—"} · {formatDate(s.created_at)}
                        </div>
                      </div>
                      <Link href={`/history/${s.id}`} className="no-underline">
                        <Badge color={bandVar[s.band]}>
                          {s.score} · {s.band}
                        </Badge>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </CardBody>
          </Card>
        </>
      ) : (
        <>
          <Card>
            <CardBody className="flex flex-col items-start gap-3">
              <h2 className="m-0 text-base font-semibold">Try it without an account</h2>
              <p className="m-0 text-sm text-ink-muted">
                Scanning is open to everyone. Sign in only if you want your scans
                saved to history.
              </p>
              <div className="flex gap-2">
                <Link href="/scan" className="no-underline">
                  <Button size="sm">
                    <ScanLine size={16} />
                    Scan an email
                  </Button>
                </Link>
                <Link href="/register" className="no-underline">
                  <Button size="sm" variant="secondary">
                    Create account
                  </Button>
                </Link>
              </div>
            </CardBody>
          </Card>

          <div className="grid gap-4 md:grid-cols-3">
            {LAYERS.map(({ icon: Icon, title, body }) => (
              <Card key={title}>
                <CardBody>
                  <Icon size={18} className="text-accent" />
                  <h3 className="m-0 mt-2 text-sm font-semibold">{title}</h3>
                  <p className="m-0 mt-1 text-sm text-ink-muted">{body}</p>
                </CardBody>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
