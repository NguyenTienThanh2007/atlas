# Phase 0 checklist

Last verified: 2026-11-22, macOS (Docker 29.6.1, Node 24.16, uv-managed Python 3.13.15).
Branch: `phase-0-foundation` (uncommitted at time of writing).

Status legend: **PASS** (verified by running it) · **FAIL** · **BLOCKED** (couldn't run, reason
given) · **NOT STARTED**.

## A. Repository foundation

| Item | Status | Verification | Result | Files |
| --- | --- | --- | --- | --- |
| Repo inspected before changes | PASS | `git log`, `find . -type f` | Only `README.md` and an initial commit existed | — |
| Monorepo structure (frontend / backend / data / infra / docs) | PASS | `ls` | All present | `frontend/ backend/ data/ infra/ docs/` |
| `.gitignore` | PASS | `git check-ignore --no-index -q` on 10 `.env*` paths (root, `backend/`, `frontend/`, `infra/postgres/`, `data/sub/`, `a/b/c/`) and 4 `.env.example` paths | All 10 ignored; all 4 `.env.example` allowed (`frontend/.env.example` was wrongly ignored before the pre-commit review, now fixed) | `.gitignore`, `frontend/.gitignore` |
| `.env.example` | PASS | `docker compose --env-file .env.example -p atlasph up --build --wait` on a fresh volume, then `pytest` with the placeholder password | Health 200, frontend 200, 6 passed; a wrong password makes the DB test fail, so the password is enforced | `.env.example` |
| No secrets committed | PASS | Staged path scan + `git grep --cached` for password/secret/token/key patterns | Only the documented placeholder in `.env.example` and the ephemeral CI service password `atlas_ci` | — |
| Dependencies documented and locked | PASS | `uv sync --frozen` / `npm ci` in clean copy | Both installed from lockfiles | `backend/uv.lock`, `frontend/package-lock.json` |

## B. Frontend

| Item | Status | Verification | Result | Files |
| --- | --- | --- | --- | --- |
| App runs (dev) | PASS | `npm run dev`, `curl` each route | `/`, `/sectors`, `/companies`, `/watchlist` → 200; `/nope` → 404 | `frontend/src/app/**` |
| App runs (production container) | PASS | `docker compose up`, `curl :3000/` | 200 | `frontend/Dockerfile` |
| TypeScript strict | PASS | `tsconfig.json` `"strict": true`; `npm run typecheck` | exit 0 (also on a fresh checkout) | `frontend/tsconfig.json`, `package.json` |
| Tailwind works | PASS | Visual check in browser | Theme tokens render (navy, brass, glass) | `src/app/globals.css` |
| ATLAS branding | PASS | Browser screenshot | Wordmark, palette, Fraunces + IBM Plex Sans | `layout.tsx`, `shell.tsx` |
| Responsive sidebar | PASS | Browser at 375×812 and 1440×900 | Mobile drawer opens/closes (button, link click, Escape); desktop sticky sidebar; closed drawer not focusable | `components/shell.tsx` |
| Discovery workspace | PASS | Browser | Discover page with empty state and world-view placeholder section | `src/app/page.tsx` |
| Navigation functional | PASS | Clicked through in browser (dev and prod) | Active state via `aria-current`; client navigation works | `components/shell.tsx` |
| Empty states | PASS | Browser | Every section explains why it's empty and what fills it | `components/empty-state.tsx` |
| Live API status | PASS | Browser + `curl` with DB stopped | Shows "API and database online" / "API online, database unreachable" | `components/api-status.tsx` |
| No console errors | PASS | Fresh browser tab against production build, navigated two pages | "No console logs" | — |
| Lint | PASS | `npm run lint` | exit 0, no warnings | `eslint.config.mjs` |
| Production build | PASS | `npm run build` | Compiled; 5 routes partially prerendered | — |
| Dependency audit | PASS | `npm audit --omit=dev` | 0 vulnerabilities | — |

## C. Backend

