# Security review, 2026-11-26 (P2-6.12)

Scope: the whole application on `main` @ `8692a0c` (PR #12 merge, WS4-4 Phase A): backend, frontend,
database migrations, Docker, Compose and GitHub Actions. Aim: find what must change before a
**controlled private pilot** (gate G2). Fixes and their status: [SECURITY_REMEDIATION_CHECKLIST.md](SECURITY_REMEDIATION_CHECKLIST.md).

**Who did this review.** An AI assistant (Claude Code), working for the owner. **This is not an
independent human review.** It does not close AU-6, W4-H2 or P2-8.11, and it is not a penetration
test.

**Result.** No Critical or High finding. Two findings are Medium, and both are pilot preconditions
rather than flaws you can exploit today: the application's database role is a superuser (SEC-01),
and there is no access control (SEC-02). Five findings are Low and three are Informational. The
scope says to fix only Critical and High findings, so **no application code changed**.

Labels used below: **VERIFIED** means checked on GitHub or in the running system. **TESTED** means
a command or test ran here, and its output is quoted. **NOT TESTED** and **BLOCKED** mean what they
say.

## 1. Baseline

| Check | Result | Label |
| --- | --- | --- |
| Working tree before the review | clean on `feat/ws4-4-phase-a`; `git fetch` brought `main` from `9d44fb4` to `8692a0c` | VERIFIED |
| Merge commit | `8692a0c1f5af39232011d2acf4e871da31a11617`, "Merge pull request #12"; PR #12 merged 2026-11-26T05:38:29Z by the owner's account; head `219856e` | VERIFIED (`gh pr view 12`) |
| Recorded reviews on PR #12 | **0** (`reviews: []`, `reviewDecision: ""`) | VERIFIED |
| Branch protection on `main` | none ("Branch not protected", HTTP 404) | VERIFIED (`gh api …/branches/main/protection`) |
| CI on the PR head `219856e` | `test` (Backend) pass, `build` (Frontend) pass, `compose` (Docker) pass | VERIFIED (`gh pr checks 12`; runs 45762066162, 45762066101, 45762066191) |
| CI on the merge `8692a0c` | Backend success: **404 passed**, plus `alembic upgrade head && alembic check`. Frontend success: lint, typecheck, **36/36**, build. Docker success: build, `up --wait`, health | VERIFIED (runs 45762922320, 45762922338, 45762922350; counts read from the job logs) |
| Merge tree compared with the PR head | `git diff 219856e 8692a0c` is empty | VERIFIED |

GitHub CI and local runs are recorded separately below. One does not stand in for the other.

## 2. Findings

Severity follows impact × likelihood in the **current** deployment: localhost only, no real data,
and no write endpoints.

### SEC-01 · Medium · The application's database role is a PostgreSQL superuser

- **Where:** `docker-compose.yml:30` builds `DATABASE_URL` from `POSTGRES_USER`. That is the
  superuser the `postgres` image creates. `.env.example:16` does the same for runs on the host.
  `backend/Dockerfile:20` runs migrations and the API with that same role.
- **Evidence (TESTED, on the isolated stack `atlasws44`, in a transaction that was rolled back):**
  - `select rolsuper, rolcreaterole, rolbypassrls from pg_roles where rolname = current_user` →
    `t | t | t`.
  - `BEGIN; SET LOCAL session_replication_role = replica; UPDATE evidence SET verification_status =
    'verified' WHERE id = (…) RETURNING …;` → `UPDATE 1`, status `verified`. Then `ROLLBACK`.

  The triggers that make evidence start as `unverified` and only change through a two-person review
  (`atlas_guard_evidence`, `atlas_apply_review`) are skipped. So are the append-only and
  sample/real isolation triggers.
- **Impact:** ATLAS's central promise is that nothing is VERIFIED without an independent review. That
  promise only holds as long as nobody who holds this one password (or runs code as the API) chooses
  to break it. A superuser can also run `COPY … TO PROGRAM` on the database host. No SQL injection
  was found (§3), so today this needs the credentials. That is why it is Medium and not High.
- **Fix:** keep separate roles.
  - An owner role runs migrations only.
  - `atlas_api` gets `SELECT` only, with `NOSUPERUSER NOCREATEROLE NOBYPASSRLS`.
  - `atlas_curator` gets `INSERT` on the import, review and classification tables only. It is not a
    superuser, so it cannot set `session_replication_role`.
  - Compose and `.env.example` give each process its own URL.
  - The test database can keep a superuser: the tests need replica mode for their fixtures.
- **Regression test:** connected as the API role, assert `rolsuper = false`. Assert that
  `SET session_replication_role = replica` raises "permission denied". Assert that `UPDATE evidence`
  raises "permission denied".
- **Status:** OPEN. Needs an owner decision: it changes the deployment and database setup, and it
  must be done before real pilot data is loaded.

### SEC-02 · Medium · No authentication or access control

- **Where:**
  - `backend/app/main.py:12-28`: no auth dependency or middleware. All 12 routes are `GET`
    (listed from `/openapi.json`).
  - The frontend has no sign-in.
  - Compose binds every port to `127.0.0.1` (`docker-compose.yml`, lines with `127.0.0.1:`). That is
    today's only control.
- **Evidence (TESTED):**
  - `curl http://localhost:8063/api/v1/companies` answers without credentials.
  - `docker inspect` shows all three ports bound to `127.0.0.1` only.
- **Impact:** A-6 allows the private pilot "for internal usability testing only, nothing
  published". As soon as testers on other machines need access, anyone who can reach the URL sees
  everything: real unverified pilot figures, evidence and source URLs (see SEC-03). Nothing in the
  code enforces A-6 or the `commercial_usage_status` of a source. Today only "no deployment"
  enforces them.
- **Fix:** before any access from beyond localhost:
  - Put the frontend behind an authenticating layer: a private network such as a VPN, or a reverse
    proxy with TLS and sign-in.
  - Stop publishing the backend's port (the frontend reaches it on the Compose network).
  - Add rate limiting at that layer (SEC-08).
- **Regression test:** a deployment smoke test. A request without credentials gets 401 or 403, or
  cannot connect. The backend port cannot be reached from outside the host.
- **Status:** OPEN. BLOCKED on Q-7 (hosting and budget), an owner decision.

### SEC-03 · Low · The evidence API returns local `file://` paths unfiltered

- **Where:**
  - `backend/app/ingestion/schemas.py:46-49`: `EvidenceUrl` accepts `file://` and `fixture://`, also
    for real (non-sample) evidence.
  - `backend/app/api/v1/schemas.py:122`: `EvidenceOut.source_url` is returned as stored.
- **Evidence (TESTED):**
  - Ran a temporary test against the throwaway database: import a fictional real-source company
    whose evidence is `file:///Users/curator-name/private/annual-report.pdf`, then call
    `GET /companies/{id}/evidence`. It returned `['file:///Users/curator-name/private/annual-report.pdf']`.
  - The test passed and was then deleted.
  - The UI shows only the document title. `SourceLink` links only through `safeHref`.
- **Impact:** a curator's local paths, including the account name and folder layout, can reach
  anyone who can call the API.
- **Fix:** one of these (an owner choice, because it changes the API or importer behaviour):
  - return `source_url` only when `linkable_url` accepts it, and otherwise `null` plus the scheme;
  - or refuse `file://` for real evidence in the importer.
- **Regression test:** the reproduction above, with the assertion reversed.
- **Status:** OPEN.

### SEC-04 · Low · The company website is rendered as a link without `safeHref`

- **Where:** `frontend/src/app/[lang]/companies/[id]/page.tsx:127` uses `href={c.website}`. Every
  other external link goes through `safeHref` (`frontend/src/lib/provenance.ts:14`) or
  `linkable_url`.
- **Evidence (code):**
  - The importer's `Url` type (`backend/app/ingestion/schemas.py:41-44`, `^https?://\S+$`) rules out
    `javascript:` today. It does allow credentials (`https://user:pass@host`).
  - The `companies.website` column has no check constraint, so the only guard is the importer.
- **Impact:** none today. This is a defence-in-depth gap. A future write path that skips the importer
  could store a `javascript:` URL, and React 19 does not block it (it warns only).
- **Fix:** `const site = safeHref(c.website)`, and render the link only when it is set.
- **Regression test:** a unit test that `safeHref` refuses `javascript:` and credentials (these
  exist in `provenance.test.ts`), plus a route-check assertion on the website link.
- **Status:** OPEN (Low; outside the fix scope).

### SEC-05 · Low · No security headers on the frontend

- **Evidence (TESTED):** `curl -sI http://localhost:3063/companies` returns no
  `Content-Security-Policy`, `X-Frame-Options` / `frame-ancestors`, `X-Content-Type-Options` or
  `Referrer-Policy`. It does return `X-Powered-By: Next.js`.
- **Where:** `frontend/next.config.ts:3` (no `headers()`, no `poweredByHeader: false`).
- **Impact:**
  - The site can be framed. The pages are read-only, so clickjacking risk is low.
  - No second line of defence if an XSS bug appears.
  - The full referrer is sent to external document hosts. Note that `rel="noreferrer"` on the
    external links already removes it there.
- **Fix:** `poweredByHeader: false`, plus `headers()` with `frame-ancestors 'none'`, `nosniff` and
  `strict-origin-when-cross-origin`. Add a CSP after testing it with Next's inline scripts.
- **Regression test:** the route check asserts the headers.
- **Status:** OPEN.

### SEC-06 · Low · Third-party actions and base images are pinned by mutable tags

- **Where:**
  - `.github/workflows/backend.yml:34-35`, `frontend.yml:22-23`, `docker.yml:15`:
    `actions/checkout@v7`, `actions/setup-node@v7`, `astral-sh/setup-uv@v10.4.0`.
  - `backend/Dockerfile:1,3`: `python:3.13-slim`, `ghcr.io/astral-sh/uv:0.9`.
  - `frontend/Dockerfile:1,9`: `node:24-alpine`.
  - `docker-compose.yml:8`: `postgres:17-alpine`.
- **Mitigations already in place (VERIFIED in the workflow files):**
  - `permissions: contents: read`.
  - No secrets used.
  - No `pull_request_target`.
  - Dependencies are locked (`uv sync --frozen`, `npm ci` from `package-lock.json`).
- **Impact:** a changed upstream tag runs new code in CI or ships it in an image without a review.
- **Fix:** pin actions to commit SHAs and images to digests, with Dependabot or Renovate to update
  them.
- **Status:** OPEN.

### SEC-07 · Low · Code reaches `main` without review or branch protection

- **Evidence (VERIFIED):**
  - PRs #3 to #12 were merged by the owner's account with 0 recorded reviews (PR #12 above; earlier
    PRs in P2-8.11).
  - `main` is not protected.
