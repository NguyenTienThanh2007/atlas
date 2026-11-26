# SEC-01A: threat model (design only)

**Status: DESIGN FOR OWNER REVIEW. Nothing here is implemented.**

- Baseline: `main` @ `aa3218a`.
- Architecture: [SEC_01A_SECURITY_ARCHITECTURE.md](SEC_01A_SECURITY_ARCHITECTURE.md), cited as
  "Arch §n".
- Tests and decisions: [SEC_01A_IMPLEMENTATION_PLAN.md](SEC_01A_IMPLEMENTATION_PLAN.md), cited as
  "Plan".

Probes P1–P11 are the disposable-database tests in Arch §2. They are TESTED FACT. Everything marked
"proposed" is a PROPOSAL and has not been tested.

## 1. Assets

| ID | Asset | Why it matters |
| --- | --- | --- |
| A1 | **Verification state** of evidence (`evidence.verification_status`) and the "Last verified" display | ATLAS's core promise: nothing is shown as verified without an independent review |
| A2 | **Review history** (`verification_reviews`) and classification history (`company_classifications`) | Accountability; corrections are traceable |
| A3 | **Reported figures** (`financial_statements`, `financial_metrics`): exact Decimal values, page, scale | Wrong figures hurt trust disproportionately (D-6) |
| A4 | **Sample/real separation** | Fictional data must never look real |
| A5 | **Human identities** (future `principals`, `p_*` credentials) | Two-person verification rests on them |
| A6 | **Credentials**: bootstrap superuser, migrator, API, person roles | Each one is a capability |
| A7 | **Unpublished pilot data** (Company 1–5) | A-6: internal only until G1 |
| A8 | **Curators' local environment details** (paths, user names) | SEC-03 privacy |
| A9 | **Audit evidence** (`security_audit_log`, server logs, external anchors) | Detecting what can't be prevented |

## 2. Trust boundaries

| ID | Boundary | Today | Proposed |
| --- | --- | --- | --- |
| TB1 | Internet / LAN → host | Only `127.0.0.1` bindings (VERIFIED) | VPN plus an authenticating proxy (Arch §6.2) |
| TB2 | Browser → frontend | None | Proxy sign-in (OIDC) |
| TB3 | Frontend → API | Internal; the API also publishes a host port | Internal only; no host port |
| TB4 | API process → database | **Superuser** (VERIFIED) | `atlas_api`, read-only, views only |
| TB5 | Curator or reviewer → database | **Superuser** from `.env` (VERIFIED) | A personal `p_*` login, procedures only |
| TB6 | Migration → database | Superuser, inside the API container (VERIFIED, `backend/Dockerfile:20`) | `atlas_migrator` → `SET ROLE atlas_owner`, a one-shot job |
| TB7 | Database operator / host root → everything | Unbounded | Unbounded. Only detective controls (Arch §9) |
| TB8 | Repository → CI → images | Mutable tags, no branch protection (SEC-06, SEC-07) | Pinned, protected, a human review |

## 3. Threat actors

| ID | Actor | Capability assumed |
| --- | --- | --- |
| TA1 | Outside attacker | Network reach, if anything is exposed; can run public exploits |
| TA2 | Pilot tester (authorised reader) | A valid proxy session; reads everything |
| TA3 | **Curator acting alone** (an honest mistake or a shortcut) | Their own credential and the CLI. Wants their own work marked verified |
| TA4 | Reviewer | Their own credential. May rubber-stamp, or have their account taken over |
| TA5 | Attacker with code execution in the API | Whatever credential the API container holds |
| TA6 | Holder of a leaked database credential | That role's rights |
| TA7 | **Malicious or careless administrator** (owner role, superuser, host root) | Everything |
| TA8 | Supply-chain attacker | A changed action or image tag |

## 4. Attack surfaces

- The read-only HTTP API: 12 `GET` routes (VERIFIED).
- `/docs` and `/openapi.json` (SEC-09).
- The frontend server.
- The PostgreSQL listener: today `127.0.0.1:5433` on the host.
- The CLI (`backend/app/ingestion/__main__.py`), using `.env` credentials.
- The container environment and `docker inspect`.
- Backups and volume files.
- CI workflows and image builds.

## 5. Threat scenarios

**Risk scale.** Likelihood × impact, each Low, Medium or High.
- The "today" rating assumes the current deployment: localhost only, no real data.
- The "pilot without fix" rating assumes real pilot data with the current code.
- The "residual" rating assumes the proposed controls are in place.

**Tests.** The test IDs in the last column are defined in Plan §5.

### 5.1 Self-approval and impersonation

