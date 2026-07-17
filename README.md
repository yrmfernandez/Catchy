# 🛡️ PhishGuard AI

> Layered phishing-detection platform that fuses deterministic email forensics, a calibrated ML classifier, and an LLM analyst into a single **explainable** 0–100 risk score.

**Core principle:** the LLM never decides the verdict — deterministic forensics and a trained model produce the score; the LLM only *explains* it. This keeps the system testable, injection-resistant, and auditable.

📐 **[Full architecture design document →](docs/architecture.md)**

---

## Stack

| Tier      | Technology                                               |
| --------- | -------------------------------------------------------- |
| Frontend  | Next.js · React · TypeScript · Tailwind · shadcn/ui      |
| Backend   | FastAPI · Python 3.12 · Celery                           |
| Data      | PostgreSQL · Redis (cache + broker)                      |
| ML        | scikit-learn · LightGBM (TF-IDF first, embeddings v2)    |
| LLM       | Gemini (behind a provider-swappable interface)           |
| Infra     | Docker · GitHub Actions · Vercel · Render                |

## Repository layout

```
phishguard-ai/
├── frontend/   # Next.js app
├── backend/    # FastAPI + Celery (Clean Architecture)
├── ml/         # training pipelines, datasets, model registry
├── infra/      # Dockerfiles, compose, CI
└── docs/       # architecture, ADRs
```

## Quick start (local, full stack)

```bash
cp .env.example .env          # fill in secrets as needed
docker compose up --build     # postgres, redis, api, worker, web
```

| Service       | URL                             |
| ------------- | ------------------------------- |
| Frontend      | http://localhost:3000           |
| API (docs)    | http://localhost:8000/docs      |
| API health    | http://localhost:8000/api/v1/health |

## Development roadmap

Built in independently-demoable milestones — see the [roadmap](docs/architecture.md#roadmap).

- [x] **M0** — Foundation & scaffolding *(you are here)*
- [ ] **M1** — Email parsing engine
- [ ] **M2** — Feature engineering + rule scoring
- [ ] **M3** — ML training pipeline
- [ ] **M4** — Model serving + full fusion
- [ ] **M5** — Threat-intel integrations
- [ ] **M6** — LLM explanation layer
- [ ] **M7** — Auth, persistence & history API
- [ ] **M8** — Frontend dashboard
- [ ] **M9** — Hardening, CI/CD & docs

## License

MIT