- **Impact:** nothing technical stops an unreviewed or red-CI change from landing on `main`. This
  is also the open process items AU-6 and P2-8.11.
- **Fix:** protect `main`: require a PR and the three CI checks, and block force-push. Record a
  human review as each PR's acceptance step.
- **Status:** OPEN. This is an owner action: changing GitHub settings was not authorised in this
  review.

### SEC-08 · Informational · No rate limiting; some reads cost more as data grows

- **Where:** `backend/app/api/v1/catalog.py:464` and `:508`. These compute every ROE/ROA result or
  comparison for the company, then slice the page. The search at `:169-175` runs `ILIKE '%q%'` over
  four columns with no trigram index.
- **Bounds already in place (code):**
  - `q` ≤ 100 characters.
  - `limit` ≤ 100.
  - `offset` ≤ 100 000.
  - `metric` ≤ 64 characters.
  - Frontend fetches time out after 5 s.
- **Impact:** negligible at pilot scale (5 to 30 companies).
- **Fix:** rate limit at the access layer (SEC-02). Push the slicing into SQL only if the data
  grows a lot.
- **Status:** ACCEPTED for the pilot (no change).

### SEC-09 · Informational · API docs on in every environment; health shows the environment

- **Evidence (TESTED):**
  - `/docs`, `/redoc` and `/openapi.json` return 200.
  - `/api/v1/health` returns `"environment":"development","version":"0.1.0"`.
  - Swagger UI loads its scripts from a CDN.
