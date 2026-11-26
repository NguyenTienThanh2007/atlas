# SEC-01A: implementation plan (design only)

**Status: READY FOR OWNER ARCHITECTURE REVIEW. NOT READY FOR IMPLEMENTATION.**

- Nothing here is approved.
- Every recommendation is a **PROPOSAL**.
- No code, migration, database, GitHub setting or deployment was changed by this design phase.

Baseline: `main` @ `aa3218a`. Architecture: [SEC_01A_SECURITY_ARCHITECTURE.md](SEC_01A_SECURITY_ARCHITECTURE.md)
("Arch"). Threats: [SEC_01A_THREAT_MODEL.md](SEC_01A_THREAT_MODEL.md) ("TM").

The approved product decisions (A-1..A-11, WS4-D*, WS4-4-D1..D10, EX-2) are **unchanged**.
WS4-4-D7 asks that "two people" check each classification. This plan proposes the way to *enforce*
that; it does not change what the decision says.

## 1. Owner decision register (all OWNER DECISION REQUIRED)

| ID | Decision | Context | Options | Advantages / risks | Recommendation (PROPOSAL) | Depends on | Blocks implementation? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D1 | Database principal architecture | Superuser everywhere (Arch §1.1); three roles are not enough (Arch §2, P5/P6e) | (a) 3 roles, as in the SEC-01 checklist row; (b) Arch §3: NOLOGIN owner, migrator, API, one role per person, definer procedures | (a) is simple but leaves P5/P6e/P7; (b) closes them and costs more grants and procedures | **(b)** | — | **Yes**, for Stages 1–2 |
| D2 | How reviewer identity is authenticated | SEC-10, T-1, T-6 | (1) app OIDC; (2) a shared credential; (3) a DB role per person; (4) a context variable; (5) hybrid gateway | Arch §4.1 table | **(3)** for the pilot; (5) only if a web review UI is approved later | D1 | **Yes**, for Stage 2 |
| D3 | Where accounts are managed | Who creates and revokes people | Inside ATLAS (`principals` table plus DB roles, provisioned by the owner) or an external IdP | Inside is simple at 2–3 people; external is needed for SSO | **Inside ATLAS** for the pilot; the IdP is only for proxy sign-in (D8) | D2 | Yes, for Stage 2 |
| D4 | Does the DB enforce verification through stored procedures? | Invoker triggers force broad grants (P3a, P6c) | (a) keep triggers, grant tables; (b) `SECURITY DEFINER` procedures, no table DML | (a) keeps P5/P6e; (b) brings rewrite effort and tests | **(b)**, with per-record import procedures so the Python validation in `importer.py` stays | D1 | Yes |
| D5 | Direct SQL by privileged operators | TM T-12, T-17 | Accept with detection; or separate duties (another person holds the superuser and the anchor) | Detection only vs real separation (needs a second trusted person) | **Accept and detect** (event trigger, hash chain, external anchor, integrity check) for the pilot; separate duties before G1 | D13 | No (Stage 4 detective work) |
| D6 | Remote private pilot before Q-7? | SEC-02 | No remote access until hosting is chosen; or a temporary VPN to the owner's machine | A host has to exist either way | **No remote access** until Q-7 is decided and Stage 3 passes | Q-7 | Yes, for Stage 3 |
| D7 | SEC-03..SEC-06, SEC-09 in the same release? | Scope control | All in one release; or staged | One release is larger | **Staged:** SEC-03 with Stage 1 (it comes free with the views); SEC-09 with Stage 3; SEC-04/05/06 as Stage 4 | — | No |
| D8 | Authentication and session policy | Person DB credentials; proxy sessions | DB: SCRAM in a password manager, or client certificates. Proxy: OIDC with MFA, 8 h sessions | Certificates are stronger and need TLS to the DB | **Client certificates** if hosting allows, else SCRAM; `VALID UNTIL` 90 d; MFA on VPN and IdP | Q-7 | Yes, for Stages 2–3 |
| D9 | Audit identity retention and revocation | Reviews must stay attributable after someone leaves | Keep principals forever (NOLOGIN), or anonymise | Accountability vs privacy | **Keep forever** with a display name; personal data limited to name and role; revocation as in Arch §5.3. A legal check on personal-data retention may be needed (OPEN QUESTION) | — | No |
| D10 | Backup and recovery security | TM T-18 | Encrypted, versioned dumps compared with the anchor on restore | Cost and storage location (Q-7) | **Encrypted dumps + anchor check before reopening** | Q-7, D5 | No (before real data: yes, see D12) |
| D11 | Rollback strategy | §6 | A forward fix only; or a down-migration plus restore | §6 | **Down-migration for Stage 1** (grants only); Stage 2 a forward fix plus restore from backup | — | No |
| D12 | Acceptance before real pilot data | G2 | §7 list | — | **All of §7 "before real data"** | D1–D4, D10 | **Yes**, for G2 data |
| D13 | Appoint an independent human reviewer | Q-3, D-6 | Appoint someone; or postpone verification | Without one, nothing can be `verified` | **Appoint** before G2 reviews start; ideally someone other than the database operator | — | Blocks verification, not engineering |

