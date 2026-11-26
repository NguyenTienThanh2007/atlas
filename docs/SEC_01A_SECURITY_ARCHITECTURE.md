# SEC-01A: security architecture (design only)

**Status: DESIGN FOR OWNER REVIEW. Nothing here is approved or implemented.** Every
recommendation is a **PROPOSAL**. Decisions are listed in
[SEC_01A_IMPLEMENTATION_PLAN.md](SEC_01A_IMPLEMENTATION_PLAN.md) §1. Threats:
[SEC_01A_THREAT_MODEL.md](SEC_01A_THREAT_MODEL.md).

| | |
| --- | --- |
| Baseline inspected | `main` @ `aa3218a0e0bc07fe4f0ce7f844983f42c68a408b` (PR #13 merge, 2026-11-26T09:37:12Z, 0 reviews). Branch `security/sec-01a-design` was cut from it; the working tree was clean |
| CI on the baseline | Docker success. Backend and Frontend did not run: PR #13 changed docs only, and both workflows have path filters (VERIFIED, `gh run list`) |
| Author | An AI assistant. This is not an independent human review, so AU-6, W4-H2, P2-8.11 and SEC-07 stay open |
| Pilot companies | Called Company 1–5 only. The private G2 workspace was not opened |

The labels are those of the brief: **VERIFIED FACT** (read in the repository or on GitHub),
**TESTED FACT** (a command ran; its output is quoted), **INFERENCE**, **PROPOSAL**, **OPEN QUESTION**
and **HUMAN DEPENDENCY**.

## 0. Summary

1. **Splitting the superuser into three roles is not enough.** The proposed fix in the SEC-01 row of
   the remediation checklist would leave two bypasses that need no superuser at all. Both were
   TESTED on a disposable database (§2.3):
   - **P5:** any role allowed to record a review can set evidence to `verified` with **zero** review
     rows.
   - **P6e:** a curator role can store a classification that cites **another company's** evidence.
2. **The two-person rule is one person typing two names.** Today one session submits both
   `curator` and `reviewer` (P7). The database cannot tell who is at the keyboard.
3. **Recommended model (PROPOSAL):**
   - one owner role that is never used at runtime;
   - a read-only API role;
   - **one database login per human**, authenticated by PostgreSQL itself;
   - writes only through `SECURITY DEFINER` procedures, which take the actor from `session_user`
     and never from input;
   - a curator-then-reviewer flow in two steps, by two different logins;
   - tamper-evident review history, plus an integrity check that runs independently.
4. **What no design here prevents:** a superuser, or the owner role, can still rewrite anything.
   Against them the design only *detects* tampering (§9). The owner and the operator of the host
   must be trusted, or watched by someone else.

## 1. Current state

### 1.1 Components and credentials (VERIFIED FACT)

| Component | Where | Database principal |
| --- | --- | --- |
| PostgreSQL 17 (`postgres:17-alpine`) | `docker-compose.yml:7-22`, port `127.0.0.1:${POSTGRES_PORT}` (line 15) | Image superuser `${POSTGRES_USER}` (`atlas`) |
| Backend API (FastAPI) | `docker-compose.yml:24-45`, `127.0.0.1:${BACKEND_PORT}` (line 34) | The same superuser: `DATABASE_URL` is built from `POSTGRES_USER`/`POSTGRES_PASSWORD` (line 30) |
| Migrations and reference seed | `backend/Dockerfile:20`: `alembic upgrade head && python -m app.ingestion reference && exec uvicorn …` in the **API container** at every start | The same superuser |
| Import, review and classify CLI | `backend/app/ingestion/__main__.py` (`import`, `review`, `reviews`, `classify`). It runs on the operator's machine with `.env`'s `DATABASE_URL` (`backend/app/config.py:19`, `.env.example:16`) | The same superuser (on the host: `atlas@localhost:5433`) |
| Frontend (Next.js) | `docker-compose.yml:47-55`, `127.0.0.1:${FRONTEND_PORT}`. Server-side fetches use `API_URL` (`frontend/src/lib/api.ts:12`) | None |
| Test database | `TEST_DATABASE_URL`. The tests use `SET LOCAL session_replication_role = replica` (`backend/tests/test_sample_isolation.py:210`), so the test role must be a superuser | The test superuser |
| CI | `.github/workflows/backend.yml:17-27`: the service container runs `atlas`/`atlas_ci` as superuser | The test superuser |

Other facts:
- Authentication: none (VERIFIED: `backend/app/main.py:12-28` registers no auth dependency; no
  file in `frontend/src` mentions auth, sessions or cookies). All 12 API routes are `GET`. The
  review tool is deliberately CLI-only (`tests/test_verification.py:510`
  `test_no_public_review_api`).
- Engine and pool: `backend/app/db.py:24-31`, `create_engine(..., pool_pre_ping=True)`. There is no
  external pooler.

### 1.2 Enforcement inventory (TESTED FACT)

The schema was migrated to `5c1f0a2b7e44` on a disposable database (`atlas-sec01a-testpg`,
127.0.0.1:5464, fictional data) and the catalogue was read.

| Control | Object | Migration | Fires on | Security mode |
| --- | --- | --- | --- | --- |
| Evidence starts `unverified`/`sample`; content is immutable; status changes only when `pg_trigger_depth() >= 2` | `atlas_guard_evidence` / `evidence_guard` | `31b1317163eb` (`…verification_reviews_and_figure_.py:219-247`) | BEFORE INSERT OR UPDATE on `evidence` | INVOKER, no `search_path` |
| A review applies the transition matrix, checks `from_status`, and runs `UPDATE evidence` | `atlas_apply_review` / `verification_reviews_apply` | `31b1317163eb` (lines 170-200) | BEFORE INSERT on `verification_reviews` | INVOKER, no `search_path` |
| Reviews are append-only | `atlas_reject_review_change` | `31b1317163eb` (lines 201-215) | BEFORE UPDATE OR DELETE (row) | INVOKER |
| Curator ≠ reviewer, reviewer is "a person" | CHECK `ck_verification_reviews_*` | `31b1317163eb` (lines 111-127) | INSERT | String comparison |
| History is append-only | `atlas_reject_history_change` | `981ec5176312` (`…domain_model.py:562-573`), reused by `5c1f0a2b7e44` | BEFORE UPDATE OR DELETE (row) on `financial_statements`, `financial_metrics`, `company_classifications` | INVOKER |
| Sample/real isolation | `atlas_isolate_{statement,evidence,company,security}`, `atlas_company_of_evidence` | `8de09b58f4c2` | INSERT/UPDATE on `financial_statements`, `evidence`; UPDATE OF `is_sample` on `companies`; UPDATE OF `company_id` on `securities` | INVOKER, no `search_path` |
| Classification evidence checks | `atlas_check_classification` | `5c1f0a2b7e44` (lines 112-161) | BEFORE INSERT on `company_classifications` | INVOKER, no `search_path` |
| Real figures need a page and their as-reported value | `atlas_require_figure_provenance` | `31b1317163eb` (lines 249-271) | BEFORE INSERT on `financial_metrics` | INVOKER |

More catalogue facts:
- **Every table and function is owned by the superuser `atlas`.**
- Table ACLs are defaults: no grants to anyone else.
- No RLS.
- Schema `public`: `pg_database_owner=UC`, PUBLIC `U`, so PUBLIC cannot CREATE there.
- Database ACL: default, so **PUBLIC has CONNECT and TEMP**.
- No sequences (all keys are UUIDs).

What the inventory does not cover (VERIFIED FACT, from the trigger list):
- No `TRUNCATE` trigger anywhere.
- No `DELETE` guard on `evidence`, `companies`, `securities`, `data_sources`, `exchanges`,
  `sectors` or `ingestion_runs`.
- `companies` and `securities` are guarded only on `is_sample` and `company_id`.

### 1.3 A display field set by the application, not by the database

The company page shows "Last verified" from `companies.last_verified_at`
(`frontend/src/app/[lang]/companies/[id]/page.tsx:134`).

- That value is written by **application code** (`backend/app/ingestion/review.py:56-70`,
  `_stamp_last_verified`), not by the database. No trigger guards the column (VERIFIED FACT).
- `docs/VERIFICATION_WORKFLOW.md` §4 says "the database sets" it. That sentence is inaccurate.
- INFERENCE: any role with `UPDATE` on `companies` or `securities` could show a "Last verified"
  date with no review behind it.

## 2. Why "three roles" is not enough

### 2.1 What NOSUPERUSER does fix (TESTED FACT, probes P1, P2, P8, P10)

A role without superuser:
- cannot set `session_replication_role`: "permission denied to set parameter";
- cannot write tables it was not granted;
- cannot `TRUNCATE` or `ALTER TABLE … DISABLE TRIGGER` a table it does not own ("must be owner of
  table evidence");
- cannot `COPY … TO PROGRAM`, which needs `pg_execute_server_program`;
- cannot `CREATE` in `public`.

### 2.2 What it does not fix: invoker trigger functions force broad grants

- **P3a (TESTED):** a role with only `INSERT` on `verification_reviews` and `SELECT` on `evidence`
  cannot record a review. The trigger's `SELECT … FOR UPDATE` and `UPDATE evidence` run with the
  *caller's* rights. So every reviewer role needs `UPDATE` on `evidence`.
- **P6c (TESTED):** a role with only `SELECT` on `companies` cannot record a classification. The
  trigger's `SELECT … FOR SHARE` needs an `UPDATE` grant on `companies`.

### 2.3 Bypasses with those grants (TESTED FACT)

Every probe below ran in a transaction that was rolled back, on the disposable database only.
Afterwards: 2 evidence rows `unverified`, 0 reviews, 0 classifications, test roles dropped.

| Probe | Role (no superuser) | Action | Result |
| --- | --- | --- | --- |
| **P4** | reviewer, with `UPDATE` on `evidence` | `UPDATE evidence SET verification_status='verified'` | Refused by the guard ("changes only through verification_reviews"). The depth-1 guard works |
| **P5** | the same | `CREATE TEMP TABLE poke`, then a `pg_temp` trigger function that updates `public.evidence`, then `INSERT INTO poke` | **`verified`, with 0 review rows.** The UPDATE runs at trigger depth 2, which the guard treats as "from a review" |
| **P6d** | curator, with `INSERT` on `company_classifications`, `SELECT` on `evidence`/`companies` and `UPDATE(is_sample)` on `companies` | Classify Company A citing Company B's evidence | Refused ("must cite evidence about that company") |
| **P6e** | the same | First `CREATE TEMP TABLE evidence(...)` holding a fake row, then the same insert | **Stored.** The unqualified `FROM evidence` in `atlas_check_classification` resolved to `pg_temp.evidence`, because `pg_temp` is searched first. The foreign key still checks the real row, but the semantic checks read the fake one |
| **P7** | reviewer | One session inserts `curator='Same Person'`, `reviewer='Same Person (2)'` | Accepted, `verified` |
| **P9** | a **non-superuser** that owns `evidence` | `ALTER TABLE evidence DISABLE TRIGGER evidence_guard; UPDATE …` | `verified`. Owning the table is enough to bypass it |
| **P9b** | a non-superuser that owns `verification_reviews` | `TRUNCATE verification_reviews` | All review history gone. Row triggers don't fire on TRUNCATE |
| **P11** | any role granted `DELETE` on `evidence` | `DELETE` unreviewed evidence | Deleted. There is no DELETE guard |

INFERENCE: the same `pg_temp` shadowing works against every INVOKER trigger function with
unqualified table names, including the sample/real isolation functions and `atlas_apply_review`.
Only P6e was run.

**Conclusion:** the security-critical functions must be `SECURITY DEFINER`, owned by a role nobody
logs in as, with a pinned `search_path` and schema-qualified names. Runtime roles must hold **no**
`UPDATE`, `DELETE` or `TRUNCATE` on protected tables, and no `TEMP`. Writes go only through
procedures.

## 3. Recommended PostgreSQL role model (PROPOSAL)

### 3.1 Principals

| Principal | LOGIN | Attributes | Member of | Purpose | Where its secret lives |
| --- | --- | --- | --- | --- | --- |
| `postgres` (bootstrap) | yes | SUPERUSER | — | Cluster creation, extensions, the event trigger, break-glass | Owner only, offline; never in `.env` or a container environment after bootstrap |
| `atlas_owner` | **no** | NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS | — | Owns the schema, tables and functions; the security-definer identity | No password (NOLOGIN) |
| `atlas_migrator` | yes | NOSUPERUSER NOCREATEROLE, **NOINHERIT** | `atlas_owner` (it must `SET ROLE atlas_owner`) | Runs Alembic and the reference seed in a one-shot job | Only the migration job's secret |
| `atlas_api` | yes | NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS NOINHERIT, `default_transaction_read_only=on`, `statement_timeout`, connection limit | — | Serves the read-only API | Only the backend container |
| `atlas_curators` | **no** | NOSUPERUSER | — | Group: EXECUTE on the curation procedures | — |
| `atlas_reviewers` | **no** | NOSUPERUSER | — | Group: EXECUTE on the review procedures | — |
| `p_<id>` (one per human) | yes | NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS **NOINHERIT**, a connection limit, `VALID UNTIL` | `atlas_curators` and/or `atlas_reviewers` | A person's own database identity | Each person's own credential (§5.3). Never shared, never in `.env` |

Notes on this model:
- **Why `atlas_owner` is NOLOGIN and the migrator NOINHERIT.** A leaked migrator password then
  needs an explicit `SET ROLE` to act as owner, and that shows in the logs. It still *can* act as
  owner, so migration credentials are as sensitive as the owner itself (T-15 in the threat model).
- **Why the person roles are NOINHERIT.** The procedures check membership with
  `pg_has_role(session_user, 'atlas_reviewers', 'MEMBER')`, so no table rights flow through
  inheritance.
- **No separate `atlas_curator` service login.** A shared curator login would again record "the
  service" rather than a person (§4).

### 3.2 Database-wide hardening (PROPOSAL)

Each item below fixes a tested gap.

- `REVOKE ALL ON DATABASE atlas FROM PUBLIC`, then `GRANT CONNECT` to the roles that need it. This
  removes **TEMP**, which closes P5 and P6e as defence in depth.
- `REVOKE ALL ON SCHEMA public FROM PUBLIC`; `GRANT USAGE` only to the runtime roles.
  `ALTER DEFAULT PRIVILEGES FOR ROLE atlas_owner REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC`, and
  `REVOKE EXECUTE` on the existing functions. Functions are EXECUTE-to-PUBLIC by default.
- Every security function becomes:
  - `SECURITY DEFINER`, owned by `atlas_owner`;
  - `SET search_path = pg_catalog, public, pg_temp` (with `pg_temp` explicitly last);
  - written with **schema-qualified** names (`public.evidence`).

  Trigger functions that keep INVOKER rights also get the pinned `search_path`.
- `atlas_guard_evidence`: replace `pg_trigger_depth() < 2` with "the status may change only when
  `current_user = 'atlas_owner'`". Only the definer procedures run as `atlas_owner`, and no runtime
  role holds `UPDATE` on `evidence`. Keep the immutability check.
- Add `BEFORE TRUNCATE` statement triggers that refuse truncation. Add `BEFORE DELETE` guards on
  `evidence`, `companies`, `securities`, `data_sources`, `ingestion_runs` and the new identity and
  audit tables. Neither stops the owner, but they catch mistakes and force a visible
  `DISABLE TRIGGER`.
- Never `GRANT SET ON PARAMETER session_replication_role`. A test asserts that `pg_parameter_acl`
  has no row for it.
- Optional, needs the bootstrap superuser: an **event trigger** on `ddl_command_end` that appends
  every DDL command (including `ALTER TABLE … DISABLE TRIGGER`) to an audit table and to the server
  log. A superuser can drop it; it is for detection (T-13).
- `log_connections`, `log_disconnections` and `log_statement = 'ddl'` on. Consider `pgaudit` for
  role and DDL logging; it is an OPEN QUESTION whether the extension is available on the chosen
  host (Q-7).
- RLS: **not recommended** for the current tables. All rows are meant for public reading. RLS is
  bypassed by the owner unless `FORCE` is set, and it would add complexity without closing a path
  above. Revisit if per-tenant or private data appears.

### 3.3 Permission matrix (PROPOSAL)

Actual tables from the schema at `5c1f0a2b7e44`. In the matrix:
- S/I/U/D/T are SELECT, INSERT, UPDATE, DELETE and TRUNCATE.
- `—` means none.
- "via proc" means only through the `SECURITY DEFINER` procedures in §4.3, which run as
  `atlas_owner`.

`atlas_owner` owns every table and so holds every right. It is shown once in the last column.
`atlas_migrator` has no rights of its own and acts only through `SET ROLE atlas_owner`.

| Table | `atlas_api` | `p_*` curator (via `atlas_curators`) | `p_*` reviewer (via `atlas_reviewers`) | Owner |
| --- | --- | --- | --- | --- |
| `evidence` | S (via view, §3.4) | I via proc (`atlas_submit_evidence` / import) | U of status **via proc only** | all |
| `verification_reviews` | S (view, without internal identity columns) | — | I via proc (`atlas_record_review`) | all |
| `company_classifications` | S | I (proposal row) via proc | I (approval) via proc | all |
| `financial_statements` | S | I via import proc | — | all |
| `financial_metrics` | S | I via import proc | — | all |
| `ingestion_runs` | — (not exposed today) | I and own-row status via import proc | — | all |
| `data_sources` | S | I via import proc (terms can't change; existing rule) | — | all |
| `companies` | S | I via import proc. U: none. `last_verified_at` is derived, §4.4 | — | all |
| `securities` | S | I via import proc | — | all |
| `exchanges`, `sectors` | S | — (reference seed runs as owner in the migration job) | — | all |
| `alembic_version` | — | — | — | all |
| New `principals`, `principal_role_events` | — | S of own row (view) | S of own row (view) | all |
| New `security_audit_log` | — | — | — | I via procs and the event trigger; no U/D/T for anyone except the owner |

- **No runtime role holds U, D or T on any table. EXECUTE is granted only on the named
  procedures**, never to PUBLIC.
- The import path is today a Python transaction that writes many tables (`importer.py`, savepoint
  per record at lines 124-138). It needs either one `atlas_import_bundle(jsonb)` procedure or
  narrow per-table procedures. That is an OWNER DECISION (D4); the plan recommends per-record
  procedures so the existing Python validation stays.

### 3.4 Views or tables for the API?

**PROPOSAL: views in a dedicated `api` schema** for `evidence` and `verification_reviews`, and for
every table that gains identity columns. Plain `SELECT` grants for the reference tables.

- Views let the API never see `created_by` principal ids, local paths (SEC-03: the view returns
  `source_url` only when it is http(s)) or audit columns. A compromised API can then leak less.
- Make them `security_barrier` views owned by `atlas_owner`. Keep the existing column names, so the
  ORM read models change only their schema (backward compatibility, plan §4).

## 4. Human identity and two-person verification (PROPOSAL)

### 4.1 Options

| # | Option | Security | Ops complexity | Auditability | Credential mgmt | Local dev | Docker | Future hosting | Revocation | Insider threat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **Application-authenticated identity** (OIDC in a curation web service that holds one DB login) | The DB trusts the service. A compromised service can write any actor id | Medium: an IdP and a web write surface (new) | Good in app logs; DB records only what the service says | IdP | Needs a local IdP or a stub | Easy | Good | IdP-side, immediate | **Weak:** whoever controls the service impersonates anyone |
| 2 | **Separate shared reviewer credential** | Proves only "someone who knows the reviewer password" | Low | Poor (shared) | One shared secret | Easy | Easy | Poor | Rotate for everyone | **Weak:** the curator can learn it |
| 3 | **A database role per human** | The DB authenticates the person; `session_user` can't be forged by SQL | Low at pilot scale (2–3 people) | Strong: the identity is in every row and in server logs | One secret per person (SCRAM password or client certificate) | Easy (`psql`/CLI per role) | Needs DB reachable by the person's tool (§6) | Fine for a few curators; awkward at dozens | `ALTER ROLE … NOLOGIN` and revoke membership, immediate | Medium: the DB superuser and owner can still impersonate |
| 4 | **Stored procedures with an identity context** (`SET atlas.actor = …`) | **Unsafe alone:** custom settings can be set by any session | Low | Only as good as whoever sets the context | — | Easy | Easy | — | — | **Weak** |
| 5 | **Hybrid:** IdP identity in a service that connects per user (`SET ROLE p_x` from a gateway login that is a member of every person role), plus DB-enforced procedures | Strong against the curator. A compromised gateway can `SET ROLE` to anyone | High | Strong (DB `current_user` and IdP log) | IdP and a gateway secret | Hard | Medium | Best for a web review UI | IdP and DB | Medium: the gateway is a single point of trust |

### 4.2 Recommendation

**For the private pilot (PROPOSAL): option 3 combined with definer procedures that read
`session_user`, keeping the CLI-only review tool (EX-2).**

Why this one:
1. It is the only option where **the database itself** proves which login acted, without trusting
   an application process. PostgreSQL authenticates `session_user`, and no SQL inside the session
   can change it (`SET ROLE` changes `current_user`, not `session_user`).
2. It adds no web write surface. The public API stays read-only, which matches
   `test_no_public_review_api`.
3. It suits 2–3 people (G2: one curator and one reviewer; Q-3).

Limit, stated honestly: a database login proves **who holds the credential**, not who sits at the
keyboard. It must be personal, unshared and protected (a client certificate or a password manager;
§5.3). A person who knowingly gives away their credential defeats every design here (HUMAN
DEPENDENCY, T-6).

**Later, for a web review UI or more curators (OPEN QUESTION, D2/D3):** move to option 5, with the
gateway's trust and its `SET ROLE` audit documented. Not part of the pilot.

### 4.3 Identity schema (PROPOSAL; new migration, plan Stage 2)

- **`principals`**
  - Columns: `id uuid` (stable, never reused); `db_role name UNIQUE` (`p_<id>`); `display_name`;
    `created_at`; `created_by` (= `session_user` of the owner action); `status`
    (`active` | `revoked`); `revoked_at`; `revoked_reason`.
  - Rows are never deleted. A role that is revoked stays as a NOLOGIN role, so its OID and history
    survive.
- **`principal_role_events`** (append-only): grants and revocations of `curator` or `reviewer`,
  each with who did it and when.
- **`evidence.created_by`, `financial_statements.created_by`** (new, `uuid` → `principals.id`).
  Set by trigger from `session_user`, never from input. Legacy rows get `NULL`, meaning "before
  SEC-01A, typed names only".
- **`verification_reviews`**
  - New `reviewer_id uuid` and `curator_id uuid`, both set by `atlas_record_review` from
    `session_user` and from `evidence.created_by`.
  - The existing `curator`/`reviewer` text columns stay as display snapshots. Legacy rows keep
    them, with `identity_assurance = 'typed_name'`; new rows are `'authenticated'`.
- **`classification_requests`** (append-only): the curator proposes `kind`, `evidence_id` and
  `basis`; `created_by` comes from `session_user`. The reviewer approves it through
  `atlas_approve_classification`, which inserts the `company_classifications` row with both ids.
  Today's single-insert path, where one session types both names, is retired.
- **`security_audit_log`** (append-only, hash-chained):
  - Columns: `seq bigint` (identity); `at`; `actor_db_role` (`session_user`); `action`;
    `object_id`; `payload jsonb`; `prev_hash`; `hash` = `sha256(prev_hash ‖ canonical row)`.
  - Written by every procedure and by the DDL event trigger.

### 4.4 Verification flow (PROPOSAL)

| Step | Actor | Mechanism | Enforced by |
| --- | --- | --- | --- |
| 1 | Curator (`p_c`) | Runs `import` as **their own** login | DB authentication |
| 2 | — | Evidence is inserted `unverified` and `created_by` is set from `session_user` | `atlas_guard_evidence` and the `created_by` trigger (definer) |
| 3 | — | The curator's id comes from the login, not a flag. The `--curator` CLI flag is removed | Procedure |
| 4 | — | The evidence is listed as "awaiting review", a query on `unverified` evidence by others. Optional notification is out of scope | Read-only view |
| 5 | Reviewer (`p_r`) | Connects with **their own** credential | DB authentication |
| 6 | — | `atlas_record_review(evidence_id, expected_from_status, decision, checked_against, notes)` | Definer procedure |
| 7 | — | The procedure checks that `session_user` maps to an `active` principal holding `reviewer` | Procedure (refuses otherwise) |
| 8 | — | It checks that the reviewer's id ≠ `evidence.created_by`, and ≠ the `created_by` of the statement that cites the evidence | Procedure **and** a CHECK on `verification_reviews` (`reviewer_id <> curator_id`) |
| 9 | Reviewer | Examines the document; `checked_against` is required | Human, with the existing CHECK |
| 10 | — | Inserts the append-only review row with `reviewer_id` and `curator_id` | Existing append-only trigger |
| 11 | — | Locks the evidence row `FOR UPDATE`, compares `from_status`, applies the transition matrix, updates the status as `atlas_owner`, and stamps `last_verified_at` | Procedure. The guard allows changes only as `current_user = atlas_owner` |
| 12 | — | Appends to `security_audit_log` (actor, time, decision, evidence, hash) | Procedure |
| 13 | Anyone | A correction is a new review, or new evidence or a new revision. Nothing is rewritten | Append-only triggers, and no U/D/T grants |

**Transition rules: unchanged.** They are the matrix in `docs/VERIFICATION_WORKFLOW.md` §3,
already enforced in `atlas_apply_review`. Added rules (PROPOSAL):
- A `verified` decision needs `reviewer_id` ≠ the evidence's `created_by`, and neither may be
  `NULL`. Legacy evidence without `created_by` therefore **cannot be verified** until it is
  re-imported or re-attested by its curator (plan §4).
- `disputed`/`rejected` may be recorded by any active reviewer, including the curator. Flagging
  your own error is allowed; approving your own work is not.
- A reopen (`→ unverified`) needs a reviewer other than the one who rejected.
  - OPEN QUESTION: should it be stricter, for example a third person? At pilot scale there are only
    two people.
- A principal who was revoked can't act, because the procedure checks `status = 'active'` at call
  time. The reviews they recorded before stay valid and attributed. A revocation for compromise is
  handled by the integrity check plus re-review (plan §6).

Replays and duplicates: a replayed or duplicate call fails because `expected_from_status` no
longer matches: the row is locked, then compared (existing behaviour,
`test_stale_from_status_is_refused`). There is no request token to replay, because the call is a
DB transaction in the person's own session.

## 5. Migration isolation and secrets (PROPOSAL)

### 5.1 Separate the migration job

- Split `backend/Dockerfile:20`. The API image runs `uvicorn` only. A one-shot Compose service
  `migrate` (the same image) runs `alembic upgrade head && python -m app.ingestion reference` as
  `atlas_migrator` (who runs `SET ROLE atlas_owner` from `migrations/env.py`). `backend` waits
  with `depends_on: migrate: condition: service_completed_successfully`.
- Alembic must create objects **as `atlas_owner`**, so ownership never drifts to the migrator: run
  `SET ROLE atlas_owner` in `env.py` before migrating.
- A test asserts that every table and function is owned by `atlas_owner` (Stage 1 test DB-13).

### 5.2 Secrets

- One URL per process, with no shared password:
  - `DATABASE_URL_API` goes only to the backend container;
  - `DATABASE_URL_MIGRATE` goes only to `migrate`;
  - person roles are never in `.env`.

  Use Compose `secrets:` files (`*_FILE`), not `environment:`. `docker inspect` and
  `/proc/<pid>/environ` show plain environment values (INFERENCE from Docker's behaviour, not
  tested here).
- The bootstrap superuser password is used once (role provisioning) and then kept offline.
  `POSTGRES_PASSWORD` stays in the `db` service only, because the image needs it at first start.
- Logs:
  - keep SQLAlchemy `echo` off;
  - the health check already logs only the exception type (`health.py`);
  - `alembic.ini`/`env.py` must never print the URL;
  - set `log_min_error_statement` so failed statements with literals stay at the default level.
- CI: the test superuser stays for the test suite, because replica-mode fixtures need it. A
  **second** CI job provisions the production role model on a fresh database, migrates as
  `atlas_migrator`, and runs the negative tests as `atlas_api` and as person roles.

### 5.3 Person credentials

- Pilot (PROPOSAL): `scram-sha-256` passwords generated per person and kept in their own password
  manager, **or** client certificates (`pg_hba` `cert`). Certificates avoid shared typing and are
  preferred if hosting (Q-7) allows TLS to the database. Choosing is OWNER DECISION D8.
- `VALID UNTIL` on each person role (for example 90 days), renewed on purpose. Revocation:
  `ALTER ROLE p_x NOLOGIN`, revoke group membership, set `principals.status = 'revoked'`, and
  terminate open backends.

## 6. Network topology (PROPOSAL)

### 6.1 Scenario 1: local, owner only (today)

Every port stays on `127.0.0.1` (VERIFIED: `docker-compose.yml:15,34,51`). Development
credentials, fictional data only. The role model (§3) applies here too, so it gets tested every
day. There is no IdP. People are local `p_*` roles created by a dev script.

### 6.2 Scenario 2: private pilot, curator and reviewer on separate machines

```mermaid
flowchart LR
  subgraph Person devices
    B[Browser]
    CLI[Curation CLI / psql<br>own p_* credential]
  end
  IdP[(Identity provider<br>OIDC, MFA)]
  subgraph Private network: VPN, per-device keys
    RP[Reverse proxy<br>TLS, OIDC sign-in, rate limits]
    subgraph Docker network (internal)
      FE[Frontend<br>Next.js]
      API[Backend API<br>atlas_api]
      DB[(PostgreSQL<br>atlas_owner owns)]
      MIG[migrate job<br>atlas_migrator, one-shot]
    end
  end
  B -- HTTPS over VPN --> RP
  RP -- OIDC redirect --> IdP
  RP -- authenticated requests --> FE
  FE -- internal HTTP --> API
  API -- read-only SQL --> DB
  MIG -- DDL as atlas_owner --> DB
  CLI -- TLS + own credential, over VPN --> DB
```

| Path | Allowed? |
| --- | --- |
| Browser → reverse proxy (443, over the VPN) | **Allowed**, after an OIDC sign-in, only for allow-listed accounts |
| Reverse proxy → frontend | Allowed (internal network) |
| Frontend → API | Allowed (internal network). The API publishes **no host port** |
| API → DB | Allowed as `atlas_api` only, read-only |
| Migration job → DB | Allowed as `atlas_migrator`, only while it runs |
| Curation CLI → DB | Allowed over the VPN with TLS (`hostssl` in `pg_hba` for `p_*` roles only), **or** through SSH to the host with each person's own key |
| Browser → API, browser → DB | **Denied** (not published) |
| Frontend → DB | **Denied** (no credentials, `pg_hba` rejects) |
| API → internet egress | **Denied** (not needed) |
| `atlas_api` or `atlas_migrator` from outside the Docker network | **Denied** in `pg_hba` |
| Anything → `postgres` superuser remotely | **Denied**: local socket only, break-glass |

Notes:
- **Why both a VPN and an authenticating proxy.** The VPN keeps every service off the public
  internet (defence against unauthenticated scanning and framework CVEs). The proxy gives a named
  identity per browser request, needed for audit and revocation.
- **Pilot simplification.** The web app is read-only, so a VPN alone (per-person keys) is the
  minimum. The proxy sign-in is recommended, not required, if the VPN identities are personal
  (OWNER DECISION D6/D8).
- **Session policy for the proxy** (PROPOSAL):
  - cookies `Secure`, `HttpOnly`, `SameSite=Lax`;
  - 8-hour lifetime, re-authentication with MFA;
  - logout kills the session;
  - IdP account disable, then denial on the next request;
  - **CSRF:** the app has no state-changing HTTP endpoints, so the risk is nil today. Any future
    web write path needs CSRF tokens or `SameSite=Strict` plus an origin check.
- **Rate limits at the proxy** (SEC-08). Keep backend logs with the proxy's authenticated user
  header **only** if the API trusts it from the proxy alone (internal network).
- Hosting, VPN product and IdP: **OWNER DECISION** (Q-7). No provider or budget is chosen here.

### 6.3 Scenario 3: future public product (NOT designed here)

What it would additionally need:
- G1 legal clearance and commercial data rights (A-6, Track B LR-1..5);
- public TLS and a CDN or WAF;
- a different auth model (readers anonymous, staff on an IdP);
- privacy policy and data-protection obligations under Vietnamese law (a legal opinion is needed);
- separate staff and public deployments, so no curation network path exists from the public tier;
- vulnerability management and incident response;
- backups with tested restore;
- SEC-05 headers and a CSP;
- SEC-09 docs disabled.

## 7. SEC-02 authorisation in the API (PROPOSAL)

- In Scenario 2 the read-only API needs no per-route roles. Everyone allowed through the proxy may
  read.
- A remote-pilot mode (`APP_ENV=pilot`) makes the backend refuse requests that don't carry the
  proxy's authenticated-user header, from the proxy's address only. That gives defence in depth if
  the backend port is ever published by mistake (test API-1).
- There is no curator-only HTTP operation, so "API cannot reach curator operations" holds by
  construction:
  - `atlas_api` has EXECUTE on no procedure;
  - it is read-only by `default_transaction_read_only`;
  - it holds SELECT only (test DB-3, API-5).

## 8. Low findings in this context

See [SEC_01A_IMPLEMENTATION_PLAN.md](SEC_01A_IMPLEMENTATION_PLAN.md) §2, Stage 4, for the
staging. In short:

| Finding | Before real-data pilot | Before remote pilot | Notes |
| --- | --- | --- | --- |
| SEC-03 `file://` paths | **Yes**: the `api.evidence` view drops non-http(s) URLs, and the importer refuses `file://` for real evidence | Yes | Comes with Stage 1 (the views) |
| SEC-04 website link | Defence in depth | Recommended | One-line frontend fix |
| SEC-05 headers | Defence in depth | Recommended (framing, nosniff) | |
| SEC-06 pinning | Defence in depth | Recommended | |
| SEC-07 branch protection | Owner-only GitHub setting | Owner-only | Plus a human review per PR (AU-6) |
| SEC-09 docs | Acceptable locally | **Yes**: off, or behind the proxy only | |
| SEC-10 typed names | **Yes**: this design (§4) | Yes | The central issue |

## 9. Residual risks (what stays true after every stage)

1. **A superuser or `atlas_owner` can rewrite anything**, including disabling triggers and forging
   hash-chain rows by recomputing them. Controls are detective only:
   - an external anchor (§9.1);
   - the event-trigger DDL log;
   - server logs shipped off the database host;
   - the integrity check run by someone other than the operator.

   Accepting this is OWNER DECISION D5.
2. **Credential sharing.** One person using two `p_*` credentials looks exactly like two people.
   Only process controls help: personal credentials, an appointed reviewer (Q-3), and a reviewer
   declaration on each session (HUMAN DEPENDENCY).
3. **The host operator** (root on the Docker host) can read the volume, swap images, or run as the
   superuser. Hosting choice and access (Q-7) decide this.
4. **Backup rollback.** Restoring an old backup silently undoes later reviews. Mitigations: signed,
   versioned backups; compare the restored `security_audit_log` head with the last external anchor
   before going live (D10).
5. **The reviewer's diligence** can't be proven by any control. `checked_against` records what they
   say they checked (HUMAN DEPENDENCY).
6. **Option 5 later** (web review) moves trust to the gateway service.

### 9.1 Tamper evidence (PROPOSAL)

- **Daily anchor.** A job (owner-run, read-only role `atlas_auditor`) exports the head `hash` of
  `security_audit_log`, the count and latest id of `verification_reviews`, and a digest of
  `(evidence.id, verification_status)`. The export goes somewhere the database operator can't
  rewrite: a signed git commit in a **private** repository, or an append-only store chosen by the
  owner.
- **Integrity check** (read-only, also in CI against fixtures). Each item is a SQL assertion:
  - every evidence row not `unverified`/`sample` has a latest review whose `decision` equals its
    status;
  - no review has `reviewer_id = curator_id`;
  - each classification chain is linear;
  - the hash chain recomputes;
  - nothing exists in `pg_trigger` with `tgenabled <> 'O'` on protected tables;
  - all objects are owned by `atlas_owner`.

  The check would have caught P5 (status `verified` with no review) and P9 (a disabled trigger).
