"use client";

import { useEffect, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

type Health = {
  status: string;
  service: string;
  version: string;
  environment: string;
};

// M0 status page: confirms the frontend can reach the backend health endpoint.
// The real dashboard (all seven surfaces) arrives at M8.
export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setHealth)
      .catch((e) => setError(String(e)));
  }, []);

  const online = Boolean(health) && !error;

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "2rem",
      }}
    >
      <section
        style={{
          maxWidth: 460,
          width: "100%",
          background: "var(--surface)",
          border: "1px solid var(--line)",
          borderRadius: 14,
          padding: "2rem",
        }}
      >
        <div
          style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}
        >
          <span style={{ fontSize: 22 }}>🛡️</span>
          <h1 style={{ margin: 0, fontSize: 22, letterSpacing: "-0.02em" }}>
            Catchy
          </h1>
        </div>
        <p style={{ color: "var(--ink-muted)", marginTop: 0 }}>
          Explainable phishing detection — forensics + ML + LLM analyst.
        </p>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            marginTop: 24,
            padding: "12px 14px",
            borderRadius: 10,
            border: "1px solid var(--line)",
          }}
        >
          <span
            style={{
              width: 10,
              height: 10,
              borderRadius: "50%",
              background: online ? "var(--safe)" : "var(--crit)",
              boxShadow: `0 0 0 3px ${online ? "#12271f" : "#33191c"}`,
            }}
          />
          <span className="mono" style={{ fontSize: 13 }}>
            {online
              ? `API online · ${health?.service} v${health?.version} · ${health?.environment}`
              : error
                ? `API unreachable · ${error}`
                : "checking API…"}
          </span>
        </div>

        <p
          className="mono"
          style={{ color: "var(--ink-muted)", fontSize: 12, marginTop: 20 }}
        >
          M0 — Foundation & scaffolding
        </p>
      </section>
    </main>
  );
}
