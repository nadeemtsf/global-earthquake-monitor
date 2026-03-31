# FastAPI/React Migration Architecture

## Purpose

This document fixes the target repository structure and migration boundaries for the move from the current Streamlit application to a FastAPI backend plus React frontend. It exists so later implementation issues can build against a stable target layout instead of making structural decisions ad hoc.

## Current State

The repository is currently a single Python/Streamlit application centered on:

- `src/app.py` as the Streamlit entrypoint
- `src/data.py`, `src/providers/`, `src/utils/`, and `src/ai/` as the reusable logic layers
- `tests/` as the existing Python test suite
- `xml/` as the current XML/XSLT-related assets

## Target Repository Layout

The migration target is a monorepo with separate backend and frontend applications plus shared documentation:

```text
global-earthquake-monitor/
  backend/
    app/
    tests/
    .env.example
    requirements.txt
  frontend/
    src/
    public/
    .env.example
    package.json
  transforms/
    *.xsl
  docs/
    MIGRATION_ARCHITECTURE.md
    ...
  README.md
```

### Layout intent

- `backend/`
  Owns the FastAPI application, XML/XSLT transformation pipeline, API routes, backend tests, and backend-specific configuration.
- `frontend/`
  Owns the React application, client-side state, charts, map UI, and frontend-specific configuration.
- `transforms/`
  Owns the visible XSLT deliverables used in the XML pipeline. This directory is intentionally top-level because it is a primary graded artifact.
- `docs/`
  Owns migration, architecture, and academic-deliverable documentation.

## Migration Boundary Decisions

### Streamlit transition policy

Streamlit remains temporarily during the migration for parity validation only.

- The current Streamlit app is the reference implementation for behavior and feature parity.
- New feature work should target the future FastAPI backend and React frontend, not expand the Streamlit architecture.
- Streamlit should be removed only after:
  - FastAPI can serve the required backend endpoints
  - React reaches parity for the required frontend views
  - XML/XSLT pipeline deliverables are present and documented

### What stays in legacy code temporarily

- Existing business logic in `src/data.py`, `src/providers/`, `src/utils/`, and `src/ai/` may remain temporarily while being extracted into backend-safe modules.
- Existing tests remain valid reference coverage until they are moved or mirrored under `backend/tests/`.

### What should not be built in legacy code

- No new long-term routing or API logic should be added to Streamlit.
- No new frontend-only feature architecture should be added under `src/ui/` beyond temporary parity support.
- New XML/XSLT pipeline work should target the future backend and top-level `transforms/` structure.

## Local Development Commands

These commands define the intended local development workflow during and after migration.

### Current legacy app

```bash
pip install -r requirements.txt
streamlit run src/app.py
pytest -q
```

### Target backend workflow

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest -q
```

### Target frontend workflow

```bash
cd frontend
npm install
npm run dev
npm run build
```

## Environment File Locations

### Current

- Root Python environment variables are used by the current app.
- `.streamlit/secrets.toml` may provide Streamlit-only secrets locally.

### Target

- `backend/.env.example`
  Documents backend configuration such as API keys, cache URLs, CORS origins, and provider settings.
- `frontend/.env.example`
  Documents frontend configuration such as `VITE_API_URL`.
- No real secrets should be committed in tracked files.

## Deployment Units

The deployment target is two separate application units:

- Backend deployment unit
  A FastAPI service with its own runtime, environment variables, cache configuration, and backend CI pipeline.
- Frontend deployment unit
  A React/Vite build deployed separately with its own environment variables and frontend CI pipeline.

This split keeps backend secrets and runtime concerns separate from frontend delivery.

## XML/XSLT Boundary

The XML/XSLT pipeline is a required architectural boundary, not an optional detail.

- Raw XML or QuakeML is fetched from upstream providers.
- XSLT stylesheets in `transforms/` convert source XML into canonical XML.
- Canonical XML is the backend source of truth before JSON serialization.
- `GET /api/v1/export/xml` must return canonical transformed XML.
- README and supporting docs must explain the pipeline with diagram, sample input, and sample output.

## Migration Checklist

- Create `backend/` and move backend runtime code there.
- Create `frontend/` and scaffold the React app there.
- Move XSLT assets from `xml/` to top-level `transforms/`.
- Extract framework-agnostic services from the current Streamlit code.
- Use Streamlit only for temporary parity validation until replacement is complete.
