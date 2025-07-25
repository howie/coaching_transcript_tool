# Coach‑Review Agent – MVP TODO Breakdown

> Last updated: 2025‑07‑25 (UTC+8)

## 0. Project Setup

* [ ] Initialize monorepo or single repo structure (`/core`, `/api`, `/integrations`).
* [ ] Add `pyproject.toml` + `ruff`/`black`/`mypy` configs.
* [ ] Create `.windsurf/rules.md` & `.cline/rules.md` to guide agents.

## 1. Core / Backend

* [ ] Abstract `TranscriptParser` interface to support **VTT / SRT / Audio(JSON)**.
* [ ] Refactor CLI-only code into importable module: `coaching_transcript/core.py`.
* [ ] Expose main pipeline function: `format_transcript(input_bytes, filename, output="excel|markdown")`.
* [ ] Publish to internal PyPI (optional) for easier reuse.
* [ ] Write unit tests with `pytest` (coverage ≥ 80%).

## 2. API & Cloud

* [ ] Implement FastAPI endpoint `POST /format` (multipart upload).
* [ ] Add storage layer (AWS S3 or Cloudflare R2) + pre‑signed URL return.
* [ ] Docker multi‑stage build (builder → slim runtime).
* [ ] GitHub Actions: lint, test, build & push container.
* [ ] One‑click deploy scripts for Replit Deploy / Fly.io / Render.

## 3. Auth, Rate Limit & Billing (Phase 1 minimal)

* [ ] Implement API key auth (env var or simple DB table).
* [ ] Add per‑key daily quota (e.g., #files or minutes of audio).
* [ ] Log request metadata (user\_id, size, duration) for billing analytics.
* [ ] Stripe checkout link for upgrading plan (manual mapping ok for MVP).

## 4. Custom GPT (Action Path)

* [ ] Draft system prompt & instructions in English/Chinese.
* [ ] Import OpenAPI schema into GPT Builder → **Actions**.
* [ ] Configure OAuth2/API Key in Actions (if needed) and test sign‑in flow.
* [ ] Provide sample files & walkthrough inside GPT knowledge.

## 5. MCP Agent

* [ ] Generate `openapi.json` from FastAPI; host at `/openapi.json`.
* [ ] Create `mcp.yaml` manifest (name, description, auth, endpoints).
* [ ] Package simple `mcp-server` wrapper (if needed) or list as HTTP API.
* [ ] Submit to mcp.directory (or internal catalog) for discovery.

## 6. (Optional) Slack / Teams Bot PoC

* [ ] Choose platform: Slack Bolt / Teams Bot Framework.
* [ ] Slash command `/review-meeting` → upload transcript or link.
* [ ] Call `/format`, return Excel + summary to thread.
* [ ] Basic permission & tenant config.

## 7. QA / Testing / Observability

* [ ] Add integration tests: end‑to‑end file → Excel/MD output diff check.
* [ ] Setup logging (structured JSON) & error tracing (Sentry / OpenTelemetry).
* [ ] Health check & readiness endpoints.
* [ ] Load test: 10 concurrent 10MB files < 20s avg.

## 8. Security & Privacy

* [ ] Auto‑delete raw files after N hours (24h default).
* [ ] Add data processing & privacy statement to README/website.
* [ ] Region selection flag (future): `?region=ap-sg|eu-de|us-east`.

## 9. Docs & DevX

* [ ] `README.md`: quick start, API usage, examples.
* [ ] `API.md`: endpoint specs, auth, error codes.
* [ ] `CONTRIBUTING.md`: branch strategy, commit style (why/what/how).
* [ ] Example scripts: `curl`, `python client`, `js client`.

## 10. Launch & Marketing

* [ ] Landing copy draft (hero, value props, CTA) for doxa.com.tw product page.
* [ ] Short demo video / GIF walkthrough.
* [ ] Outreach list: coaching groups, ICF communities, LinkedIn posts.
* [ ] Collect beta feedback form (Google Form / Tally).

---

### Backlog / Nice‑to‑Have (Post‑MVP)

* [ ] Whisper integration for direct audio → VTT.
* [ ] Auto‑tag PCC Markers & sentiment/emotion cues.
* [ ] Webhook callbacks for async processing.
* [ ] Multi‑tenant dashboard (usage/billing/admin UI).
* [ ] Localization i18n (EN/zh‑TW/ja).
