"""sample/real isolation (WS4-2 audit AU-3)

A company is either a sample (fictional fixture) company or a real one (`companies.is_sample`).
Its evidence, and the evidence behind its financial statements, must have the same
classification: `verification_status = 'sample'` for a sample company, any other status
(unverified, verified, disputed, rejected, superseded) for a real one. Before this migration only
the importer enforced that; a direct database write could mix them (audit AU-3).

Triggers added here, all raising `check_violation`:
- `financial_statements` (insert, update): the statement's source evidence, and any evidence
  already pointing at the statement, must match the company's classification.
- `evidence` (insert): evidence for a company, a security or an existing statement must match
  that company's classification. (update): the sample classification of an evidence row can never
  change.
- `companies` (update of `is_sample`): refused once the company has statements or evidence.
- `securities` (update of `company_id`): refused when the security's evidence would no longer
  match its company.

Concurrency: the statement, evidence and security checks take `FOR SHARE` on the company row,
and a change of `is_sample` takes that row's exclusive lock, so the two can't interleave.

Upgrade first audits existing data and fails, listing record ids only, if anything already
violates the rule. Nothing is repaired, deleted or reclassified. Downgrade drops the triggers
and functions and changes no data.

Revision ID: 8de09b58f4c2
Revises: 31b1317163eb
Create Date: 2026-11-25 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8de09b58f4c2"
down_revision: str | Sequence[str] | None = "31b1317163eb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The company a piece of evidence belongs to (NULL for sector evidence or a statement that does
# not exist yet: the statement trigger checks that case when the statement is inserted).
COMPANY_OF_EVIDENCE = """
    CREATE FUNCTION atlas_company_of_evidence(kind text, entity uuid) RETURNS uuid
    LANGUAGE sql STABLE AS $$
        SELECT CASE kind
            WHEN 'company' THEN (SELECT id FROM companies WHERE id = entity)
            WHEN 'security' THEN (SELECT company_id FROM securities WHERE id = entity)
            WHEN 'financial_statement'
                THEN (SELECT company_id FROM financial_statements WHERE id = entity)
        END
    $$;
"""

# Existing rows that break the rule. Used by upgrade (and by the tests) before any trigger exists.
AUDIT_SQL = """
    DO $$
    DECLARE
        bad_statements int;
        bad_evidence int;
        sample_ids text;
    BEGIN
        CREATE TEMP TABLE atlas_mixed_statements ON COMMIT DROP AS
            SELECT s.id FROM financial_statements s
              JOIN companies c ON c.id = s.company_id
              JOIN evidence e ON e.id = s.source_evidence_id
             WHERE (e.verification_status = 'sample') <> c.is_sample;
        SELECT count(*) INTO bad_statements FROM atlas_mixed_statements;
        SELECT string_agg(id::text, ', ') INTO sample_ids
          FROM (SELECT id FROM atlas_mixed_statements ORDER BY id LIMIT 5) first_ids;
        DROP TABLE atlas_mixed_statements;
        SELECT count(*) INTO bad_evidence
          FROM evidence e
          JOIN companies c ON c.id = atlas_company_of_evidence(e.entity_type::text, e.entity_id)
         WHERE (e.verification_status = 'sample') <> c.is_sample;
        IF bad_statements > 0 OR bad_evidence > 0 THEN
            RAISE EXCEPTION 'sample/real isolation: existing data mixes sample and real records '
                '(statements: %, evidence rows: %; first statement ids: %). Nothing was changed; '
                'resolve these records deliberately before upgrading',
                bad_statements, bad_evidence, coalesce(sample_ids, 'none')
                USING ERRCODE = 'check_violation';
        END IF;
    END $$;