| Item | Status | Verification | Result | Files |
| --- | --- | --- | --- | --- |
| FastAPI app | PASS | `uvicorn app.main:app` | Serves on :8000 | `backend/app/main.py` |
| Env-based config | PASS | Tests set `DATABASE_URL`/`APP_ENV`; compose injects its own | `environment` field reflects `test` / `development` | `app/config.py` |
| DB connection configured | PASS | Health check | `latency_ms` reported | `app/db.py` |
| SQLAlchemy base | PASS | `alembic check` reads `Base.metadata` | "No new upgrade operations detected" | `app/db.py` |
| Alembic configured | PASS | `alembic upgrade head`, `alembic current` | `2fa53e542881 (head)` | `alembic.ini`, `migrations/` |
| `/api/v1` prefix | PASS | `curl /api/v1/health` | 200 | `app/main.py` |
| Health checks the real DB | PASS | Live: stopped `db` container mid-run | 200 → 503 → 200 after restart | `app/api/v1/health.py` |
| Correct status codes | PASS | pytest | 200 ok, 503 DB down, 405 wrong method, 404 unknown, 500 generic | `tests/test_health.py` |
| Error handling | PASS | pytest `test_unhandled_error_returns_generic_500` | No internals leaked; DB errors log the type only | `app/main.py` |
| Lint / format | PASS | `ruff check .`, `ruff format --check .` | All checks passed | `pyproject.toml` |
| Type check | PASS | `mypy app tests migrations/env.py` (strict) | No issues in 12 files | — |
| API tests | PASS | `uv run pytest` | 6 passed, 1 warning (see LOW-1) | `tests/` |

## D. Database and Docker

| Item | Status | Verification | Result | Files |
| --- | --- | --- | --- | --- |
| PostgreSQL service | PASS | `docker compose ps` | `db` healthy (pg_isready healthcheck) | `docker-compose.yml` |
| Compose valid | PASS | `docker compose config -q` | exit 0 | — |
| Env vars used correctly | PASS | Compose requires `POSTGRES_*` (`:?` guards); backend `DATABASE_URL` built from them | Stack starts from `.env` | — |
| Persistence configured | PASS | Named volume `atlas_pgdata` | — | — |
| App connects to Postgres in Docker | PASS | `curl :8000/api/v1/health` against containers | 200, `database: ok` | — |
| Migrations run | PASS | Backend container log | `alembic upgrade head` ran before uvicorn | `backend/Dockerfile` |
| Fresh DB init | PASS | Isolated project `-p atlasfresh` on a new volume | Migrated to head; `atlas_test` created; health 200; volume removed afterwards | `infra/postgres/init/` |
| Restart keeps data | PASS | Inserted marker row → `docker compose down` → `up` → selected it | `survives-restart` and `alembic_version` intact; marker table dropped afterwards | — |
| Containers non-root | PASS | `whoami` in containers | `atlas`, `node` | Dockerfiles |
| Ports bound to localhost only | PASS | compose `127.0.0.1:` bindings | — | — |

## E. Testing and quality

| Item | Status | Evidence |
| --- | --- | --- |
| Backend tests | PASS | 6/6 against real Postgres (also from a clean copy) |
| Frontend lint / typecheck / build | PASS | All exit 0 (also from a clean copy) |
| Docker config | PASS | `config -q`, `build`, `up --wait` all succeed |
| Migration checks | PASS | Round-trip test (upgrade → base → head) + `alembic check` |
| No known critical security issues | PASS | Self-review below; npm audit clean |
| No dead code | PASS | Removed unused `get_sessionmaker`, starter SVGs, scaffold README |

## F. CI/CD

| Item | Status | Verification | Result | Files |
| --- | --- | --- | --- | --- |
| Backend workflow | PASS (local) | Same commands run locally | lint, mypy, pytest with Postgres service, alembic check | `.github/workflows/backend.yml` |
| Frontend workflow | PASS (local) | Same commands run locally on a fresh checkout | lint, typecheck, build | `.github/workflows/frontend.yml` |
| Docker workflow | PASS (local) | Steps run in isolated project `-p atlasci` | `up --wait` healthy; health and frontend 200 | `.github/workflows/docker.yml` |
| Workflow syntax | PASS (YAML parse) | `yaml.safe_load` on all three | Parses; jobs present | — |
| actionlint | BLOCKED | `docker run rhysd/actionlint` was denied by the session's permission policy | Not run | — |
| Workflows executed on GitHub | BLOCKED | Needs a push, which needs the owner's authorization | Not run | — |