| ID | Threat | Attacker / path | Impact | Existing control | Proposed control | Residual | Regression tests |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T-1 | **Curator self-approval** | TA3 runs `review --curator Me --reviewer "Someone"` with the shared `.env` login | A1 broken; false "verified" | CHECK: names differ (string). **P7: accepted** | Personal logins. The procedure takes the reviewer from `session_user` and the curator from `evidence.created_by`, and refuses equality. The `--curator`/`--reviewer` flags are removed | Low, unless credentials are shared (T-6) | ID-1, ID-2, ID-4 |
| T-2 | **Curator changes the reviewer id in the request** | TA3 passes a different `reviewer_id` argument | The same as T-1 | None: today there is no id, only text | The procedures take **no** actor argument. Identity is `session_user` only | Low | ID-3 |
| T-3 | **Replaying an old approval** | TA3 or TA4 re-runs a recorded review call | A duplicate or stale transition | `from_status` is compared under a lock (`atlas_apply_review`; `test_stale_from_status_is_refused`) | The same, inside the definer procedure. There is no bearer token to replay (DB session) | Low | ID-6 |
| T-4 | **Reusing another user's session** | TA3 uses the reviewer's open `psql` session or proxy cookie | Impersonation | None | Personal devices; idle timeout (`idle_session_timeout`); proxy cookies `HttpOnly`/`Secure`/short-lived. Proxy sessions can't write anything (read-only web) | Medium: physical access defeats it (HUMAN DEPENDENCY) | API-3 (proxy), DEP-5 |
| T-5 | **Reviewer whose access was revoked** | A former reviewer still holds a password | A1 | None | `ALTER ROLE NOLOGIN`, revoke membership, `principals.status = 'revoked'`; the procedure checks `active` at call time; `VALID UNTIL` | Low | ID-5 |
| T-6 | **Credential sharing / one person, two logins** | TA3 holds both the `p_c` and `p_r` secrets | Two-person verification defeated, and undetectable by the DB | None | Owner process: one credential per person, issued directly to that person; the reviewer is appointed (Q-3); signed declarations; certificates bound to a device | **Medium, accepted HUMAN DEPENDENCY** | none possible in code (documented) |
| T-7 | **Reviewer account compromise** | TA1 phishes the reviewer's credential | False verification | None | Certificates or a password manager; MFA on VPN and IdP; a connection limit of 1; `log_connections`; the anchor lets you re-review every decision since the compromise window | Medium | ID-5, AUD-2 |

### 5.2 Concurrency and duplicates

| ID | Threat | Path | Impact | Existing control | Proposed control | Residual | Tests |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T-8 | **Duplicate review submission** | The same call is sent twice | A double history row | `from_status` check: the second call sees the new status and fails | Unchanged | Low | ID-6 |
| T-9 | **Concurrent review race** | Two reviewers decide at the same moment | Lost update or an inconsistent history | `SELECT … FOR UPDATE` on the evidence row in the trigger | The same `FOR UPDATE` in the procedure | Low | ID-7 (two connections) |

### 5.3 Direct SQL, triggers and privilege

| ID | Threat | Path | Impact | Existing control | Proposed control | Residual | Tests |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T-10 | **Direct SQL UPDATE of the status** | Any role with `UPDATE` on `evidence` | A1 | Depth-1 guard (P4 refused) **but P5 bypasses it at depth 2** | No runtime role has `UPDATE`. The guard allows changes only as `current_user = atlas_owner`. `TEMP` is revoked | Low (except TA7) | DB-2, DB-6, DB-7 |
| T-11 | **Direct SQL DELETE / TRUNCATE of history or evidence** | A role with `DELETE`/`TRUNCATE`, or the table owner | A2 lost. P9b: TRUNCATE wiped reviews. P11: unreviewed evidence deleted | Row-level append-only triggers (not on TRUNCATE, not on `evidence` DELETE) | No D/T grants; `BEFORE TRUNCATE` and `BEFORE DELETE` guards; ownership kept by the NOLOGIN owner | Low (except TA7) | DB-3, DB-8, DB-9 |
| T-12 | **Disabling a trigger** | The table owner: `ALTER TABLE … DISABLE TRIGGER` (P9) | Every guard | Only owners and superusers can (P8 refused for a non-owner) | The owner is NOLOGIN. Migrator credentials exist only in the one-shot job. The DDL event trigger logs it. The integrity check looks at `tgenabled` | Medium (detective vs TA7) | DB-10, AUD-3 |
| T-13 | **`session_replication_role = replica`** | A superuser, or a role granted `SET ON PARAMETER` | Every trigger | Superuser-only (P1 refused) | No runtime superuser; no parameter grant (asserted); the superuser secret kept offline | Low (except TA7) | DB-4, DB-11 |
| T-14 | **Search-path shadowing through `pg_temp`** | A role with `TEMP` and an INSERT privilege creates `pg_temp.evidence` (P6e) | A4 / classification integrity; INFERENCE: the isolation and review triggers are exposed the same way | None | Definer functions with `SET search_path = pg_catalog, public, pg_temp`, qualified names; `TEMP` revoked | Low | DB-5, DB-6 |
| T-15 | **Migration credential leak** | TA6 obtains `atlas_migrator` | Owner powers (DDL, trigger disable) | n/a (today everything is the superuser) | The secret exists only in the `migrate` job; NOINHERIT needs a visible `SET ROLE`; rotation after every release (OPEN QUESTION); DDL audit | Medium | DEP-1, DEP-2 |
| T-16 | **API database credential leak / API compromise** | TA5 or TA6 as `atlas_api` | Read everything the views expose (pilot data, A7) | n/a (today: the superuser, a full takeover) | SELECT on views only; read-only transactions; no EXECUTE; no TEMP; `statement_timeout`; network-limited in `pg_hba` | Low for integrity, Medium for confidentiality of unpublished data | DB-1..DB-5, API-4, DEP-1 |

