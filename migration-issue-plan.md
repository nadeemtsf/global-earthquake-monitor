# FastAPI/React Migration Issue Plan

## Summary

The project is still a modular Streamlit application, but most of the reusable backend-worthy logic already exists in provider, utility, AI, and data modules. The migration should therefore focus on extracting framework-agnostic services, mounting them behind FastAPI, and then building the React frontend against stable API contracts.

An important academic requirement changes the priority of the migration: XML and XSLT must be a central, visible, graded component of the system. The intended pipeline is:

`raw XML/QuakeML input -> XSLT transformation -> canonical XML schema -> JSON API responses`

That means the canonical XML representation is the authoritative intermediate format, the `/transforms/` directory and `.xsl` stylesheets are required deliverables, the README must visibly explain the XML/XSLT pipeline, and `GET /api/v1/export/xml` must return the transformed canonical XML rather than raw upstream data.

## Final Ordered Issue Set

1. **[01] Revoke leaked GitHub token and remove hardcoded secrets**
2. **[02] Define target repository layout and migration boundaries**
3. **[03] Extract framework-agnostic domain/service layer from Streamlit code**
4. **[04] [Backend] Setup FastAPI Project Structure & Architecture**
5. **[05] Define API contracts and response schemas**
6. **[06] [Backend] Build Core XML/XSLT Data Processing Pipeline**
7. **[07] [Backend] XSLT Visibility & Architectural Documentation**
8. **[08] [Backend] Create Core REST Endpoints**
9. **[09] Backend security and platform middleware**
10. **[10] Port AI chat endpoint**
11. **[11] Port export/report routes**
12. **[12] [Frontend] Initialize React Architecture & Environment**
13. **[13] [Frontend] Implement API Integration & Global State**
14. **[14] [Frontend] Implement Distribution Analytics Tab**
15. **[15] [Frontend] Implement Geographic Map**
16. **[16] [Frontend] Implement Timeline Playback & Animation**
17. **[17] [Frontend] Implement Time Series, Search, & AI UI**
18. **[18] Search/grid backend support if dataset size requires it**
19. **[19] [Backend] Delivery: Containerization, CI/CD, & Cloud Deployment**
20. **[20] [Frontend] Delivery: Edge Deployment & CI Pipeline**

## Key Changes

### Ordering and issue ownership

- Existing migration issues `#46` through `#57` should be edited in place where they still map cleanly to the revised migration sequence.
- New governance and split-out issues should be created as new GitHub issues so the migration board fully reflects the intended order.
- Geographic map implementation is split from timeline playback so base map parity lands before animation work.
- AI backend delivery is split from PDF/report export so each issue has a clear review scope.
- Security and rate limiting are split out from the core REST endpoint issue.
- Search/grid backend support is explicitly optional and only added if frontend dataset size makes it necessary.

### XML/XSLT as a core deliverable

- The backend pipeline must visibly flow through XML at every transformation stage.
- Raw XML sources from providers must be normalized through XSLT into a canonical XML schema before the API emits JSON.
- The canonical XML schema is the source of truth for downstream serialization and export behavior.
- The `/transforms/` folder with `.xsl` files is mandatory and must be prominent enough for grading review.
- The README must contain a dedicated XML/XSLT section with:
  - an architecture diagram
  - sample source XML
  - sample transformed canonical XML
  - explanation of each stylesheet's responsibility
- `GET /api/v1/export/xml` must serve the fully transformed canonical XML, never raw upstream XML.

### Existing issue edits reflected in the final sequence

- **#46** becomes the FastAPI bootstrap issue only.
- **#47** becomes the XML/XSLT-centered pipeline issue with explicit canonical XML ownership.
- **#48** becomes the grading-visibility/documentation issue for `/transforms/` and README coverage.
- **#49** becomes the functional REST endpoints issue without security scaffolding.
- **#50** is split into separate AI chat and export/report issues.
- **#52** remains the frontend scaffold issue.
- **#53** remains the frontend integration and global state issue.
- **#54** remains the distribution analytics tab issue.
- **#55** is effectively split into a dedicated geographic map issue and a dedicated timeline playback issue.
- **#56** becomes the combined time series, search, and AI UI issue.
- **#51** and **#57** stay as backend and frontend delivery issues, but with clearer CI/deployment expectations.

## Test Plan

- Validate that the managed issue list contains exactly 20 uniquely ordered items.
- Validate that issue titles are prefixed with zero-padded order markers such as `[01]` through `[20]`.
- Validate that legacy issue edits are routed through `PATCH` and new issues are routed through `POST`.
- Validate that all issues include labels and complete title/body content.
- Validate that the XML/XSLT academic requirements appear explicitly in the pipeline, documentation, and REST endpoint issues.
- Validate that `create_issues2.py` is no longer needed because all issue management lives in `create_issues.py`.
- Validate that the plan document and the automation script describe the same ordered issue set and the same XML/XSLT requirements.

## Assumptions and Defaults

- Existing migration issues `#46` through `#57` are the current edit targets for the subset of issues that still map to them.
- New planning, security, export, timeline, and search-support issues will be created as additional GitHub issues.
- Zero-padded ordering is required so GitHub titles sort predictably.
- The repository will use a single issue-management script going forward.
- The migration remains parity-first: backend and frontend should replace current Streamlit behavior before major redesign work is introduced.