- **Where:** `backend/app/main.py:16`, `backend/app/api/v1/health.py:64`.
- **Fix:** turn docs off when `APP_ENV=production`, or leave them on only behind SEC-02.
- **Status:** OPEN (decide together with SEC-02).

### SEC-10 · Informational · The two-person rule can't prove who the people are

- **Where:** `curator` and `reviewer` are free text. The database only checks that they differ and
  that the reviewer isn't a system name (`ck_verification_reviews_reviewer_is_a_person`,
  `ck_company_classifications_reviewer_is_a_person`).
- **Impact:** one person can type two names. This is by design until a reviewer is appointed (Q-3),
  and authenticated identities would need SEC-02.
- **Status:** a human dependency (Q-3). Recorded, not a code fix.

## 3. Areas assessed

| Area | What was checked | Result |
| --- | --- | --- |
| SQL injection | All queries go through the SQLAlchemy ORM with bound parameters. `grep` for `text(`, `exec_driver_sql` and f-string SQL in `backend/app` finds only constant `server_default`/index expressions in `models.py`. Search escapes `%`, `_` and `\` (`catalog.py:72-75`; tests `test_search_and_filters[*]`). Probe `q=' OR 1=1--` → 0 items | No finding (TESTED) |
| SSRF | The backend makes no outbound requests. Connectors are local files only (`connectors.py`), and source URLs are never fetched. The frontend fetches only `API_URL` (server-only env, no `NEXT_PUBLIC_`), and route ids must match `UUID` first (`companies/[id]/page.tsx:41`, `sectors/[id]/page.tsx:19`) | No finding |
| Path traversal | The only file read is the operator's `python -m app.ingestion import <path>` (trusted CLI). No API reads files | No finding |
| XSS | No `dangerouslySetInnerHTML`, no `innerHTML`. React escapes all text. API errors are JSON (`unknown metric code: <script>…` is returned as `application/json`). External links pass `safeHref`/`linkable_url`, except the website (SEC-04) | SEC-04 (Low) |
| Open redirect | The proxy redirects only to a same-origin path (`routing.ts`). Probes `/vi//evil.com`, `/vi/\evil.com` and `//evil.com` → 308 to `http://localhost:3063/…`. `/en/%2F%2Fevil.com` → 404, and the language-switch link was `/%2F%2Fevil.com` (same origin; checked in a browser) | No finding (TESTED) |
| Authentication / authorisation | There is none. Read-only API. Writes go only through the local CLI, and the database enforces the two-person rule | SEC-02, SEC-10 |
| Information disclosure | The 500 handler returns `{"detail":"Internal server error"}` and logs the stack trace on the server. The health check logs only the exception type. Evidence paths and docs: SEC-03, SEC-09. Secrets: `.env` is git-ignored at every depth; `git grep` for key, token or password assignments finds only templates; CI uses throw-away test credentials | SEC-03, SEC-09 |
| Dependencies | `pip-audit 2.10.1` on `uv export --frozen`: "No known vulnerabilities found". `npm audit`: 0 (all deps), 0 (`--omit=dev`). next 16.4.6, react 19.3.0 | No finding (TESTED) |
| Supply chain | Lockfiles are used (`--frozen`, `npm ci`). Tags are not pinned | SEC-06, SEC-07 |
| Migrations | Five migrations read. The latest only adds `company_classifications`, its triggers and function, and drops them on downgrade. Round-trip `downgrade base` → `upgrade head` and `alembic check` are clean (§5) | No finding (TESTED) |
| DoS / unbounded input | Query bounds as in SEC-08. Import bundles are read whole, CLI only | SEC-08 |
| Containers | Backend runs as uid 10001 and the frontend as `node` (1000). None privileged, no added capabilities. Ports are on `127.0.0.1` only (`docker inspect`). The frontend image is a multi-stage standalone build | No finding (TESTED) |

