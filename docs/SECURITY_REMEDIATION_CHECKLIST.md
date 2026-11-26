# Security remediation checklist

Tracks the findings of [SECURITY_REVIEW_2026-11-26.md](SECURITY_REVIEW_2026-11-26.md). Statuses
allowed: `OPEN`, `IN PROGRESS`, `FIXED` (only when the regression test exists and passes in CI on
`main`), `ACCEPTED` (the owner accepts the risk, or it is accepted for the pilot as stated), and
`BLOCKED`.

Add a dated update when a status changes. Don't rewrite a row's history.

| Last updated | 2026-11-26, review of `main` @ `8692a0c` |
| --- | --- |
| Counts (from the rows below) | 10 findings: 0 Critical, 0 High, 2 Medium, 5 Low, 3 Informational. 7 OPEN, 1 BLOCKED, 1 ACCEPTED, 1 human dependency |

| ID | Severity | Finding | Fix | Regression test | Owner action needed | Status |
| --- | --- | --- | --- | --- | --- | --- |
| SEC-01 | Medium | The application database role is a superuser and can skip the verification, append-only and isolation triggers | Separate owner, API (read-only) and curator roles; give each process its own URL | As the API role: `rolsuper = false`; `SET session_replication_role` and `UPDATE evidence` denied | Approve the database and deployment setup change; do it before real pilot data | OPEN |
| SEC-02 | Medium | No authentication or access control; localhost binding is the only gate | VPN or a reverse proxy with TLS and sign-in in front of the frontend; backend port not published; rate limits | Deployment smoke test: without credentials → 401/403 or no connection | Choose the pilot access method and hosting (Q-7) | BLOCKED (Q-7) |
| SEC-03 | Low | `GET /companies/{id}/evidence` returns local `file://` paths | Return only linkable URLs, or refuse `file://` for real evidence | Import a real bundle with a `file://` URL; the API does not return the path | Choose between the two fixes (API or importer behaviour) | OPEN |
| SEC-04 | Low | The company website link skips `safeHref` | `safeHref(c.website)` | Route check asserts the website `href`; `safeHref` unit tests already exist | Approve the fix | OPEN |
| SEC-05 | Low | No security headers; `X-Powered-By` sent | `poweredByHeader: false`; `headers()` with `frame-ancestors 'none'`, `nosniff`, `Referrer-Policy`; CSP after testing | Route check asserts the headers | Approve the fix | OPEN |
| SEC-06 | Low | Actions and images pinned by mutable tags | Pin to SHAs and digests; Dependabot or Renovate | Not applicable (a CI configuration review) | Approve the change | OPEN |
| SEC-07 | Low | No branch protection; PRs merged with 0 reviews | Protect `main`: PR, three checks, no force-push; record a human review | Not applicable (`gh api …/protection` returns rules) | Change the GitHub settings (owner only) | OPEN |
| SEC-08 | Informational | No rate limiting; some reads compute everything, then slice | Rate limit at the SEC-02 layer | Not applicable | None for the pilot | ACCEPTED (pilot scale) |
| SEC-09 | Informational | API docs on in every environment; health shows the environment | Turn docs off in production, or leave them on behind SEC-02 | `GET /docs` → 404 when `APP_ENV=production` | Decide with SEC-02 | OPEN |
| SEC-10 | Informational | Curator and reviewer are typed names | Authenticated identities (after SEC-02); appoint a reviewer (Q-3) | Not applicable | Appoint the reviewer (Q-3) | Human dependency |

No Critical or High finding was found, so no application code was changed (the scope allows fixes
for Critical and High only).
