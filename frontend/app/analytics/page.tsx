"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { RequireAuth } from "@/components/RequireAuth";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { bandVar } from "@/lib/bands";
import { useAuth } from "@/lib/auth";
import type { Band, ScanSummary } from "@/lib/types";

const BANDS: Band[] = ["low", "medium", "high", "critical"];

function Charts() {
  const { user } = useAuth();
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    api
      .listScans(200)
      .then(setScans)
      .catch(() => setScans([]))
      .finally(() => setLoading(false));
  }, [user]);

  if (loading) return <p className="text-sm text-ink-muted">Loading analytics…</p>;
  if (scans.length === 0) {
    return <p className="text-sm text-ink-muted">No scans yet — nothing to chart.</p>;
  }

  // Oldest -> newest so the trend reads left to right.
  const trend = [...scans]
    .reverse()
    .map((s, i) => ({ n: i + 1, score: s.score }));

  const distribution = BANDS.map((band) => ({
    band,
    count: scans.filter((s) => s.band === band).length,
  }));

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader title="Score over time" subtitle="Fused risk score per scan" />
        <CardBody>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend} margin={{ top: 5, right: 10, bottom: 5, left: -20 }}>
                <CartesianGrid stroke="var(--line)" strokeDasharray="3 3" />
                <XAxis dataKey="n" stroke="var(--ink-muted)" fontSize={12} />
                <YAxis domain={[0, 100]} stroke="var(--ink-muted)" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    background: "var(--surface)",
                    border: "1px solid var(--line)",
                    borderRadius: 10,
                    color: "var(--ink)",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="var(--accent)"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Risk distribution" subtitle="Scans per band" />
        <CardBody>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={distribution}
                margin={{ top: 5, right: 10, bottom: 5, left: -20 }}
              >
                <CartesianGrid stroke="var(--line)" strokeDasharray="3 3" />
                <XAxis dataKey="band" stroke="var(--ink-muted)" fontSize={12} />
                <YAxis allowDecimals={false} stroke="var(--ink-muted)" fontSize={12} />
                <Tooltip
                  cursor={{ fill: "var(--surface-2)" }}
                  contentStyle={{
                    background: "var(--surface)",
                    border: "1px solid var(--line)",
                    borderRadius: 10,
                    color: "var(--ink)",
                  }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {distribution.map((d) => (
                    <Cell key={d.band} fill={bandVar[d.band]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-4">
      <h1 className="m-0 text-xl font-semibold tracking-tight">Analytics</h1>
      <RequireAuth>
        <Charts />
      </RequireAuth>
    </div>
  );
}
