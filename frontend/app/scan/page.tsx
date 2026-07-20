"use client";

import { Loader2, Upload } from "lucide-react";
import Link from "next/link";
import { useRef, useState } from "react";

import { ScanResultView } from "@/components/ScanResultView";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ApiError, api, type AnalyzeResponse } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { ScanResult } from "@/lib/types";

// A ready-made phishing sample so the tool can be tried in one click.
const SAMPLE = `From: PayPal Service <service@paypa1-secure.com>
Reply-To: <recover@mailbox-verify.ru>
To: user@example.org
Subject: Urgent: your account has been limited
Authentication-Results: mx.example.org; spf=fail; dkim=none; dmarc=fail
Content-Type: text/html

<html><body><p>We detected unusual activity. Your account has been suspended.
Please verify your identity within 24 hours or lose access.
<a href="http://198.51.100.77/verify-login">https://www.paypal.com/login</a></p></body></html>`;

export default function ScanPage() {
  const { user } = useAuth();
  const [raw, setRaw] = useState("");
  const [result, setResult] = useState<ScanResult | null>(null);
  const [scanId, setScanId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  async function run(fn: () => Promise<AnalyzeResponse>) {
    setLoading(true);
    setError(null);
    try {
      const resp = await fn();
      setResult(resp.result);
      setScanId(resp.scanId);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Unexpected error.");
      setResult(null);
      setScanId(null);
    } finally {
      setLoading(false);
    }
  }

  function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) void run(() => api.analyzeFile(file));
    e.target.value = "";
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-4">
      <div>
        <h1 className="m-0 text-xl font-semibold tracking-tight">Scan an email</h1>
        <p className="mt-1 mb-0 text-sm text-ink-muted">
          Paste a raw email (headers included) or upload an .eml file.
        </p>
      </div>

      <Card>
        <CardHeader
          title="Email source"
          right={
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setRaw(SAMPLE)}
              disabled={loading}
            >
              Load sample
            </Button>
          }
        />
        <CardBody className="flex flex-col gap-3">
          <textarea
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            placeholder="Paste the full raw email here, including headers…"
            spellCheck={false}
            className="mono min-h-[220px] w-full resize-y rounded-[10px] border border-line bg-bg p-3 text-sm text-ink outline-none focus:border-accent"
          />

          <div className="flex flex-wrap items-center gap-2">
            <Button
              onClick={() => void run(() => api.analyzeText(raw))}
              disabled={loading || raw.trim().length === 0}
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : null}
              {loading ? "Analyzing…" : "Analyze"}
            </Button>

            <Button
              variant="secondary"
              onClick={() => fileInput.current?.click()}
              disabled={loading}
            >
              <Upload size={16} />
              Upload .eml
            </Button>
            <input
              ref={fileInput}
              type="file"
              accept=".eml,message/rfc822,text/plain"
              onChange={onFile}
              className="hidden"
            />

            <span className="text-xs text-ink-muted">
              {user ? (
                "Signed in — scans are saved to your history."
              ) : (
                <>
                  Not signed in — this scan won&apos;t be saved.{" "}
                  <Link href="/login" className="text-accent">
                    Sign in
                  </Link>{" "}
                  to keep history.
                </>
              )}
            </span>
          </div>

          {error ? (
            <p
              className="m-0 rounded-[10px] border px-3 py-2 text-sm"
              style={{
                color: "var(--band-critical)",
                borderColor: "var(--band-critical)",
                background: "color-mix(in srgb, var(--band-critical) 10%, transparent)",
              }}
            >
              {error}
            </p>
          ) : null}
        </CardBody>
      </Card>

      {result ? (
        <>
          {scanId ? (
            <p className="m-0 text-xs text-ink-muted">
              Saved to history ·{" "}
              <Link href={`/history/${scanId}`} className="text-accent">
                view record
              </Link>
            </p>
          ) : null}
          <ScanResultView result={result} />
        </>
      ) : null}
    </div>
  );
}