Products, providers and budget are not chosen here (Q-7).

## 2. Staged implementation

Sizes: **S** ≈ 1–2 engineering days, **M** ≈ 3–5, **L** ≈ 6–10. They assume one engineer familiar
with the code, and exclude owner review time. They are rough.

### Stage 0: owner decisions (no code)

- Decide D1–D4, D6 and D8, and note D5 and D7.
- **Gate G-0:** decisions recorded in `PRODUCT_DECISIONS.md` as a new dated section, by the owner.

### Stage 1: database least privilege (M–L)

**Tasks**

1. A provisioning script (`infra/postgres/init/02-roles.sql`, plus an idempotent
   `python -m app.ops roles` for volumes that already exist). It:
   - creates `atlas_owner`, `atlas_migrator`, `atlas_api`;
   - runs `REVOKE TEMP/CREATE` from PUBLIC.
2. A migration `sec01a_least_privilege`:
   - reassign ownership of every table and function to `atlas_owner`;
   - `REVOKE EXECUTE … FROM PUBLIC`;
   - grant `atlas_api` SELECT on the `api` schema views (Arch §3.4) and the reference tables;
   - add the views (`api.evidence` filters non-http(s) URLs, which fixes SEC-03).
3. Harden every trigger function:
   - `SECURITY DEFINER` where it writes, `SET search_path`, qualified names;
   - replace the `pg_trigger_depth()` guard;
   - add `BEFORE TRUNCATE` and `BEFORE DELETE` guards (Arch §3.2).

   This is done by `CREATE OR REPLACE FUNCTION`; the existing behaviour tests stay.
4. Compose:
   - a `migrate` one-shot service;
   - `backend` gets only `DATABASE_URL_API`, from a secret file;
   - no host port for `backend` in pilot mode;
   - `backend/Dockerfile:20` runs `uvicorn` only.
5. `migrations/env.py`: `SET ROLE atlas_owner`.
6. The CLI keeps running as the owner-like dev role **only in local dev**, until Stage 2. Document
   this as a known gap.
7. CI: a new job `backend-roles` that provisions roles on a fresh database, migrates as the
   migrator, and runs the DB-* tests as the real roles.
8. Docs: DEVELOPMENT.md (roles, how to provision on an existing volume), VERIFICATION_WORKFLOW
   (fix the §4 "the database sets" inaccuracy when T-22 lands).

**Other details**

- Files likely to change: `docker-compose.yml`, `.env.example`, `backend/Dockerfile`,
  `backend/migrations/env.py`, a new migration, `infra/postgres/init/`, `backend/app/db.py`,
  `backend/app/config.py`, `backend/app/models.py` (view-backed read models or `schema=`),
  `.github/workflows/backend.yml`, `docs/DEVELOPMENT.md`, and new tests.
