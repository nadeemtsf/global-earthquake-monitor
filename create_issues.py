import os
import sys
from typing import Any

import requests


REPO = os.getenv("GITHUB_REPO", "nadeemtsf/global-earthquake-monitor")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
API_URL = f"https://api.github.com/repos/{REPO}/issues"


def required_body(description: str, tasks: list[str]) -> str:
    task_lines = "\n".join(f"- [ ] {task}" for task in tasks)
    return f"## Description\n{description}\n\n## Tasks\n{task_lines}"


ISSUES: list[dict[str, Any]] = [
    {
        "order": 1,
        "title": "Revoke leaked GitHub token and remove hardcoded secrets",
        "body": required_body(
            "A plaintext GitHub personal access token was committed into the repository tooling. Treat it as compromised immediately and remove hardcoded secret handling from the issue-management workflow before any further migration work proceeds.",
            [
                "Revoke the exposed GitHub token and rotate any replacement credentials.",
                "Remove hardcoded secrets from repository-tracked files and switch all GitHub automation to environment-variable based authentication.",
                "Update issue-management scripts and related documentation to require `GITHUB_TOKEN` from the environment.",
                "Add or document secret-scanning safeguards in CI or repository settings where available.",
            ],
        ),
        "labels": ["security", "devops", "tooling"],
    },
    {
        "order": 2,
        "title": "Define target repository layout and migration boundaries",
        "body": required_body(
            "Define the target monorepo structure and migration boundaries before implementation work expands. This issue exists to remove ambiguity about how the Streamlit codebase transitions into a FastAPI backend plus React frontend.",
            [
                "Document the target repository layout, including `backend/`, `frontend/`, and any shared package or docs locations.",
                "Decide whether Streamlit remains temporarily for parity validation or is removed immediately after backend/frontend replacement lands.",
                "Document local development commands, env file locations, and deployment units for backend and frontend.",
                "Record explicit migration boundaries so future issues do not need to make structural decisions on the fly.",
            ],
        ),
        "labels": ["architecture", "devops", "planning"],
    },
    {
        "order": 3,
        "title": "Extract framework-agnostic domain/service layer from Streamlit code",
        "body": required_body(
            "The current application logic is reusable, but it is still entangled with Streamlit in key entrypoints and caching layers. Extract the business logic into framework-agnostic services so FastAPI can adopt it cleanly and Streamlit can be retired without duplicating behavior.",
            [
                "Move data loading, provider orchestration, aggregation, PDF generation, and AI context generation into modules with no `streamlit` dependency.",
                "Replace `st.cache_data` usage with a backend-safe caching abstraction that can later use Redis or filesystem caching.",
                "Keep the current Streamlit UI functioning temporarily by calling the extracted services instead of owning business logic directly.",
                "Preserve current schema semantics so the FastAPI layer can expose the same analytical capabilities with stable contracts.",
            ],
        ),
        "labels": ["backend", "architecture", "refactor"],
    },
    {
        "order": 4,
        "issue_number": 46,
        "title": "[Backend] Setup FastAPI Project Structure & Architecture",
        "body": required_body(
            "Initialize the FastAPI backend as the decoupled application shell that will host the extracted earthquake, export, and chat services. This issue is strictly about backend bootstrap and application structure, not full feature delivery.",
            [
                "Set up the FastAPI application entrypoint, app factory or equivalent initialization flow, and router registration.",
                "Configure CORS middleware for the React frontend with environment-driven allowed origins.",
                "Add structured settings management for API keys, URLs, cache configuration, and deployment-specific runtime values.",
                "Create a documented `.env.example` covering backend configuration without exposing secrets.",
                "Create router scaffolding for `/api/v1/earthquakes`, `/api/v1/chat`, and `/api/v1/export` plus a basic `/health` endpoint.",
                "Add baseline logging, exception handling, and dependency wiring needed for the later issues.",
            ],
        ),
        "labels": ["backend", "architecture", "devops"],
    },
    {
        "order": 5,
        "title": "Define API contracts and response schemas",
        "body": required_body(
            "Freeze the public API contracts before the React app is built against them. The goal is to define canonical request and response shapes so backend and frontend work can proceed independently without guessing field names or payload structure.",
            [
                "Define request parameters and response schemas for `GET /api/v1/earthquakes`.",
                "Define response schemas for `GET /api/v1/earthquakes/aggregate`, `POST /api/v1/chat`, `GET /api/v1/export/xml`, and `GET /api/v1/export/pdf`.",
                "Define the canonical earthquake event fields derived from the current normalized dataset.",
                "Document how canonical XML is converted into JSON response models for the frontend.",
            ],
        ),
        "labels": ["api", "architecture", "backend"],
    },
    {
        "order": 6,
        "issue_number": 47,
        "title": "[Backend] Build Core XML/XSLT Data Processing Pipeline",
        "body": required_body(
            "This is a primary graded component. The entire data pipeline must visibly and explicitly flow through XML: raw QuakeML/XML input, XSLT transformation, canonical XML schema output, and only then JSON serialization for the API. XML and XSLT are not optional implementation details; they are a core architectural deliverable.",
            [
                "Fetch raw XML sources from upstream providers, including QuakeML from USGS and XML/RSS source data from GDACS, instead of treating GeoJSON as the primary pipeline.",
                "Design XSLT stylesheets that transform provider-specific XML into a canonical internal XML schema such as `<earthquake-dashboard-data>`.",
                "Use an XML processing library such as `lxml` to execute XSLT transformations in-memory inside the backend pipeline.",
                "Make canonical XML the authoritative intermediate representation before any JSON serialization occurs.",
                "Cache transformed canonical XML or the corresponding transformation results using Redis or filesystem caching to avoid excessive upstream bandwidth usage.",
                "Ensure the end-to-end backend data flow is explicitly raw XML/QuakeML in -> XSLT transform -> canonical XML out -> JSON API responses.",
            ],
        ),
        "labels": ["backend", "data", "xml-processing"],
    },
    {
        "order": 7,
        "issue_number": 48,
        "title": "[Backend] XSLT Visibility & Architectural Documentation",
        "body": required_body(
            "The XML/XSLT layer must be prominent and easy for evaluators to inspect. This issue exists to make the transformation pipeline a visible, reviewable, graded deliverable rather than hidden implementation glue.",
            [
                "Create a top-level or clearly visible `/transforms/` directory containing the `.xsl` stylesheets used by the backend pipeline.",
                "Document the purpose of each stylesheet and what stage of the transformation pipeline it owns.",
                "Add a dedicated README or README section explaining the XML/XSLT pipeline end to end with an architecture diagram, sample input XML, sample transformed canonical XML, and stylesheet responsibilities.",
                "Describe the canonical XML schema clearly enough that the professor can understand the transformation flow without reading the source code.",
                "Ensure the documentation makes it obvious that `/transforms/` and the XSLT pipeline are mandatory graded deliverables.",
            ],
        ),
        "labels": ["backend", "documentation", "xml-processing"],
    },
    {
        "order": 8,
        "issue_number": 49,
        "title": "[Backend] Create Core REST Endpoints",
        "body": required_body(
            "Expose the transformed earthquake dataset through clean REST endpoints for the React frontend while preserving visible XML export for grading. JSON responses must be derived from the canonical XML representation produced by the XSLT pipeline.",
            [
                "Create `GET /api/v1/earthquakes` with query parameters such as `start_date`, `end_date`, `min_mag`, and `provider`.",
                "Convert canonical `<earthquake-dashboard-data>` XML into the standardized JSON response model used by the frontend.",
                "Create `GET /api/v1/earthquakes/aggregate` returning precomputed distributions and summary datasets needed by the analytics UI.",
                "Create `GET /api/v1/export/xml` that returns the fully XSLT-transformed canonical XML, not raw upstream source XML.",
                "Ensure endpoint behavior and serialization clearly reflect the pipeline raw XML/QuakeML -> XSLT -> canonical XML -> JSON API output.",
            ],
        ),
        "labels": ["api", "backend", "xml"],
    },
    {
        "order": 9,
        "title": "Backend security and platform middleware",
        "body": required_body(
            "Add cross-cutting backend protections after the main endpoints exist so security concerns are implemented cleanly without distorting the functional API issue.",
            [
                "Implement API key verification or equivalent request authentication middleware appropriate for the public API surface.",
                "Add rate limiting for public endpoints to reduce abuse risk.",
                "Document any environment-specific bypass or development-mode rules needed for local React development.",
                "Review CORS, logging, and request validation middleware as part of the security hardening pass.",
            ],
        ),
        "labels": ["backend", "security", "api"],
    },
    {
        "order": 10,
        "title": "Port AI chat endpoint",
        "body": required_body(
            "Move the existing AI assistant behavior into a stateless backend endpoint so the React frontend can consume it without embedding provider credentials or Streamlit-specific session behavior.",
            [
                "Create `POST /api/v1/chat` using the backend AI service layer and Gemini integration.",
                "Define request and response payloads for user prompts, assistant responses, and any structured metadata needed by the frontend.",
                "Preserve the current earthquake-context generation logic so responses remain grounded in the filtered dataset.",
                "Handle missing API keys, provider failures, and quota exhaustion with explicit API responses.",
            ],
        ),
        "labels": ["backend", "ai", "api"],
    },
    {
        "order": 11,
        "title": "Port export/report routes",
        "body": required_body(
            "Expose report-generation features as backend routes that the React frontend can call directly. This issue is intentionally focused on report/export behavior and should not own the canonical XML export if that already lives under the REST endpoints issue.",
            [
                "Create `GET /api/v1/export/pdf` returning `application/pdf` streams generated from the backend reporting layer.",
                "Reuse the current PDF generation logic while removing any Streamlit-specific assumptions.",
                "Define request parameters needed to generate reports from the current filtered earthquake dataset.",
                "Coordinate export UX expectations with the frontend so downloads map cleanly to backend routes.",
            ],
        ),
        "labels": ["backend", "reporting", "api"],
    },
    {
        "order": 12,
        "issue_number": 52,
        "title": "[Frontend] Initialize React Architecture & Environment",
        "body": required_body(
            "Scaffold the React frontend that will replace the Streamlit shell. This issue is only about project setup, environment wiring, and the main UI shell, not data feature implementation.",
            [
                "Initialize the frontend using Vite with React and TypeScript.",
                "Set up the main application shell, including sidebar filters area and main content area.",
                "Configure routing for the planned feature areas and major tabs.",
                "Create a documented frontend `.env.example` including `VITE_API_URL` and any other non-secret configuration.",
                "Add baseline styling infrastructure and initial layout conventions for the new frontend.",
            ],
        ),
        "labels": ["architecture", "devops", "frontend"],
    },
    {
        "order": 13,
        "issue_number": 53,
        "title": "[Frontend] Implement API Integration & Global State",
        "body": required_body(
            "Connect the React frontend to the FastAPI backend using stable API contracts and a shared filter state model that replaces the current Streamlit sidebar-driven behavior.",
            [
                "Implement global filter state for date range, provider selection, magnitude thresholds, and related controls.",
                "Create a typed API client that targets the FastAPI endpoints and forwards required headers.",
                "Add query/state management for loading, error, and cache behavior using TanStack Query or an equivalent library.",
                "Align request serialization and response typing with the backend API contract issue.",
            ],
        ),
        "labels": ["data", "frontend", "security"],
    },
    {
        "order": 14,
        "issue_number": 54,
        "title": "[Frontend] Implement Distribution Analytics Tab",
        "body": required_body(
            "Port the current distribution-focused analytics into React with parity to the existing Streamlit visualizations and summary tables.",
            [
                "Implement the Top 10 significant earthquakes table.",
                "Render the magnitude distribution histogram using the selected charting library.",
                "Render the alert-level breakdown chart.",
                "Port the top regions visualization and alert severity spread view.",
                "Use backend aggregate data where appropriate instead of rebuilding heavy calculations only in the client.",
            ],
        ),
        "labels": ["frontend", "visualization"],
    },
    {
        "order": 15,
        "title": "[Frontend] Implement Geographic Map",
        "body": required_body(
            "Port the core geographic earthquake map into React first, keeping base rendering and marker interaction separate from playback and animation concerns.",
            [
                "Render the base map using the chosen React mapping stack.",
                "Plot earthquake markers with appropriate magnitude and alert-level visual encoding.",
                "Provide tooltip or detail interactions comparable to the current Streamlit map behavior.",
                "Ensure the initial geographic view achieves parity before timeline playback is introduced.",
            ],
        ),
        "labels": ["frontend", "map", "visualization"],
    },
    {
        "order": 16,
        "title": "[Frontend] Implement Timeline Playback & Animation",
        "body": required_body(
            "Add timeline playback as a dedicated follow-up to the geographic map so animation and playback performance can be implemented and tested independently.",
            [
                "Add a time scrubber and playback controls that animate earthquake visibility over time.",
                "Use browser-native animation primitives such as `requestAnimationFrame` where appropriate.",
                "Keep playback state synchronized with the rendered map markers and current filter state.",
                "Optimize for smooth interaction without blocking or regressing the baseline geographic map experience.",
            ],
        ),
        "labels": ["frontend", "map", "visualization"],
    },
    {
        "order": 17,
        "issue_number": 56,
        "title": "[Frontend] Implement Time Series, Search, & AI UI",
        "body": required_body(
            "Complete the remaining React feature surfaces by porting the time-series views, the search/grid experience, and the conversational AI UI.",
            [
                "Implement the time-series visualizations using the backend data contracts.",
                "Build the search or data-grid experience for filtered earthquake exploration.",
                "Build a chat-style UI for the backend `POST /api/v1/chat` endpoint.",
                "Connect PDF downloads and any other export actions needed by the frontend.",
                "Keep the XML export behavior aligned with the dedicated backend XML endpoint.",
            ],
        ),
        "labels": ["ai", "frontend", "visualization"],
    },
    {
        "order": 18,
        "title": "Search/grid backend support if dataset size requires it",
        "body": required_body(
            "If the client-side search/grid experience becomes too heavy for realistic datasets, add backend support so the frontend can handle sorting, filtering, pagination, or bulk export without loading everything into the browser at once.",
            [
                "Evaluate whether the grid requires server-side pagination, sorting, or filtering.",
                "Add backend endpoints or query options for large dataset search workflows if needed.",
                "Add CSV or equivalent export behavior only if the React search/grid flow requires it.",
                "Document the threshold or rationale for moving grid behavior server-side.",
            ],
        ),
        "labels": ["backend", "data", "frontend"],
    },
    {
        "order": 19,
        "issue_number": 51,
        "title": "[Backend] Delivery: Containerization, CI/CD, & Cloud Deployment",
        "body": required_body(
            "Deliver the FastAPI backend as a deployable service with repeatable CI validation and environment-aware infrastructure configuration.",
            [
                "Create deployment configuration for the chosen backend host, including runtime and cache requirements.",
                "Deploy the FastAPI backend to the selected cloud platform.",
                "Set up CI to run backend tests on pull requests and pushes to main.",
                "Include any health-check or environment configuration needed by the deployed service.",
            ],
        ),
        "labels": ["backend", "ci-cd", "devops"],
    },
    {
        "order": 20,
        "issue_number": 57,
        "title": "[Frontend] Delivery: Edge Deployment & CI Pipeline",
        "body": required_body(
            "Deliver the React frontend as a production build with CI validation and deployment configuration appropriate for the chosen frontend host.",
            [
                "Prepare the production frontend build and TypeScript validation flow.",
                "Deploy the frontend to the selected host such as Vercel or another static/edge platform.",
                "Add CI checks for frontend build and lint validation.",
                "Document any environment variables or routing configuration required by the deployed frontend.",
            ],
        ),
        "labels": ["ci-cd", "devops", "frontend"],
    },
]


