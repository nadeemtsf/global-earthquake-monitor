# Global Earthquake Monitor

A real-time earthquake monitoring application that aggregates and normalizes data from multiple seismic data sources: **USGS Earthquake Catalog** and **GDACS (Global Disaster Alert and Coordination System)**.

The project is a monorepo with a **FastAPI** backend and a **React (Vite + TypeScript)** frontend, connected by a canonical XML/XSLT transformation pipeline.

---

## Architecture

```text
global-earthquake-monitor/
  backend/      FastAPI app, XML/XSLT pipeline, API routes, tests
  frontend/     React + Vite + Tailwind UI
  transforms/   XSLT stylesheets (USGS + GDACS -> canonical)
  docs/         API contracts, migration architecture, security
```

- **backend/** — FastAPI (uvicorn) on `http://localhost:8000`
- **frontend/** — Vite dev server on `http://localhost:5173`
- **transforms/** — XSLT stylesheets used by the backend canonicalization pipeline. See [transforms/README.md](transforms/README.md).

API contracts are documented in [docs/API_CONTRACTS.md](docs/API_CONTRACTS.md). Security notes live in [docs/SECURITY.md](docs/SECURITY.md).

---

## Quick Start (Docker)

```bash
git clone https://github.com/nadeemtsf/global-earthquake-monitor.git
cd global-earthquake-monitor
cp backend/.env.example backend/.env   # fill in API keys
docker compose --profile dev up --build
```

- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:5173`

To run backend only:

```bash
docker compose up --build backend
```

---

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run tests and lint:

```bash
cd backend
pytest -v
ruff check .
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Type check and build:

```bash
cd frontend
npx tsc --noEmit
npm run build
```

---

## Features

### Multi-Provider Data Pipeline
- Parallel fetching from **USGS** and **GDACS** with a strategy-based provider architecture.
- Historical data access across configurable date ranges.
- Local cache fallback when upstream APIs are unreachable.

### XML / XSLT Pipeline
- Raw QuakeML XML and GDACS RSS feeds are normalized to a canonical XML schema via XSLT.
- Canonical output is the authoritative form used by API consumers and exports.

### Export & Reporting
- REST endpoints for filtered earthquake data, summaries, and PDF situation reports.

### Seismic AI Assistant
- Integrated AI chat backed by Google Gemini, with context-aware responses over the currently filtered dataset.

### Interactive Dashboard
- React + Tailwind UI with map, time-series, timeline, and analytics views.
- Real-time filters for date, magnitude, region, country, and alert level.

---

## Data Sources

1. **USGS Earthquake Catalog** — [fdsnws/event/1/](https://earthquake.usgs.gov/fdsnws/event/1/) (GeoJSON/QuakeML)
2. **GDACS RSS Feed** — [Global Disaster Alert System](https://www.gdacs.org/) (RSS/XML)

---

## Quality Assurance

- **Linting:** `ruff` (backend), ESLint + TypeScript (frontend).
- **Testing:** `pytest` suite for backend API, pipeline, and security.
- **CI:** GitHub Actions runs secret scanning, backend lint + tests, Docker build, and frontend type-check + build on every push and PR.
- **Secret hygiene:** All tokens and API keys are provided via environment variables. Real `.env` files are gitignored.

---

## Secrets

This repository must not store plaintext credentials in tracked files.

- Backend configuration is read from `backend/.env` (see `backend/.env.example`).
- Real `.env` files are gitignored.

If a token was ever committed, revoke it immediately and replace it before continuing development.

---

## License

This project is licensed. See the `LICENSE` file for details.

Unless stated otherwise by the author, all rights are reserved. If you want to reuse or redistribute any part of this repository, please contact the author first for permission.

---

## Author

**Nadim Baboun**
[GitHub Profile](https://github.com/nadeemtsf)