- Risks:
  - ORM reads must target the views (a column or schema mismatch breaks the API);
  - a `SECURITY DEFINER` mistake grants too much;
  - the existing user volume needs a role-provisioning step (the user stack is at migration
    `31b1317163eb` today; VERIFIED, read-only).
- Acceptance:
  - the DB-1..DB-13 and DEP-1..DEP-3 tests pass in CI;
  - all 404 existing tests pass;
  - the route check passes in vi and en.
- Rollback: §6.

### Stage 2: authenticated human identity and two-person verification (L)

**Tasks**

1. A migration adds:
   - `principals` and `principal_role_events`;
   - `created_by` on `evidence` and `financial_statements`;
   - `reviewer_id`/`curator_id`/`identity_assurance` on `verification_reviews`;
   - `classification_requests`;
   - `security_audit_log` (hash chain).
2. Definer procedures:
   - `atlas_submit_*` (import, per record);
   - `atlas_record_review`;
   - `atlas_request_classification`;
   - `atlas_approve_classification`;
   - `atlas_stamp_last_verified`, inside the review procedure.
3. Person-role tooling: `python -m app.ops person add|revoke|list`, owner only.
   - It creates `p_<id>` NOINHERIT, adds membership, and writes the `principals` and audit rows.
4. CLI:
   - `import`, `review` and `classify` connect as the **person's own** credential (a prompt or a
     certificate);
   - the `--curator`/`--reviewer` flags are removed;
   - a `classify request` / `classify approve` pair.
5. Retire the direct table writes in `app/ingestion/review.py` (Python `_stamp_last_verified`) in
   favour of procedure calls.
6. Docs: VERIFICATION_WORKFLOW §1, §5 and §8a; G2_PILOT_RUNBOOK §3 and §4 (commands).

**Other details**

- Files likely to change: `backend/app/ingestion/{__main__,review,importer,runs}.py`,
  `backend/app/models.py`, a new migration, new `backend/app/ops/`, and tests
  (`test_verification.py`, `test_classification.py`, `test_ingestion.py` adapt to procedures).
- Risks:
  - **The largest behaviour change**: the import transaction semantics have to survive in
    procedures;
  - legacy reviews with typed names (§4);
  - test fixtures that use replica mode need a superuser test harness separate from the role tests.
- Acceptance: ID-1..ID-7 and AUD-1/AUD-2 pass; a two-login end-to-end run on the fictional
  fixture.
- Rollback: §6.

### Stage 3: private pilot access (M, plus hosting)

**Tasks**

1. VPN with per-person device keys.
2. Reverse proxy: TLS, OIDC sign-in, rate limits.
3. Pilot-mode API header check (Arch §7).
4. SEC-09 docs off.
5. `pg_hba`: `hostssl` for `p_*` from the VPN range only; `atlas_api` and `atlas_migrator` from the
   Docker network only.
6. `idle_session_timeout` and connection limits.
7. Log shipping off the host.

**Other details**

- Files likely to change: `docker-compose.yml` (a pilot override file), the proxy config (new),
  `backend/app/main.py` (pilot-mode middleware), `infra/postgres/` (`pg_hba`), docs.
- Dependencies: **Q-7** (hosting), D6, D8.
- Acceptance: API-1..API-3, DEP-3..DEP-6.
- Rollback: take the pilot host off the network. Local mode is unaffected.

### Stage 4: additional hardening (S–M)

- SEC-04 (`safeHref` on the website).
- SEC-05 (headers).
- SEC-06 (SHA/digest pinning, Dependabot).
- SEC-07 (branch protection: **the owner changes GitHub settings**).
- The DDL event trigger (AUD-3).
- The daily anchor job (AUD-4).
- Image scanning in CI.
- Acceptance: DEP-7, AUD-3, AUD-4, and the route check asserts the headers.

## 3. Migration plan

