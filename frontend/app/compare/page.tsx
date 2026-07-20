"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { RequireAuth } from "@/components/RequireAuth";
import { ScoreGauge } from "@/components/ScoreGauge";
import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ApiError, api } from "@/lib/api";
import { bandVar, formatDate } from "@/lib/bands";
import { useAuth } from "@/lib/auth";
import type { Band, CompareResult } from "@/lib/types";

function CompareInner() {
  const params = useSearchParams();
  const { user } = useAuth();
  const a = params.get("a");
  const b = params.get("b");
  const [data, setData] = useState<CompareResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user || !a || !b) return;
    api
      .compareScans(a, b)
      .then(setData)
      .catch((e) =>
        setError(e instanceof ApiError ? e.message : "Failed to compare."),
      );
  }, [a, b, user]);

  if (!a || !b) {
    return (
      <p className="text-sm text-ink-muted">
        Pick two scans in{" "}
        <Link href="/history" className="text-accent">
          history
        </Link>{" "}
        to compare them.
      </p>
    );
  }
  if (error) return <p className="text-sm text-ink-muted">{error}</p>;
  if (!data) return <p className="text-sm text-ink-muted">Loading comparison…</p>;

  const { diff } = data;
  const worse = diff.score_delta > 0;

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardBody className="flex flex-col items-center gap-6 sm:flex-row sm:justify-center">
          <div className="text-center">
            <ScoreGauge
              score={data.a.result.fusion.score}
              band={data.a.result.fusion.band}
              size={150}
            />
            <p className="m-0 mt-1 text-xs text-ink-muted">
              {formatDate(data.a.created_at)}
            </p>
          </div>

          <div className="flex flex-col items-center gap-1">
            <ArrowRight size={22} className="text-ink-muted" />
            <span
              className="text-sm font-semibold"
              style={{
                color: worse ? bandVar.critical : bandVar.low,
              }}
            >
              {worse ? "+" : ""}
              {diff.score_delta}
            </span>
          </div>

          <div className="text-center">
            <ScoreGauge
              score={data.b.result.fusion.score}
              band={data.b.result.fusion.band}
              size={150}
            />
            <p className="m-0 mt-1 text-xs text-ink-muted">
              {formatDate(data.b.created_at)}
            </p>
          </div>
        </CardBody>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader title="Band change" />
          <CardBody className="flex items-center gap-3">
            <Badge color={bandVar[diff.band_from as Band]}>{diff.band_from}</Badge>
            <ArrowRight size={16} className="text-ink-muted" />
            <Badge color={bandVar[diff.band_to as Band]}>{diff.band_to}</Badge>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Indicator changes" />
          <CardBody className="flex flex-col gap-2 text-sm">
            <div>
              <span className="text-ink-muted">Added: </span>
              {diff.indicators_added.length === 0 ? (
                <span className="text-ink-muted">none</span>
              ) : (
                <span className="mono">{diff.indicators_added.join(", ")}</span>
              )}
            </div>
            <div>
              <span className="text-ink-muted">Removed: </span>
              {diff.indicators_removed.length === 0 ? (
                <span className="text-ink-muted">none</span>
              ) : (
                <span className="mono">{diff.indicators_removed.join(", ")}</span>
              )}
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

export default function ComparePage() {
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-4">
      <h1 className="m-0 text-xl font-semibold tracking-tight">Compare scans</h1>
      <RequireAuth>
        <Suspense fallback={<p className="text-sm text-ink-muted">Loading…</p>}>
          <CompareInner />
        </Suspense>
      </RequireAuth>
    </div>
  );
}
