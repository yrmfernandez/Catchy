import { AlertTriangle, Bot, Database, Link2, Paperclip, ShieldCheck } from "lucide-react";

import { IndicatorList } from "@/components/IndicatorList";
import { ScoreGauge } from "@/components/ScoreGauge";
import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { bandVar } from "@/lib/bands";
import type { ScanResult } from "@/lib/types";

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4 border-b border-line py-2 last:border-0">
      <span className="text-sm text-ink-muted">{label}</span>
      <span className="mono min-w-0 break-words text-right text-sm">{value}</span>
    </div>
  );
}

function authBadge(value: string | null) {
  if (!value) return <span className="text-ink-muted">—</span>;
  const ok = value === "pass";
  return (
    <Badge color={ok ? bandVar.low : bandVar.critical}>{value}</Badge>
  );
}

export function ScanResultView({ result }: { result: ScanResult }) {
  const { parsed, assessment, ml, intel, analysis, fusion } = result;
  const allIndicators = [...assessment.indicators, ...intel.indicators];

  return (
    <div className="flex flex-col gap-4">
      {/* Verdict */}
      <Card>
        <CardBody className="flex flex-col items-center gap-6 md:flex-row md:items-center">
          <ScoreGauge score={fusion.score} band={fusion.band} />
          <div className="min-w-0 flex-1">
            <p className="m-0 text-base">{fusion.summary}</p>
            {fusion.critical_override ? (
              <p
                className="mt-2 mb-0 flex items-center gap-2 text-sm font-medium"
                style={{ color: bandVar.critical }}
              >
                <AlertTriangle size={16} />
                Critical override — a confirmed-malicious signal set the floor.
              </p>
            ) : null}

            {/* Weighted contributions */}
            <div className="mt-4 flex flex-col gap-2">
              {fusion.components.map((c) => (
                <div key={c.name} className="flex items-center gap-3">
                  <span className="w-20 shrink-0 text-xs uppercase tracking-wide text-ink-muted">
                    {c.name}
                  </span>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-2">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${Math.min(c.score, 100)}%`,
                        background: bandVar[fusion.band],
                        transition: "width 500ms ease",
                      }}
                    />
                  </div>
                  <span className="mono w-24 shrink-0 text-right text-xs text-ink-muted">
                    {c.score} · w{c.weight}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </CardBody>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Indicators */}
        <Card>
          <CardHeader
            title="Security indicators"
            subtitle={`${allIndicators.length} finding(s) — every point is traceable`}
          />
          <CardBody>
            <IndicatorList indicators={allIndicators} />
          </CardBody>
        </Card>

        {/* AI explanation */}
        <Card>
          <CardHeader
            title={
              <span className="flex items-center gap-2">
                <Bot size={16} /> AI analyst
              </span>
            }
            subtitle="Explains the verdict — it never sets it"
          />
          <CardBody>
            {analysis.available ? (
              <div className="flex flex-col gap-3">
                {analysis.summary ? (
                  <p className="m-0 text-sm">{analysis.summary}</p>
                ) : null}
                {analysis.why_suspicious.length > 0 && (
                  <div>
                    <h3 className="m-0 mb-1 text-xs font-semibold uppercase tracking-wide text-ink-muted">
                      Why it&apos;s suspicious
                    </h3>
                    <ul className="m-0 pl-5 text-sm">
                      {analysis.why_suspicious.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {analysis.attack_techniques.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {analysis.attack_techniques.map((t, i) => (
                      <Badge key={i} color="var(--accent)">
                        {t}
                      </Badge>
                    ))}
                  </div>
                )}
                {analysis.recommendations.length > 0 && (
                  <div>
                    <h3 className="m-0 mb-1 text-xs font-semibold uppercase tracking-wide text-ink-muted">
                      Recommendations
                    </h3>
                    <ul className="m-0 pl-5 text-sm">
                      {analysis.recommendations.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <p className="m-0 text-sm text-ink-muted">
                AI explanation unavailable — set <code className="mono">GEMINI_API_KEY</code>{" "}
                to enable it. The verdict above is unaffected: it comes from the
                deterministic and ML layers.
              </p>
            )}
          </CardBody>
        </Card>

        {/* Sender & authentication */}
        <Card>
          <CardHeader
            title={
              <span className="flex items-center gap-2">
                <ShieldCheck size={16} /> Sender &amp; authentication
              </span>
            }
          />
          <CardBody className="py-1">
            <Row label="From" value={parsed.from?.raw ?? "—"} />
            <Row label="Reply-To" value={parsed.reply_to?.raw ?? "—"} />
            <Row
              label="Reply-To mismatch"
              value={
                parsed.reply_to_mismatch ? (
                  <Badge color={bandVar.critical}>yes</Badge>
                ) : (
                  <Badge color={bandVar.low}>no</Badge>
                )
              }
            />
            <Row label="SPF" value={authBadge(parsed.auth.spf)} />
            <Row label="DKIM" value={authBadge(parsed.auth.dkim)} />
            <Row label="DMARC" value={authBadge(parsed.auth.dmarc)} />
          </CardBody>
        </Card>

        {/* ML + intel */}
        <Card>
          <CardHeader
            title={
              <span className="flex items-center gap-2">
                <Database size={16} /> Model &amp; threat intel
              </span>
            }
          />
          <CardBody className="py-1">
            <Row
              label="ML probability"
              value={
                ml.available && ml.probability !== null
                  ? `${(ml.probability * 100).toFixed(1)}% (${ml.label})`
                  : "model unavailable"
              }
            />
            <Row label="Model" value={ml.model_type ?? "—"} />
            <Row
              label="Threat intel"
              value={
                intel.enabled
                  ? intel.providers.map((p) => `${p.name}:${p.status}`).join(", ")
                  : "disabled"
              }
            />
            <Row
              label="Malicious URL hits"
              value={String(intel.url_malicious_hits)}
            />
          </CardBody>
        </Card>

        {/* URLs */}
        <Card>
          <CardHeader
            title={
              <span className="flex items-center gap-2">
                <Link2 size={16} /> Links ({parsed.urls.length})
              </span>
            }
          />
          <CardBody>
            {parsed.urls.length === 0 ? (
              <p className="m-0 text-sm text-ink-muted">No links found.</p>
            ) : (
              <ul className="m-0 flex list-none flex-col gap-2 p-0">
                {parsed.urls.map((u, i) => (
                  <li key={i} className="min-w-0">
                    <div className="mono break-all text-sm">{u.url}</div>
                    <div className="mt-0.5 flex flex-wrap gap-2">
                      {u.is_ip && <Badge color={bandVar.critical}>raw IP</Badge>}
                      {u.anchor_mismatch && (
                        <Badge color={bandVar.critical}>link mismatch</Badge>
                      )}
                      {u.anchor_text && (
                        <span className="text-xs text-ink-muted">
                          shows: {u.anchor_text}
                        </span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>

        {/* Attachments */}
        <Card>
          <CardHeader
            title={
              <span className="flex items-center gap-2">
                <Paperclip size={16} /> Attachments ({parsed.attachments.length})
              </span>
            }
            subtitle="Metadata only — payloads are hashed, never stored"
          />
          <CardBody>
            {parsed.attachments.length === 0 ? (
              <p className="m-0 text-sm text-ink-muted">No attachments.</p>
            ) : (
              <ul className="m-0 flex list-none flex-col gap-2 p-0">
                {parsed.attachments.map((a, i) => (
                  <li key={i}>
                    <div className="mono break-all text-sm">{a.filename}</div>
                    <div className="text-xs text-ink-muted">
                      {a.content_type} · {a.size_bytes} bytes
                    </div>
                    <div className="mono break-all text-xs text-ink-muted">
                      {a.sha256}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