| Step | Migration | Data effect | Reversible? |
| --- | --- | --- | --- |
| M1 | `sec01a_least_privilege` (Stage 1) | None (ownership, grants, function bodies, views, guards) | Yes: down restores the old function bodies and ownership |
| M2 | `sec01a_identity` (Stage 2) | Adds nullable columns and new tables; backfills `identity_assurance='typed_name'` on existing reviews; `created_by = NULL` on existing evidence and statements | Down drops the new objects, **refuses** if authenticated reviews exist (like `test_downgrade_refuses_to_discard_review_history`) |
| M3 | `sec01a_audit_ddl` (Stage 4) | Event trigger (needs the bootstrap superuser) | Yes |

**Ordering.** Every migration runs as `atlas_migrator` → `SET ROLE atlas_owner`. Exceptions are the
role provisioning (bootstrap superuser, once) and M3 (superuser, event triggers). The migration
completes before the backend starts (`service_completed_successfully`).

## 4. Backward compatibility

- **API responses:** unchanged. The views keep the column names. Exception (SEC-03, D7):
  non-http(s) `source_url` becomes `null`. This is an API behaviour change and needs owner
  approval.
- **Existing data:**
  - `main` holds no real reviews: 0 real companies; the user stack is empty (VERIFIED, read-only).
  - Legacy typed-name reviews, if any, keep their text and are labelled `typed_name`.
  - Legacy evidence with `created_by = NULL` **can't be newly verified** until it is re-imported by
    an authenticated curator. That is deliberate (Arch §4.4).
- **CLI:** `--curator`/`--reviewer` disappear in Stage 2 (a breaking change for operators; the
  docs update in the same PR).
- **Tests:**
  - The existing 404 tests run under a superuser test harness, because the fixtures use replica
    mode.
  - A new role-test harness runs as the real roles.
  - The existing tests that insert raw SQL reviews (`test_raw_sql_review_is_held_to_the_same_rules`)
    move to calling procedures.
- **Local development:** `.env.example` gains per-process URLs. An existing volume needs
  `python -m app.ops roles` once (documented). Never `docker compose down -v` on someone's stack.

## 5. Test matrix (all PROPOSED, none run)

Automation locations:
- `backend/tests/security/test_roles.py` (DB-*): runs on a fresh database with the real roles.
- `backend/tests/security/test_identity.py` (ID-*).
- `backend/tests/test_api.py` plus `frontend/scripts/check-routes.mjs` (API-*).
- `.github/workflows/backend.yml` job `backend-roles`, plus a pilot smoke script (DEP-*).
- `backend/tests/security/test_audit.py` plus the `app.ops integrity` command (AUD-*).

### 5.1 Database (DB)