### 5.4 Administrators, backups and audit

| ID | Threat | Path | Impact | Existing control | Proposed control | Residual | Tests |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T-17 | **Malicious administrator** | TA7 with the superuser or host root | Anything, including forging reviews with recomputed hashes | None | Detective only: an external anchor held outside the database operator's control; server logs shipped off the host; an integrity check run by another person; ideally the owner and the reviewer are different people | **High residual. Can't be prevented in the app or the DB (D5)** | AUD-1..AUD-4 |
| T-18 | **Backup restore rollback** | Restore an older dump | Later reviews silently undone; an old state shown | None | Signed, versioned backups; compare the restored audit head with the latest anchor before reopening; restore runs as the owner, never `--disable-triggers` in production | Medium | AUD-4, DEP-6 |
| T-19 | **Audit log tampering** | TA7 updates or deletes `security_audit_log` | Lost detection | n/a | Append-only and TRUNCATE guards; hash chain; an external anchor; server logs off-host | Medium (TA7 can rewrite the database, not the anchor) | AUD-1, AUD-2 |

### 5.5 Network, application and supply chain

| ID | Threat | Path | Impact | Existing control | Proposed control | Residual | Tests |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T-20 | **Unauthenticated remote access** | TA1 reaches a pilot host | A7 exposed | `127.0.0.1` bindings only | VPN, then the proxy with OIDC; no backend or DB host ports; a pilot-mode header check in the API | Low | API-1, API-2, DEP-3, DEP-4 |
| T-21 | **Local path disclosure** | Anyone reading `/companies/{id}/evidence` | A8 (TESTED, SEC-03) | None | The `api.evidence` view returns http(s) URLs only; the importer refuses `file://` for real data | Low | API-4 |
| T-22 | **Display field forged** | Any role with `UPDATE` on `companies`/`securities` writes `last_verified_at` | False "Last verified" on the page (Arch §1.3) | None (set by the application, not the database) | Stamped by the review procedure only; a guard trigger refuses other changes; no U grants | Low | DB-12 |
| T-23 | **Supply-chain change** | TA8 swaps a tag | Code execution in CI or the image | `permissions: contents: read`; lockfiles | SHA/digest pinning; branch protection; a human review (SEC-06, SEC-07) | Low/Medium | DEP-7 |
| T-24 | **Credentials in env and logs** | `docker inspect`, crash logs | A6 | The health check logs the type only | Compose secrets (`*_FILE`); no URL logging; per-process URLs | Low | DEP-1, DEP-5 |

## 6. What can't be prevented by application or database controls

- **T-6, credential sharing.** It needs personal credentials and an appointed, independent reviewer
  (Q-3, HUMAN DEPENDENCY).
- **T-17, a malicious superuser, owner or host root.** Controls can only make tampering
  *detectable*, and only if the external anchor and the integrity check are held by someone the
  administrator does not control. While the owner is also the operator and the only reviewer
  candidate, that separation does not exist (D5, D13).
- **A reviewer who doesn't actually check the document.** `checked_against` records a claim, not
  diligence.

## 7. Risk summary

| Rating | Today (localhost, no real data) | Pilot with current code | After Stages 1–3 |
| --- | --- | --- | --- |
| High | — | T-1, T-10 (P5), T-11, T-14 (P6e), T-17, T-20 if exposed | T-17 (accepted, detective) |
| Medium | T-1, T-10, T-17 (no real data, so impact is limited) | T-12, T-13, T-16, T-18, T-22 | T-4, T-6, T-7, T-12, T-15, T-16 (confidentiality), T-18, T-19 |
| Low | the rest | T-21, T-23, T-24 | the rest |