## 4. Data and privacy controls

| Control | How it is enforced | Evidence | Label |
| --- | --- | --- | --- |
| Sample and real data can't mix | Database triggers (migration `8de09b58f4c2`) and importer checks. Classifications also check (migration `5c1f0a2b7e44`) | `test_sample_and_real_data_never_mix`, isolation tests in `test_classification.py`; 404 passed (§5) | TESTED; weakened by SEC-01 |
| Nothing unverified is shown as verified | Evidence must start `unverified`/`sample` (`atlas_guard_evidence`), and only a review changes it (`atlas_apply_review`). Every figure carries its verification status. ROE/ROA and comparisons carry `input_verification` | Test suite; route check (§5) | TESTED; weakened by SEC-01 |
| No real data published before G1 | Process only: nothing is deployed. The code has no gate (SEC-02) | User stack `atlas` (read only): 0 companies, 0 sources, 0 evidence, migration `31b1317163eb`. Isolated stack: 5 companies, all fictional (`fixture://`, `https://example.test`) | VERIFIED (current state) |
| A classification needs evidence and two people | NOT NULL `evidence_id`; curator ≠ reviewer; reviewer is a person; same-company, not-withdrawn evidence (trigger); append-only | 24 tests in `test_classification.py` | TESTED |
| Sources with unclear rights stay restricted | Every source is `unknown` (`data/SOURCES.md`). Never sourced from aggregators (A-6). The API does not filter on `commercial_usage_status` | Data sources in both stacks: none real | VERIFIED (process); no technical gate |
| No real data invented | This review imported nothing into any persistent database. The temporary SEC-03 test used fictional `Test Co 9` in the throwaway database | — | VERIFIED |

