# SEC-01A Stage 0: owner decisions

**Status: OWNER DECISIONS REQUIRED — STAGE 1 NOT AUTHORIZED.**

- None of the D1–D13 proposals in this file is approved. The separate G-0 scope amendment is recorded in `PRODUCT_DECISIONS.md` §5.
- Each "Proposal" is the design team's recommendation. It becomes a decision only when the owner
  records it in [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) as a new dated section (gate G-0 in
  [SEC_01A_IMPLEMENTATION_PLAN.md](SEC_01A_IMPLEMENTATION_PLAN.md) §9).
- Written by an AI assistant. It is not a human review.

## 1. Baseline (VERIFIED FACT)

| | |
| --- | --- |
| Commit | `main` @ `e9db10ca15225142f6883f48faec7433491f4f72` (PR #14 merge, 0 reviews) |
| Branch | `docs/sec-01a-stage-0-decisions`, cut from that commit for this document. It is not an implementation branch, and no PR was opened |
| Working tree | Clean before this document |
| SEC-01A documents on `main` | [SEC_01A_SECURITY_ARCHITECTURE.md](SEC_01A_SECURITY_ARCHITECTURE.md) ("Arch"), [SEC_01A_THREAT_MODEL.md](SEC_01A_THREAT_MODEL.md) ("TM"), [SEC_01A_IMPLEMENTATION_PLAN.md](SEC_01A_IMPLEMENTATION_PLAN.md) ("Plan"). The dated SEC-01A note is at the end of [SECURITY_REMEDIATION_CHECKLIST.md](SECURITY_REMEDIATION_CHECKLIST.md) |
| Security decisions in PRODUCT_DECISIONS | None. No SEC-* decision exists. Sections run to §2f (WS4-4, approved 2026-11-26) |
| Existing approved decisions this work must respect | **D-6:** two-person verification for financial figures. **EX-2:** append-only reviews, curator ≠ reviewer in the database, local-only review tool, no public review API. **WS4-4-D7:** two people per classification. **A-6:** private pilot, nothing published before G1 |
| Open questions this work depends on | **Q-3** (who the second reviewer is), **Q-7** (hosting and budget) |
| Pilot companies | Called Company 1–5 only. The private G2 workspace was not opened |

**Decision numbering.** The brief for this document renames one decision. In Plan §1, D3 was
"where accounts are managed". Here D3 is "local development and CLI authentication", and the old D3
question is folded into D2. D1, D2 and D4–D13 keep their meaning.

## 2. Technical consistency audit (before any approval)

### 2.1 How the checks were run

The ten questions in the brief were checked two ways:
- statically, against the repository;
- dynamically, on a **new, disposable** PostgreSQL 17.12 container (`atlas-stage0-testpg`, never
  published to a host port, stopped afterwards).

No existing database was touched. Results T1–T14 are TESTED FACT for that version. The production
image is `postgres:17-alpine` (`docker-compose.yml:8`).

### 2.2 Results

| # | Question | Finding | Label | Effect on the design |
| --- | --- | --- | --- | --- |
| 1 | Migrator membership and `SET ROLE` on PG 17 | Since PG 16, inherit and set are **options of each grant**. A role's NOINHERIT attribute only sets the default for future grants. T1: `GRANT atlas_owner TO atlas_migrator` on a NOINHERIT migrator gave `inherit=false, set=true`, which is what Arch §3.1 wants. **But a migrator acting as owner can't take over or replace objects owned by the superuser.** T2: `CREATE OR REPLACE FUNCTION` and `ALTER TABLE … OWNER TO atlas_owner` both fail with "must be owner". After the superuser reassigns ownership, the owner can replace functions (T3) | TESTED | **Inconsistency C-1:** Plan Stage 1 puts "reassign ownership" inside migration M1, run as the migrator. It must be a bootstrap-superuser step done before M1. **C-4:** write the grant explicitly: `WITH INHERIT FALSE, SET TRUE` |
| 2 | Is `session_user` a safe actor identity inside `SECURITY DEFINER`? | T6/T7: inside a definer function, `session_user` is the login (`p_a`, `p_b`) and `current_user` is the owner. T12: a non-superuser can't `SET SESSION AUTHORIZATION` ("permission denied") and can't `SET ROLE` to a role it isn't a member of. Safe **only when each person connects with their own login**. A procedure called by the migrator sees `session_user = atlas_migrator` and must refuse it as "not a principal" | TESTED | Holds for the planned direct CLI connections. Breaks under any shared login, gateway or pooler (Q4). Already noted in Arch §4.1 option 5 |
| 3 | Membership checks with NOINHERIT | T5: a NOINHERIT person granted `atlas_reviewers` **can't call a function whose EXECUTE was granted to the group** ("permission denied"). T7: `GRANT atlas_reviewers TO p_b WITH INHERIT TRUE, SET FALSE` lets the call through and refuses `SET ROLE atlas_reviewers`. `pg_has_role(session_user, g, 'MEMBER')` is true in both cases; `'USAGE'` is false when inherit is false | TESTED | **Inconsistency C-3:** with Arch §3.1 as written (person NOINHERIT plus EXECUTE on the group), the reviewer could not review. Fix: grant group membership `WITH INHERIT TRUE, SET FALSE` (the groups hold only EXECUTE), and check `'MEMBER'` in procedures |
| 4 | Could pooling reuse a human session? | `backend/app/db.py:24-31`: one SQLAlchemy engine (default QueuePool) per process. The CLI is one process per run, so a person's pool holds only their connections. No external pooler exists (VERIFIED). INFERENCE: a long-lived service holding several people's connections, or a single-login pooler, would make `session_user` the service. PgBouncer pools per user and database, so it would not mix users, but it adds a component in the trust path | VERIFIED / INFERENCE | **C-11:** add a rule: `p_*` roles connect directly, one process per person, with no shared pool or pooler. Any later web review UI is option 5 (Arch §4.1), which needs its own decision |
| 5 | Do API views keep SQLAlchemy working? | Plan §2 says `models.py` changes to "view-backed read models or `schema=`". Setting `schema='api'` on the models would change `Base.metadata`, which drives `alembic check` and the superuser test suite, so it would break both (INFERENCE). Tested alternative (T10): put views **with the same names** in schema `api` and set `ALTER ROLE atlas_api SET search_path = api`. Unqualified `SELECT … FROM ev` then reads the view, and `public.ev` is denied to the API role (T10b), so a client overriding `search_path` gains nothing. The ORM selects every mapped column, so each view must expose every mapped column under the same name (INFERENCE) | TESTED (PG part) / INFERENCE (ORM part) | **Inconsistency C-8:** the "change only their schema" assumption (Arch §3.4) is unsupported. Use role `search_path` and same-name views, with no model change. A Stage 1 spike must run the API test suite **as `atlas_api`**: today `test_api.py` runs as the superuser on `public` and would not catch a view mismatch |
| 6 | Do default privileges cover future objects? | T11: `ALTER DEFAULT PRIVILEGES FOR ROLE atlas_owner REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC` covers functions **created later by `atlas_owner`** (PUBLIC can't execute them). **Existing functions keep PUBLIC EXECUTE** (`old_fn: true`). T4: objects created after `SET ROLE atlas_owner` are owned by `atlas_owner`. If a migration forgets `SET ROLE`, the migrator owns the object and the default privileges don't apply | TESTED | **C-10:** M1 needs an explicit `REVOKE EXECUTE … FROM PUBLIC` on every existing function. `env.py` must `SET ROLE` before any DDL. DB-13 must also assert "no object owned by `atlas_migrator`". Use explicit per-view `GRANT SELECT`, not a schema-wide default grant, so a new table is never exposed by accident |
| 7 | Is the proposed `search_path` safe in definer functions? | `pg_catalog, public, pg_temp` with `pg_temp` last is the documented safe pattern **only while no untrusted role can CREATE in `public`**. VERIFIED: PUBLIC has no CREATE on `public`, which is owned by `pg_database_owner`, the database owner `atlas` (T13). T14: TEMP is granted to PUBLIC by default, so Arch §3.2's REVOKE is needed. **T8: a `SECURITY DEFINER` trigger always sees `current_user` = owner.** So the proposed guard "status may change only when `current_user = atlas_owner`" is meaningless if the guard itself is a definer. T9: an **invoker** trigger fired by a definer procedure's UPDATE sees `current_user = atlas_owner`, and sees the caller otherwise | TESTED | **Inconsistency C-5:** Arch §3.2 says "every security function becomes `SECURITY DEFINER`". Correct design: **trigger functions stay INVOKER**, with a pinned `search_path` and qualified names. Only the entry procedures (`atlas_record_review`, the import and classification procedures) are DEFINER |
| 8 | Do backups and external anchors give meaningful detection? | INFERENCE (not tested): an anchor detects a rollback restore or rewritten history **only for changes made before the latest anchor**, and only if the anchor is held by someone the operator can't overwrite. While the owner, operator and anchor holder are one person, the detection protects against outsiders and accidents, not against the owner. `pg_dumpall --globals-only` (needed to restore roles) carries role password hashes (PostgreSQL documentation; not tested), so backups become credential material | INFERENCE | **C-12:** state the window (changes after the last anchor are undetectable). Store role dumps encrypted and separately. D5/D13 decide who holds the anchor |
| 9 | Can migrations roll back after ownership changes? | T3: `atlas_owner` can't give ownership back to the superuser ("must be able to SET ROLE atlas"). Plan §3 M1 ("down restores … ownership") and §6 Stage 1 can't run as the migrator | TESTED | **Inconsistency C-2:** M1's downgrade must leave ownership with `atlas_owner` (harmless to a superuser runtime) and restore only function bodies and grants. Returning ownership is a manual bootstrap-superuser step |
| 10 | Does role provisioning work on fresh and existing volumes? | VERIFIED: `infra/postgres/init/01-create-test-db.sh:2` runs "once, on first initialisation of an empty data volume". The user's stack exists and is at `31b1317163eb` (read-only check, earlier). Plan §2 proposes `python -m app.ops roles` for existing volumes, but that tool would need the **superuser password in the app environment**, which Arch §5.2 forbids. T-pg_hba (VERIFIED on a fresh `postgres:17-alpine`): `local all all trust` and `host all all 127.0.0.1/32 trust` inside the container, `scram-sha-256` from elsewhere. So `docker compose exec db psql -U "$POSTGRES_USER"` is a superuser shell **without a password** | VERIFIED / TESTED | **C-6:** existing volumes are provisioned by the operator via `docker compose exec db psql -f roles.sql` (idempotent). Fresh volumes use an init script. Both use the same SQL file; the app tool is dropped. **C-7 (new risk):** anyone who can `docker exec` into the db container, i.e. the host's Docker group, is a database superuser. A custom `pg_hba.conf` (no `trust`) belongs in Stage 1. Docker-group membership is root-equivalent and belongs to TM T-17 |
| — | Extra: roles are cluster-wide | The test database `atlas_test` lives in the same cluster (`01-create-test-db.sh`). PUBLIC's default CONNECT and TEMP also apply there and in `postgres` | VERIFIED / TESTED (T14) | **C-9:** revoke CONNECT and TEMP from PUBLIC on **every** database in the cluster, not only `atlas` |

**Unsupported assumptions found:** C-1, C-2, C-3, C-5, C-6, C-8 (factual inconsistencies). C-4 is
a clarification. C-7, C-9, C-10, C-11 (the no-shared-pool rule from Q4) and C-12 are gaps. C-13 (added in final
validation) is a gate-scope inconsistency: D7 and D11 affect Stage 1 but were not in G-0. The corrections are recorded as a dated section in Plan §0. Arch and
TM are left as merged; the Plan correction section supersedes the affected Arch sentences
(§3.1 NOINHERIT groups, §3.2 "every security function", §3.4 schema mapping).

## 3. Decisions for the owner

**What "Blocks" means in each decision below.** The decision must be recorded before that stage
starts, or before G2 real-pilot data is loaded.

### D1: database ownership and role model

- **Proposal:**
  - `atlas_owner` is NOLOGIN and owns everything.
  - `atlas_migrator` is a member of `atlas_owner` (`INHERIT FALSE, SET TRUE`) and is used only by a
    one-shot migration job.
  - `atlas_api` is read-only and reads same-name views in schema `api` through its role
    `search_path`.
  - Group roles `atlas_curators` and `atlas_reviewers` hold only EXECUTE.
  - Every person has their own login (`p_*`), joined to the groups with `INHERIT TRUE, SET FALSE`.
  - The bootstrap superuser stays offline (Arch §3.1, corrected by C-1, C-3, C-8).
- **Benefits:** together with D2 (P7) and D4 (P5, P6e), it closes the tested bypasses for every
  role except the superuser and the owner. P9 stays possible for the owner only (Arch §2.3,
  D5). The API can't write. Migration credentials leave the API container.
- **Risks and trade-offs:**
  - More roles and grants to maintain.
  - The ownership transfer needs a superuser step.
  - The API views must match the ORM columns exactly (C-8 spike).
  - The superuser and the owner can still bypass everything (D5).
- **Dependencies:** none.
- **Owner must approve:**
  1. the principal list and its attributes;
  2. that the bootstrap superuser is never used at runtime;
  3. same-name `api` views read through the role `search_path`;
  4. the superuser-run provisioning and ownership transfer (C-1, C-6).
- **Blocks:** Stage 1.

### D2: human identity, one PostgreSQL login per person

- **Proposal:** for the pilot, option 3 (Arch §4.1).
  - Each curator and reviewer has a personal `p_<id>` login.
  - Procedures take the actor from `session_user` and never from arguments.
  - A `principals` table (stable UUIDs, never deleted) and an append-only role-event log are
    managed inside ATLAS by the owner. This folds in Plan D3, "where accounts are managed".
  - An external IdP is only for proxy sign-in (D8).
- **Benefits:**
  - The database itself proves which login acted (T6, T12).
  - No web write surface, consistent with EX-2.
  - Practical for 2–3 people.
- **Risks and trade-offs:**
  - A login proves who holds the credential, not who is at the keyboard (TM T-6).
  - Awkward beyond a few people.
  - A later web review UI needs a new decision (option 5, gateway trust).
  - The `--curator` and `--reviewer` CLI flags go away (breaking change for operators).
- **Dependencies:** D1, D8.
- **Owner must approve:**
  1. option 3 for the pilot;
  2. ATLAS-managed principals;
  3. the rule that `session_user` is the only actor source;
  4. the rule that legacy evidence without an authenticated curator can't be newly verified until
     it is re-imported (Arch §4.4).
- **Blocks:** Stage 2.

### D3: local development and CLI authentication

- **Proposal:**
  - **Local development uses the same role model as production**, so the negative tests run every
    day.
    - A dev provisioning SQL creates `atlas_owner`, `atlas_migrator`, `atlas_api` and two fictional
      people, `p_dev_curator` and `p_dev_reviewer`, with dev-only passwords kept in git-ignored
      files.
    - The test suite keeps a superuser harness for fixtures that need replica mode.
    - A separate role-test harness connects as the real roles.
  - **The CLI** connects as the person.
    - The password is prompted, or comes from a per-user `~/.pgpass` with mode 0600, or a client
      certificate (D8).
    - It is never read from the repository `.env`.
    - `.env` keeps only per-process service URLs.
  - **Until Stage 2 lands,** the CLI in local dev keeps the old shared login, and that is documented
    as a known gap (Plan Stage 1 task 6).
- **Benefits:**
  - The production model is exercised locally.
  - No human credentials in `.env`.
  - Dev and CI behave alike.
- **Risks and trade-offs:**
  - More local setup steps.
  - Existing volumes need the operator provisioning step (C-6).
  - Dev passwords must never be reused anywhere else.
- **Dependencies:** D1, D2, D8.
- **Owner must approve:**
  1. the same role model locally;
  2. fictional dev people;
  3. the CLI credential sources;
  4. accepting the gap until Stage 2 lands.
- **Blocks:** Stage 1 (dev provisioning) and Stage 2 (CLI authentication).

### D4: security-definer procedures and the import architecture

- **Proposal:**
  - All writes to protected tables go through `SECURITY DEFINER` entry procedures owned by
    `atlas_owner`, with `SET search_path = pg_catalog, public, pg_temp` and schema-qualified names.
  - **Trigger functions stay SECURITY INVOKER** (C-5).
  - The evidence guard allows a status change only when `current_user = 'atlas_owner'`. That is
    true inside a definer procedure (T9), and also for the migration job acting as `atlas_owner`,
    which is trusted under D5.
  - Import becomes **per-record procedures** called from the existing Python importer, so its
    validation, savepoints and issue reporting (`importer.py:124-138`) stay.
  - No runtime role holds UPDATE, DELETE or TRUNCATE on any table.
  - TEMP and CONNECT are revoked from PUBLIC on every database (C-9).
- **Benefits:**
  - Closes the P5 (trigger-depth) and P6e (`pg_temp` shadowing) bypasses.
  - Runtime roles need no table privileges.
- **Risks and trade-offs:**
  - The largest rewrite: import transaction semantics must survive.
  - A definer bug runs with owner rights, so every procedure needs negative tests.
  - Procedures must refuse callers that aren't principals (the migrator, the owner).
- **Dependencies:** D1.
- **Owner must approve:**
  1. procedures-only writes;
  2. per-record import procedures rather than one bundle procedure;
  3. invoker triggers with the `current_user` guard.
- **Blocks:** Stage 1 (function hardening, guard) and Stage 2 (procedures).

### D5: the privileged-operator threat and tamper detection

- **Proposal:**
  - **Accept for the pilot that the superuser and the owner can't be prevented** from changing
    data (TM T-17), and detect it instead:
    - a DDL event trigger;
    - a hash-chained `security_audit_log`;
    - a daily external anchor;
    - a read-only integrity check;
    - server logs kept off the database host.
  - Before G1, separate duties: someone other than the operator holds the anchor and runs the
    integrity check.
  - Replace the image's `trust` lines in `pg_hba.conf` (C-7).
- **Benefits:** makes the main tested bypasses detectable after the fact (P5 shows as status
  `verified` with no review; P9 as a disabled trigger).
- **Risks and trade-offs:**
  - Detection only.
  - Worthless against the owner while the owner holds the anchor (C-12).
  - Changes after the last anchor are undetectable.
  - The event trigger needs the superuser to install.
- **Dependencies:** D13 (a second trusted person), D10.
- **Owner must approve:**
  1. accept the detective-only residual risk for the pilot;
  2. who holds the anchor and where it lives;
  3. the separation-of-duties target before G1;
  4. the custom `pg_hba.conf`.
- **Blocks:** G2 (accepting the risk). Its own work is Stage 4, except the `pg_hba` change, which
  is Stage 1.

### D6: remote pilot access stays disabled until Q-7 is resolved

- **Proposal:** no access from beyond localhost until all of these hold:
  1. Q-7 (hosting and budget) is decided;
  2. Stage 3 passes: VPN with personal device keys, a TLS reverse proxy with OIDC sign-in, no
     backend or database host ports, `hostssl` only for `p_*` roles from the VPN range.

  Ports stay on `127.0.0.1` (VERIFIED, `docker-compose.yml:15,34,51`).
- **Benefits:** unpublished pilot data (A-6) is never reachable from the network.
- **Risks and trade-offs:** curator and reviewer must share the host machine, or wait, until Q-7.
  That could delay G2 if they aren't co-located.
- **Dependencies:** Q-7, D8.
- **Owner must approve:**
  1. "no remote access before Q-7 and Stage 3";
  2. what counts as "localhost only" (for example, no SSH tunnels shared with others).
- **Blocks:** Stage 3. G2 too, if the reviewer is remote.

### D7: staged remediation scope

**Status: APPROVED by the project owner, 2026-11-26.**

- **Decision:** adopt the staged remediation sequence:
  - SEC-03 (local paths) comes with Stage 1: the `api.evidence` view returns `null` for
    non-HTTP(S) URLs. The API behaviour change is approved.
  - SEC-10 (identity) comes with Stage 2.
  - SEC-09 (disable pilot API docs) comes with Stage 3.
  - SEC-04, SEC-05 and SEC-06 are Stage 4.
  - SEC-07: protect `main` now. Require PRs, at least one approving human review,
    dismissal of stale approvals, resolved conversations, and prohibit force-pushes
    and branch deletion. Do not allow routine administrator bypass. Select required
    CI checks only after confirming their stable names.
- **Benefits:** keeps each change reviewable. The privacy fix comes with the views.
- **Risks and trade-offs:** low findings remain open longer; the SEC-03 response behaviour
  changes for non-HTTP(S) source URLs.
- **Dependencies:** D1.
- **Operational note:** branch-protection policy is approved, but the GitHub settings
  change is still pending; it must be applied in repository settings.
- **Blocks:** Stage 1 for SEC-03 and D1; otherwise it fixes the scope of Stages 1–4.

### D8: database credentials, TLS and authentication policy

- **Proposal:**
  - **Person roles:** client certificates (`pg_hba` `cert`) if hosting allows, otherwise
    `scram-sha-256` passwords in each person's own password manager. Plus `VALID UNTIL` 90 days,
    connection limit 1, `idle_session_timeout`.
  - **Service roles:** secret files (Compose `secrets:`), one per process, rotated after each
    release (OPEN QUESTION).
  - **No `trust` lines** (C-7). `hostssl` for anything beyond the Docker network.
  - **Proxy:** OIDC with MFA, 8-hour sessions, `Secure`/`HttpOnly`/`SameSite=Lax` cookies.
- **Benefits:** personal and revocable credentials, and no shared secrets.
- **Risks and trade-offs:**
  - Certificates need a small CA and renewal.
  - Passwords can be shared (TM T-6).
  - The IdP choice depends on Q-7 (no provider chosen).
- **Dependencies:** Q-7 (for TLS and the IdP).
- **Owner must approve:**
  1. certificates or passwords;
  2. expiry and rotation periods;
  3. MFA for the VPN and the IdP;
  4. removing `trust` from `pg_hba`.
- **Blocks:** Stage 2 (person credentials) and Stage 3 (proxy, TLS).

### D9: personal-data retention and revocation

- **Proposal:**
  - `principals` rows and the NOLOGIN roles are kept forever, so every review stays attributable.
  - Only display name and role are stored.
  - Revocation means: `ALTER ROLE … NOLOGIN`, revoke group membership, `status = 'revoked'`, an
    audit row, and ending open sessions.
  - Reviews recorded before a revocation stay valid. After a compromise, every decision in the
    suspected window is re-reviewed.
- **Benefits:** accountability survives staff changes.
- **Risks and trade-offs:** personal data is kept indefinitely. Vietnamese personal-data rules may
  apply, which needs a legal check (OPEN QUESTION, outside this design).
- **Dependencies:** D2.
- **Owner must approve:**
  1. the retention period;
  2. the stored fields;
  3. the revocation procedure;
  4. whether a legal check is needed.
- **Blocks:** Stage 2.

### D10: backup and recovery

- **Proposal:**
  - Before every stage, and daily during G2: an **encrypted**, versioned `pg_dump`.
  - Role definitions go in a separate encrypted dump, because they carry password hashes (C-12).
  - After any restore: compare the restored audit head with the latest anchor, and run the
    integrity check before reopening.
  - Never restore with `--disable-triggers` in production.
  - Restores are tested on a disposable database.
- **Benefits:** recovery without silently undoing reviews.
- **Risks and trade-offs:**
  - Storage location and cost depend on Q-7.
  - Backup keys become critical secrets.
  - Changes after the last anchor are lost to detection.
- **Dependencies:** D5, Q-7.
- **Owner must approve:**
  1. backup frequency, encryption and location;
  2. the restore check procedure.
- **Blocks:** G2 (before real data).

### D11: migration rollback

**Status: APPROVED by the project owner, 2026-11-26.**

- **Decision (corrected by C-2):**
  - **Stage 1 (M1):** the downgrade restores the old function bodies and grants, and **leaves
    ownership with `atlas_owner`**. It must not attempt to hand ownership back to the bootstrap
    superuser. Returning ownership, if ever needed, is a separate manual bootstrap-superuser step.
  - **Stage 2 (M2):** a forward fix is preferred. The downgrade refuses if authenticated reviews
    exist; if recovery is required after authenticated reviews exist, restore from a verified
    pre-migration backup under the approved recovery procedure.
  - **Before each stage:** create and record a verified pre-migration backup and integrity-check
    result. D10's broader backup, retention and anchor policy remains a separate decision before G2.
- **Benefits:** rollback cannot discard authenticated review history.
- **Risks and trade-offs:** M1 is intentionally non-symmetric (ownership stays with `atlas_owner`);
  Stage 2 recovery relies on a verified backup.
- **Dependencies:** a verified pre-migration backup for each stage; D10's broader policy before G2.
- **Owner approved:** the non-symmetric M1 downgrade and backup-based Stage 2 recovery.
- **Blocks:** Stage 1.

### D12: acceptance criteria before real pilot data

- **Proposal:** Plan §7 "Before real pilot data", plus:
  1. the C-8 spike (the API suite passes as `atlas_api` through the views);
  2. C-7 done (no `trust`);
  3. DB-13 extended with "no object owned by `atlas_migrator`";
  4. C-9 done (CONNECT and TEMP revoked on every database).
- **Benefits:** a single checkable gate (G-3).
- **Risks and trade-offs:** G2 starts later.
- **Dependencies:** D1–D4, D8, D10, D13.
- **Owner must approve:** the list as the G-3 gate.
- **Blocks:** G2.

### D13: appointing an independent human reviewer

- **Proposal:**
  - Appoint a named person (Q-3) before any G2 review.
  - Ideally not the database operator, so they can also hold the anchor (D5).
  - They get their own `p_*` login (D2) and sign a short independence and conflict-of-interest
    declaration (G2 runbook P0-8).
  - AI reviews never count as this reviewer (AU-6).
- **Benefits:** without this person nothing can become `verified` (D-6), and two-person
  verification exists in name only.
- **Risks and trade-offs:** finding and keeping someone qualified; that person's availability sets
  the G2 pace.
- **Dependencies:** Q-3.
- **Owner must approve:**
  1. who the reviewer is (recorded privately, not in this public repo, if they prefer);
  2. their independence terms.
- **Blocks:** G2 (verification). It does not block engineering.

## 4. Summary

| Decision | Blocks | Depends on |
| --- | --- | --- |
| D1 Role model | Stage 1 | — |
| D2 Personal logins | Stage 2 | D1, D8 |
| D3 Local dev and CLI authentication | Stages 1, 2 | D1, D2, D8 |
| D4 Definer procedures and import | Stages 1, 2 | D1 |
| D5 Privileged operator | G2 (`pg_hba` in Stage 1) | D10, D13 |
| D6 No remote access before Q-7 | Stage 3 (G2 if the reviewer is remote) | Q-7, D8 |
| D7 Staged scope | Stage 1 (SEC-03 API change); SEC-07 GitHub setting approved, operational action pending | D1 |
| D8 Credentials, TLS, authentication | Stages 2, 3 | Q-7 |
| D9 Retention and revocation | Stage 2 | D2 |
| D10 Backup and recovery | G2 | D5, Q-7 |
| D11 Migration rollback | Stage 1; verified pre-migration backup required | D10 (broader policy before G2) |
| D12 Acceptance before real data | G2 | D1–D4, D8, D10, D13 |
| D13 Independent reviewer | G2 | Q-3 |

**Gate G-0 (owner-approved scope amendment, 2026-11-26; recorded in PRODUCT_DECISIONS.md §5):**
D1–D4, D6–D8 and D11 must be explicitly decided and recorded before any SEC-01A code.

This approval changes the *scope of the gate only*. It does **not** approve the substantive
proposals in D7 or D11 (or any other D1–D13 proposal). D7's SEC-03 API behaviour change
(`source_url` becomes `null` for non-http(s) URLs) and D11's non-symmetric M1 downgrade
(leaves ownership with `atlas_owner`) each still require an explicit owner decision before
implementation. Plan §9 and C-13 in Plan §0 reflect the expanded gate.

**Still PROPOSALS / not approved:** D1, D2, D3, D4, D5, D6, D8, D9, D10, D12 and D13.
D7 and D11 are approved by the owner on 2026-11-26, as recorded in
[PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §6. Approval of D7 and D11 does not satisfy G-0
by itself; D1–D4, D6 and D8 remain outstanding.

**OWNER DECISIONS REQUIRED — STAGE 1 NOT AUTHORIZED.**