## G. Documentation

| Item | Status | Verification |
| --- | --- | --- |
| README.md | PASS | Quick start commands run as written |
| docs/ARCHITECTURE.md | PASS | Reflects the code as built |
| docs/DEVELOPMENT.md | PASS | Setup and check commands run in a clean copy of committable files |
| `.env.example` | PASS | Used directly by every run above |
| Setup tested | PASS | Clean-copy run caught a real bug (typecheck failed on a fresh clone), which is now fixed |
| Known limitations | PASS | README "Known limitations" |

## Pre-commit review of staged changes (2026-11-22)

| Check | Status | Verification | Result |
| --- | --- | --- | --- |
| Shared default DB password replaced | PASS | `git grep --cached <previous default>` (after re-staging) | No matches in any staged file. `.env.example` now uses the placeholder `local_dev_only_change_me`, with inline rules (URL-safe characters, same value in 3 places, applied only on first volume init) |
| Password setup documented consistently | PASS | Read through | `docs/DEVELOPMENT.md` "Database password" section (set, keep consistent, change on an existing volume via `ALTER USER`, or reset with `down -v`); troubleshooting row for auth failures; `docker-compose.yml` header comment; README note |
| Nested `.env` ignored, `.env.example` allowed | PASS | `git check-ignore --no-index -q` probes (see A) | 10/10 ignored, 4/4 templates allowed |
| No secrets, dumps, logs, `.venv`, `node_modules` or build output staged | PASS | Staged path scan for `.env`, `.venv/`, `node_modules/`, `.next/`, `__pycache__`, `*.pyc`, `*.log`, `*.sql`, `*.dump`, `*.sqlite`, `*.db`, `*.pem`, `*.key`, `tsbuildinfo`, `.DS_Store`, `coverage`, `dist/`, `build/` | Only hit: `.env.example` (intended). 54 staged files, all source, config, lockfiles, docs or `favicon.ico` |
| No legitimate source removed | PASS | `git diff --cached --diff-filter=D --name-only` | No deletions |
| Checks rerun after the changes | PASS | ruff, ruff format, mypy, pytest (6 passed), `alembic check`, npm lint/typecheck/build, `docker compose config -q` (with `.env` and with `.env.example`), workflow YAML parse, existing stack health 200 | All pass |

Your existing local `.env` and `atlas_pgdata` volume still use the previous password. They are consistent with each other and unaffected, since `.env` is git-ignored and never staged.

## Self-review findings

| ID | Severity | Finding | Resolution |
| --- | --- | --- | --- |
| H-1 | HIGH | `npm run typecheck` failed on a fresh clone (`LayoutProps` is generated) | Fixed: `next typegen && tsc --noEmit` |
| M-1 | MEDIUM | Mobile drawer was translucent and covered the header | Fixed: solid drawer on mobile, header above it |
| M-2 | MEDIUM | Off-screen drawer links were keyboard-focusable | Fixed: `max-lg:invisible` when closed; Escape closes |
| M-3 | MEDIUM | Host port 5432 clashed with an existing local Postgres | Fixed: default host port 5433 |
| L-1 | LOW | Starlette warns that `httpx` for `TestClient` is deprecated in favour of `httpx2` | Open. Adding `httpx2` was held back as an unverified new dependency. Revisit when FastAPI docs adopt it. |
| L-2 | LOW | The API status shows "API unreachable" if a proxy returns non-JSON | Acceptable for Phase 0 |
| L-3 | LOW | `app_version` is duplicated in `pyproject.toml` and `config.py` | Keep in sync manually until release tooling exists |

No CRITICAL or HIGH findings remain open.

## Completion gate

| # | Criterion | Status |
| --- | --- | --- |
| 1 | Compose starts PostgreSQL | PASS |
| 2 | Backend starts | PASS |
| 3 | Health checks the database | PASS |
| 4 | Frontend starts | PASS |
| 5 | Frontend production build | PASS |
| 6 | Backend tests pass | PASS |
| 7 | Frontend checks pass | PASS |
| 8 | Migrations work | PASS |
| 9 | Docs reproducible | PASS |
| 10 | No open critical/high issues | PASS |

Open items outside the gate: the GitHub Actions run and actionlint (both BLOCKED above).
