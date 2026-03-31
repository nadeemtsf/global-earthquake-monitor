# Backend Security & Middleware

This document describes the cross-cutting security protections introduced in
**issue #09** and how to configure them for local development, staging, and
production.

---

## 1. API Key Authentication

### How it works

Every public endpoint (excluding `/health`) can require callers to supply a
shared secret via the `X-API-Key` request header.  The check is implemented as
a FastAPI `Depends` injectable in `backend/app/core/security.py` using
`hmac.compare_digest` for constant-time comparison to resist timing attacks.

```
GET /api/v1/earthquakes
X-API-Key: <your-api-key>
```

### Configuration

| Variable | Default | Description |
|---|---|---|
| `API_KEY_ENABLED` | `false` | Set `true` to enforce key checking |
| `API_KEY` | *(empty)* | The shared secret key |

### Development bypass (local React development)

`API_KEY_ENABLED` defaults to `false`.  With this default the Vite dev server
(`npm run dev`) can reach the backend at `http://localhost:8000` **without**
any API key header.  No other bypass rules or special headers are needed.

```bash
# backend/.env  (development)
API_KEY_ENABLED=false
API_KEY=
```

### Enabling in staging / production

```bash
# Generate a strong key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# backend/.env  (staging / production)
API_KEY_ENABLED=true
API_KEY=<the-generated-key>
```

When enforcement is on, the frontend must forward the key in every request:

```ts
// frontend — Axios / fetch wrapper example
headers: {
  "X-API-Key": import.meta.env.VITE_API_KEY,
}
```

Add `VITE_API_KEY` to `frontend/.env` (and to the CI/CD secret store, not
version control).

### Protected vs. exempt routes

| Route | Key enforced? |
|---|---|
| `GET /health` | ❌ Always public (liveness probe must work unauthenticated) |
| `GET /api/v1/earthquakes` | ✅ When `API_KEY_ENABLED=true` |
| `GET /api/v1/earthquakes/summary` | ✅ When `API_KEY_ENABLED=true` |
| `POST /api/v1/chat` | ✅ When `API_KEY_ENABLED=true` |
| `GET /api/v1/export/*` | ✅ When `API_KEY_ENABLED=true` |

Routers that want to enforce the key add `Depends(require_api_key)`:

```python
from app.core.security import require_api_key

@router.get("", dependencies=[Depends(require_api_key)])
def list_earthquakes(...):
    ...
```

---

## 2. Rate Limiting

### How it works

An in-memory sliding-window rate limiter is registered as ASGI middleware in
`backend/app/core/rate_limit.py`.  It counts requests per client IP within a
configurable window and returns **HTTP 429 Too Many Requests** when the limit
is exceeded.

Response headers inform API clients of their quota:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 42
X-RateLimit-Window: 60
Retry-After: 60      # 429 responses only
```

### Configuration

| Variable | Default | Description |
|---|---|---|
| `RATE_LIMIT_ENABLED` | `true` | Toggle the limiter on/off |
| `RATE_LIMIT_REQUESTS` | `60` | Requests allowed per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Window duration (seconds) |

### Development (local React)

The default of **60 requests per minute** is intentionally generous.  Normal
Vite hot-reload + API calls will not approach this limit.

If you run automated scripts or integration tests locally and hit the limit,
either raise `RATE_LIMIT_REQUESTS` in `.env` or set `RATE_LIMIT_ENABLED=false`
temporarily.

### Exempt paths

The following paths are **never** rate-limited regardless of configuration:

- `/health`
- `/docs`
- `/redoc`
- `/openapi.json`

### Client identification

The client IP is derived from the `X-Forwarded-For` header (first entry) when
present, falling back to the direct connection address.  This is correct for
deployments behind a single trusted reverse proxy.

---

## 3. CORS

CORS is configured by the `CORS_ALLOWED_ORIGINS` environment variable (see
`.env.example`).

The `allow_headers` list is now explicit (no wildcard) and includes
`X-API-Key` so browsers do not block the authentication header in cross-origin
pre-flight checks.

```
Access-Control-Allow-Headers: Content-Type, Authorization, X-API-Key, ...
```

Development default allows both Vite ports:

```bash
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## 4. Request Logging

All requests are logged at `INFO` level with method, path, HTTP status, and
elapsed time:

```
2026-03-31T18:00:00 [INFO] app.main — GET /api/v1/earthquakes → 200 (42.31 ms)
```

Set `LOG_LEVEL=DEBUG` to also see API key bypass notifications and
per-request rate-limit decisions.

---

## 5. Input Validation

FastAPI/Pydantic validates all query parameters and request bodies before they
reach handler code.  Invalid inputs (wrong types, out-of-range magnitudes, etc.)
return structured `422 Unprocessable Entity` responses automatically — no
additional validation layer is needed at the middleware level for type safety.

Custom range validation (e.g. `ge=0.0, le=10.0` on magnitude) is declared
directly on the query parameter annotations in each router and enforced by
Pydantic at the framework level.

---

## 6. Exception Handling

A global exception handler in `app/main.py` catches any unhandled exception and
returns a structured `500 Internal Server Error` response instead of leaking
stack traces or Python object representations to clients.

```json
{
  "detail": "An internal server error occurred.",
  "type": "SomeExceptionType"
}
```