| ID | Scenario | Setup | Action | Expected | Property proven |
| --- | --- | --- | --- | --- | --- |
| DB-1 | API attributes | Provisioned roles | Read `pg_roles` for `atlas_api` | `rolsuper`, `rolcreaterole`, `rolcreatedb`, `rolbypassrls` false; not a member of any role | API is not privileged |
| DB-2 | API writes | Connect as `atlas_api` | `INSERT`, `UPDATE`, `DELETE` on `evidence` and every table | `permission denied` (or a read-only transaction error) | Read-only API (TM T-16) |
| DB-3 | API and DDL | `atlas_api` | `TRUNCATE`, `ALTER TABLE … DISABLE TRIGGER`, `CREATE TABLE`, `CREATE TEMP TABLE` | All refused | No DDL, no TEMP |
| DB-4 | Replication role | `atlas_api`, a person role | `SET session_replication_role = replica` | `permission denied to set parameter` | T-13 (already TESTED as P1 for a non-superuser) |
| DB-5 | Shadowing | A person role (curator) | `CREATE TEMP TABLE evidence…`, then request a classification citing another company's evidence | TEMP refused; and with TEMP granted in a variant, the procedure still refuses (qualified names) | T-14 (regression for P6e) |
| DB-6 | Depth-2 bypass | A person role (reviewer) | P5 script | `permission denied for table evidence` (no UPDATE); in a variant with TEMP and UPDATE granted, the guard still refuses (`current_user` ≠ owner) | T-10 (regression for P5) |
| DB-7 | Curator sets verified | Curator role | Call the import procedure with `verification_status='verified'`; direct `UPDATE` | Refused | Evidence starts unverified |
| DB-8 | History is immutable | Curator and reviewer roles | `UPDATE`/`DELETE`/`TRUNCATE` on `verification_reviews`, `company_classifications`, `financial_*`, `security_audit_log` | Refused (privilege), and the guards refuse even for the owner without `DISABLE TRIGGER` | T-11 |
| DB-9 | Evidence deletion | All runtime roles | `DELETE FROM evidence` | Refused | Regression for P11 |
| DB-10 | Trigger disable | All non-owner roles | `ALTER TABLE evidence DISABLE TRIGGER evidence_guard` | `must be owner` | T-12 (P8 TESTED for a non-owner) |
| DB-11 | Parameter grants | — | Query `pg_parameter_acl` | No grant on `session_replication_role` | T-13 |
| DB-12 | Display forgery | Any runtime role | `UPDATE companies SET last_verified_at = now()` | Refused; only the review procedure stamps it | T-22 |
| DB-13 | Ownership and inheritance | — | Every table, view and function owned by `atlas_owner`; `atlas_migrator` NOINHERIT; person roles NOINHERIT; no runtime role is a member of `atlas_owner` | Assertions pass | No silent escalation through membership |

### 5.2 Identity (ID)

| ID | Scenario | Setup | Action | Expected | Property proven |
| --- | --- | --- | --- | --- | --- |
| ID-1 | Self-approval | `p_a` curates evidence E | `p_a` calls `atlas_record_review(E, …, 'verified')` | Refused ("reviewer is the curator") | T-1 |
| ID-2 | Two strings, one user | `p_a` | Any attempt to pass names (the procedure has no name argument); the old CLI flags | Signature error / unknown flag | String names aren't identity (SEC-10) |
| ID-3 | Impersonation | `p_a` | `SET ROLE p_b`, then review | `permission denied to set role` (no membership) | T-2 |
| ID-4 | Intended flow | `p_a` curates, `p_b` reviews | Import, then review `verified` | Status `verified`; the review row has `curator_id = a`, `reviewer_id = b`; the audit row is chained | Two-person flow works |
| ID-5 | Revoked reviewer | `p_b` revoked | `p_b` connects / calls | Connection refused (NOLOGIN), or the procedure refuses if still connected | T-5, T-7 |
| ID-6 | Replay and duplicate | After ID-4 | Repeat the same call | Refused (`from_status` mismatch); history unchanged | T-3, T-8 |
| ID-7 | Race | Two reviewers, two connections | Both decide E at the same moment | Exactly one succeeds; the other fails on `from_status` | T-9 |

### 5.3 API (API)

| ID | Scenario | Setup | Action | Expected | Property proven |
| --- | --- | --- | --- | --- | --- |
| API-1 | Unauthenticated, pilot mode | `APP_ENV=pilot` | Request without the proxy identity header, or from a non-proxy address | 401 | SEC-02 defence in depth |
| API-2 | Through the proxy | Proxy stack | No session → redirect to the IdP; a disallowed account → 403 | As stated | T-20 |
| API-3 | Revoked session | Proxy stack | The IdP account is disabled mid-session | Next request denied | T-4/T-5 at the web tier |
| API-4 | No local paths | A real-source fixture with a `file://` URL | `GET /companies/{id}/evidence` | `source_url` is not the path (`null`) | SEC-03 / T-21 |
| API-5 | No curator operations | — | OpenAPI lists only `GET`; `atlas_api` has no EXECUTE on any procedure | As stated | Read-only by construction |

### 5.4 Deployment (DEP)

