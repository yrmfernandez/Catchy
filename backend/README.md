---
title: Catchy API
emoji: 🛡️
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 8000
pinned: false
---

# Catchy — Backend API

FastAPI service for [Catchy](https://github.com/yrmfernandez/Catchy): explainable
phishing detection (email forensics + ML + an LLM analyst). This Space runs the
container defined by [`Dockerfile`](./Dockerfile) and exposes the API on
`/api/v1` (interactive docs at `/docs`).

The frontend (Next.js) is deployed separately on Vercel and points at this
Space via `NEXT_PUBLIC_API_BASE_URL`.

## Runtime configuration

Set these in **Settings → Variables and secrets** (secrets for anything
sensitive):

| Name | Required | Purpose |
| --- | --- | --- |
| `ENVIRONMENT` | yes | Set to `production` (enables prod CORS + HSTS). |
| `CORS_ORIGINS` | yes | The Vercel frontend origin, e.g. `https://catchy.vercel.app` (scheme+host, no trailing slash; comma-separate multiples). |
| `GEMINI_API_KEY` | optional | Enables the LLM explanation layer. Without it, scanning still returns a verdict. |
| `JWT_SECRET` | optional | Needed only if you wire a database for accounts/history. |

The service **degrades gracefully**: with no database, no Redis, and no ML model
bundle, anonymous scanning (forensics + rule engine + optional LLM) still works —
which is exactly the free-tier setup here. Add a managed Postgres (e.g. Neon) and
`POSTGRES_*` vars later if you want accounts and saved history.