## 5. Verification run for this review (local, branch `security/p2-6-12-review` = `8692a0c`)

All commands ran on 2026-11-26.

**Backend**

The commands ran in `backend/`, against a throwaway PostgreSQL 17 on `127.0.0.1:5464` (container
`atlas-sec-testpg`, random password).

| Command | Result | Label |
| --- | --- | --- |
| `uv sync --frozen` | "Checked 41 packages" | TESTED |
| `uv run ruff check .` | "All checks passed!" | TESTED |
| `uv run ruff format --check .` | "48 files already formatted" | TESTED |
| `uv run mypy app tests migrations/env.py` | "Success: no issues found in 43 source files" | TESTED |
| `uv run pytest -q` | **404 passed**, 1 warning, 13.81 s (includes the migration round-trip test) | TESTED |
| `uv run alembic upgrade head && uv run alembic check` | "No new upgrade operations detected." | TESTED |
| `alembic downgrade base && alembic upgrade head && alembic current`, then `alembic check` | `5c1f0a2b7e44 (head)`, then "No new upgrade operations detected." | TESTED |
| `pip-audit -r <uv export>` | "No known vulnerabilities found" | TESTED |

**Frontend**

The commands ran on a clean `git archive HEAD` copy, like CI.

| Command | Result | Label |
| --- | --- | --- |
| `npm ci` | "found 0 vulnerabilities" | TESTED |
| `npm run lint` | no output (clean) | TESTED |
| `npm run typecheck` | exit 0 | TESTED |
| `npm test` | tests 36, pass 36, fail 0 | TESTED |
| `npm run build` | "Compiled successfully" | TESTED |
| `npm audit` / `npm audit --omit=dev` | 0 / 0 | TESTED |

In the working copy, `npm run typecheck` **fails**. The cause is stale, git-ignored
`frontend/.next/dev/types` from an earlier `next dev`, and a clean checkout passes. Delete
`frontend/.next/dev` locally. This is not a security issue. The folder was left in place because it
isn't this review's to delete.

**Docker and routes**

The isolated project `atlasws44` uses ports 5463, 8063 and 3063. Its sources match `HEAD` (checked
with `diff -rq`), and it holds fictional data. The user's `atlas` stack was not touched.

| Command | Result | Label |
| --- | --- | --- |
| `docker compose config -q`, `build`, `up -d --wait` | db, backend and frontend healthy | TESTED |
| `curl /api/v1/health` | `{"status":"ok",…,"database":{"status":"ok"}}`; frontend `/` → 200 | TESTED |
| `BASE_URL=http://localhost:3063 node scripts/check-routes.mjs` | "route check passed (backend online)". Vietnamese and `/en` routes | TESTED |
| same with `EXPECT=offline`, backend stopped | "route check passed (backend offline)". The backend was started again afterwards | TESTED |

**Not tested**

- Container image CVE scanning (no scanner installed).
- A dynamic scan with DAST tools.
- TLS or a reverse proxy (none exist).
- Load testing.
- An independent human review.

## 6. Outstanding human decisions and external blockers

| Item | Who | Blocks |
| --- | --- | --- |
| SEC-01: database role separation | Owner (approve the setup change) | Loading real pilot data |
| SEC-02: pilot access method (VPN or proxy with sign-in), hosting and budget (Q-7) | Owner | Any pilot access from beyond localhost |
| SEC-03 / SEC-04 / SEC-05 / SEC-06 / SEC-09: approve Low fixes | Owner | Nothing (defence in depth) |
| SEC-07: branch protection, recorded human review (AU-6, W4-H2, P2-8.11) | Owner and a reviewer | Merge discipline |
| Independent reviewer (Q-3) | Owner | Any VERIFIED record (G2) |
| G1 legal opinion | External (lawyer) | Any public display of real data |