"""

_TRIGGERS = (
    ("financial_statements", "BEFORE INSERT OR UPDATE", "atlas_isolate_statement"),
    ("evidence", "BEFORE INSERT OR UPDATE", "atlas_isolate_evidence"),
    ("companies", "BEFORE UPDATE OF is_sample", "atlas_isolate_company"),
    ("securities", "BEFORE UPDATE OF company_id", "atlas_isolate_security"),
)


def upgrade() -> None:
    op.execute(COMPANY_OF_EVIDENCE)
    op.execute(AUDIT_SQL)

    op.execute(
        """
        CREATE FUNCTION atlas_isolate_statement() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE
            company_sample boolean;
            evidence_sample boolean;
        BEGIN
            SELECT is_sample INTO company_sample FROM companies
             WHERE id = NEW.company_id FOR SHARE;
            SELECT verification_status = 'sample' INTO evidence_sample FROM evidence
             WHERE id = NEW.source_evidence_id;
            -- Missing rows are left to the foreign keys.
            IF company_sample IS NOT NULL AND evidence_sample IS NOT NULL
               AND company_sample <> evidence_sample THEN
                RAISE EXCEPTION 'sample/real isolation: statement % of company % (is_sample=%) '
                    'cannot use evidence % (sample=%)', NEW.id, NEW.company_id,
                    company_sample, NEW.source_evidence_id, evidence_sample
                    USING ERRCODE = 'check_violation';
            END IF;
            IF company_sample IS NOT NULL AND EXISTS (
                SELECT 1 FROM evidence
                 WHERE entity_type = 'financial_statement' AND entity_id = NEW.id
                   AND (verification_status = 'sample') <> company_sample
            ) THEN
                RAISE EXCEPTION 'sample/real isolation: evidence recorded for statement % does '
                    'not match company % (is_sample=%)', NEW.id, NEW.company_id, company_sample
                    USING ERRCODE = 'check_violation';
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE FUNCTION atlas_isolate_evidence() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE
            owner uuid;
            company_sample boolean;
        BEGIN
            IF TG_OP = 'UPDATE' THEN
                IF (OLD.verification_status = 'sample') <> (NEW.verification_status = 'sample') THEN
                    RAISE EXCEPTION 'sample/real isolation: evidence % cannot change between '
                        'sample and real', NEW.id USING ERRCODE = 'check_violation';
                END IF;
                RETURN NEW;
            END IF;
            owner := atlas_company_of_evidence(NEW.entity_type::text, NEW.entity_id);
            IF owner IS NULL THEN
                RETURN NEW;  -- sector evidence, or a statement not inserted yet (checked then)
            END IF;
            SELECT is_sample INTO company_sample FROM companies WHERE id = owner FOR SHARE;
            IF company_sample <> (NEW.verification_status = 'sample') THEN
                RAISE EXCEPTION 'sample/real isolation: % evidence for company % (is_sample=%) '
                    'cannot have status %', NEW.entity_type, owner, company_sample,
                    NEW.verification_status USING ERRCODE = 'check_violation';
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE FUNCTION atlas_isolate_company() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF OLD.is_sample IS DISTINCT FROM NEW.is_sample AND (
                EXISTS (SELECT 1 FROM financial_statements WHERE company_id = NEW.id)
                OR EXISTS (
                    SELECT 1 FROM evidence
                     WHERE atlas_company_of_evidence(entity_type::text, entity_id) = NEW.id
                )
            ) THEN
                RAISE EXCEPTION 'sample/real isolation: company % already has evidence or '
                    'statements; is_sample cannot change', NEW.id
                    USING ERRCODE = 'check_violation';
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE FUNCTION atlas_isolate_security() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE
            company_sample boolean;
        BEGIN
            IF OLD.company_id IS DISTINCT FROM NEW.company_id THEN
                SELECT is_sample INTO company_sample FROM companies
                 WHERE id = NEW.company_id FOR SHARE;
                IF EXISTS (
                    SELECT 1 FROM evidence
                     WHERE entity_type = 'security' AND entity_id = NEW.id
                       AND (verification_status = 'sample') <> company_sample
                ) THEN
                    RAISE EXCEPTION 'sample/real isolation: security % has evidence that does '
                        'not match company % (is_sample=%)', NEW.id, NEW.company_id,
                        company_sample USING ERRCODE = 'check_violation';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )
    for table, timing, function in _TRIGGERS:
        op.execute(
            f"CREATE TRIGGER {table}_sample_isolation {timing} ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION {function}()"
        )


def downgrade() -> None:
    for table, _timing, function in _TRIGGERS:
        op.execute(f"DROP TRIGGER {table}_sample_isolation ON {table}")
        op.execute(f"DROP FUNCTION {function}()")
    op.execute("DROP FUNCTION atlas_company_of_evidence(text, uuid)")