def build_headers() -> dict[str, str]:
    if not GITHUB_TOKEN:
        raise RuntimeError(
            "Missing GITHUB_TOKEN environment variable. "
            "Set GITHUB_TOKEN before running this script."
        )

    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }


def format_title(order: int, title: str) -> str:
    return f"[{order:02d}] {title}"


def validate_issues(issues: list[dict[str, Any]]) -> None:
    seen_orders: set[int] = set()
    seen_titles: set[str] = set()
    required_keys = {"order", "title", "body", "labels"}

    for issue in issues:
        missing = required_keys - issue.keys()
        if missing:
            raise ValueError(f"Issue missing required keys {sorted(missing)}: {issue}")

        order = issue["order"]
        final_title = format_title(order, issue["title"])

        if order in seen_orders:
            raise ValueError(f"Duplicate order detected: {order}")
        if final_title in seen_titles:
            raise ValueError(f"Duplicate final title detected: {final_title}")
        if not isinstance(issue["labels"], list) or not issue["labels"]:
            raise ValueError(f"Issue must include a non-empty labels list: {final_title}")

        seen_orders.add(order)
        seen_titles.add(final_title)


def sync_issue(issue: dict[str, Any], headers: dict[str, str]) -> None:
    payload = {
        "title": format_title(issue["order"], issue["title"]),
        "body": issue["body"],
        "labels": issue["labels"],
    }

    issue_number = issue.get("issue_number")
    if issue_number is not None:
        url = f"{API_URL}/{issue_number}"
        response = requests.patch(url, headers=headers, json=payload, timeout=30)
        action = "PATCHED"
    else:
        url = API_URL
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        action = "CREATED"

    if response.ok:
        data = response.json()
        print(f"{action}: {payload['title']} -> {data['html_url']}")
        return

    print(
        f"FAILED: {payload['title']} -> {response.status_code} {response.text}",
        file=sys.stderr,
    )


def main() -> None:
    validate_issues(ISSUES)
    headers = build_headers()

    print(f"Syncing {len(ISSUES)} issues against {REPO}...")
    for issue in sorted(ISSUES, key=lambda item: item["order"]):
        sync_issue(issue, headers)


if __name__ == "__main__":
    main()