| ID | Scenario | Setup | Action | Expected | Property proven |
| --- | --- | --- | --- | --- | --- |
| DEP-1 | Secret separation | The Compose stack | `docker inspect backend`; read the backend's secret files | Only the `atlas_api` credential; no migrator or superuser secret | T-15, T-16, T-24 |
| DEP-2 | Migrations first | A fresh volume | `docker compose up` | `migrate` exits 0 before `backend` starts; the backend does not run Alembic | TB6 |
| DEP-3 | Backend not exposed | Pilot override | Port scan from the VPN and the host LAN | Only the proxy port answers | T-20 |
| DEP-4 | TLS and authentication enforced | Pilot | HTTP (not HTTPS), and HTTPS without a session | Redirected or denied | SEC-02 |
| DEP-5 | No secrets in logs | Start plus failing DB | Grep all container logs for passwords and URLs | None | T-24 |
| DEP-6 | Restore check | A backup taken, then reviews added | Restore the old backup; run the integrity check against the anchor | The check reports the anchor mismatch | T-18 |
| DEP-7 | Pinned supply chain | — | Lint the workflows and Dockerfiles for non-SHA/non-digest refs | None | T-23 |

### 5.5 Audit (AUD)

| ID | Scenario | Setup | Action | Expected | Property proven |
| --- | --- | --- | --- | --- | --- |
| AUD-1 | Hash chain | After ID-4 | Recompute the chain | Matches | T-19 |
| AUD-2 | Tamper detection | A superuser test harness | Change one audit row, or set a status with replica mode (P5/P9 style) | The integrity check fails, naming the row | T-10/T-12/T-17 detection |
| AUD-3 | DDL logged | Owner | `ALTER TABLE … DISABLE TRIGGER` | An audit row and a server log line | T-12 |
| AUD-4 | Anchor | Daily job | Export; compare | The digest matches the database | T-17/T-18 |

## 6. Rollback plan

| Stage | Rollback |
| --- | --- |
| 1 | `alembic downgrade` to `5c1f0a2b7e44` (as the owner) restores the function bodies and ownership. The Compose file reverts to a single URL. The roles can stay; they are harmless if unused. Data is untouched. |
| 2 | Forward fix preferred. A down-migration refuses if authenticated reviews exist. Otherwise restore the pre-migration backup taken in the deployment runbook, then re-run the integrity check. |
| 3 | Take the pilot host off the VPN. Local mode keeps working. |
| 4 | Revert the individual changes. Branch protection is the owner's setting. |

Before **every** stage on any database with data: an encrypted backup, and the integrity check
recorded (D10).

## 7. Acceptance criteria

**Before real pilot data (G2)**
- D1–D4, D8, D10 and D12 decided.
- Stages 1 and 2 merged, with DB-*, ID-*, API-4, API-5, DEP-1, DEP-2, AUD-1 and AUD-2 green in CI.
- An independent reviewer appointed (D13, Q-3).
- A human review recorded on each SEC-01A PR (AU-6). AI review does not count.

**Before remote testers**
- All of the above, plus Stage 3: API-1..API-3, DEP-3..DEP-6.
- Q-7 decided.

**Before public launch**
- Out of scope (Arch §6.3).
- Needs G1.

## 8. Dependencies

- Q-3: the reviewer.
- Q-7: hosting.
- G1: public display.
- WS4-4-D7: two people per classification, enforced by Stage 2.
- EX-2: the review tool is local only, and is kept.
- The role-test harness depends on Stage 1.
- Stage 2 depends on Stage 1.
- Stage 3 depends on Stages 1–2 and Q-7.

## 9. Explicit approval gates

| Gate | Before | Approver |
| --- | --- | --- |
| G-0 | Any SEC-01A code | Owner: D1–D4, D6, D8 |
| G-1 | Merge Stage 1 | Owner + a recorded human review + green CI |
| G-2 | Merge Stage 2 | The same |
| G-3 | Load Company 1–5 real data | Owner: §7 "before real data" met |
| G-4 | Remote access | Owner: Stage 3 accepted, Q-7 decided |

Approving this document is **not** approval of any gate.
