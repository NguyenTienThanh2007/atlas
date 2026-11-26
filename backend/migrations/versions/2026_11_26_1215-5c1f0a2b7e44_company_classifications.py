"""company classifications (WS4-4 Phase A, decisions WS4-4-D1, D2, D7, D9)

A company is a bank, a non-bank or another financial company only when a reviewed record says so.
`company_classifications` holds those records:
- append-only (the existing `atlas_reject_history_change` trigger); a correction is a new row with
  `supersedes_id`, and the unique `supersedes_id` plus one first row per company keep each
  company's records in one linear chain, whose last row is current;
- two people (curator ≠ reviewer, reviewer a person), as for verification reviews;
- the cited evidence must be about the same company, have the company's sample/real class, and not
  be disputed, rejected or superseded when the record is made. A superseding row must belong to the
  same company. The check takes `FOR SHARE` on the company row, as the isolation triggers do.

No existing table or row changes: every company starts unclassified. Downgrade drops the table,
its triggers and function; classifications recorded after the upgrade are lost on downgrade.

Revision ID: 5c1f0a2b7e44
Revises: 8de09b58f4c2
Create Date: 2026-11-26 12:15:51.484605

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5c1f0a2b7e44"
down_revision: str | Sequence[str] | None = "8de09b58f4c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "company_classifications"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "bank",
                "non_bank",
                "other_financial",
                name="company_kind",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("basis", sa.Text(), nullable=False),
        sa.Column("curator", sa.String(length=120), nullable=False),
        sa.Column("reviewer", sa.String(length=120), nullable=False),
        sa.Column("supersedes_id", sa.Uuid(), nullable=True),
        sa.Column(
            "decided_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.CheckConstraint("btrim(basis) <> ''", name=op.f(f"ck_{TABLE}_basis_present")),
        sa.CheckConstraint(
            "btrim(curator) <> '' AND btrim(reviewer) <> ''", name=op.f(f"ck_{TABLE}_names_present")
        ),
        sa.CheckConstraint(
            "lower(btrim(reviewer)) !~ '^(system|atlas|auto|automated|automatic|bot|import|"
            "importer|ingestion|claude|ai)$'",
            name=op.f(f"ck_{TABLE}_reviewer_is_a_person"),
        ),
        sa.CheckConstraint(
            "lower(btrim(curator)) <> lower(btrim(reviewer))",
            name=op.f(f"ck_{TABLE}_curator_is_not_reviewer"),
        ),
        sa.CheckConstraint("supersedes_id <> id", name=op.f(f"ck_{TABLE}_not_own_successor")),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f(f"fk_{TABLE}_company_id_companies"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            ["evidence.id"],
            name=op.f(f"fk_{TABLE}_evidence_id_evidence"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_id"],
            [f"{TABLE}.id"],
            name=op.f(f"fk_{TABLE}_supersedes_id_{TABLE}"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f(f"pk_{TABLE}")),
        sa.UniqueConstraint("supersedes_id", name=f"uq_{TABLE}_supersedes_id"),
    )
    op.create_index(f"ix_{TABLE}_company", TABLE, ["company_id", "decided_at"], unique=False)
    op.create_index(
        f"uq_{TABLE}_first",
        TABLE,
        ["company_id"],
        unique=True,
        postgresql_where=sa.text("supersedes_id IS NULL"),
    )
    op.execute(
        f"CREATE TRIGGER {TABLE}_append_only BEFORE UPDATE OR DELETE ON {TABLE} "
        "FOR EACH ROW EXECUTE FUNCTION atlas_reject_history_change()"
    )
    op.execute(
        """
        CREATE FUNCTION atlas_check_classification() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE
            company_sample boolean;
            ev_type text;
            ev_entity uuid;
            ev_status text;
            previous_company uuid;
        BEGIN
            SELECT is_sample INTO company_sample FROM companies
             WHERE id = NEW.company_id FOR SHARE;
            SELECT entity_type, entity_id, verification_status
              INTO ev_type, ev_entity, ev_status
              FROM evidence WHERE id = NEW.evidence_id;
            IF company_sample IS NULL OR ev_type IS NULL THEN
                RETURN NEW;  -- missing rows are left to the foreign keys
            END IF;
            IF ev_type <> 'company' OR ev_entity <> NEW.company_id THEN
                RAISE EXCEPTION 'classification of company % must cite evidence about that '
                    'company (evidence % is about % %)', NEW.company_id, NEW.evidence_id,
                    ev_type, ev_entity USING ERRCODE = 'check_violation';
            END IF;
            IF (ev_status = 'sample') <> company_sample THEN
                RAISE EXCEPTION 'sample/real isolation: classification of company % '
                    '(is_sample=%) cannot cite evidence with status %', NEW.company_id,
                    company_sample, ev_status USING ERRCODE = 'check_violation';
            END IF;
            IF ev_status IN ('disputed', 'rejected', 'superseded') THEN
                RAISE EXCEPTION 'classification cannot rest on % evidence %', ev_status,
                    NEW.evidence_id USING ERRCODE = 'check_violation';
            END IF;
            IF NEW.supersedes_id IS NOT NULL THEN
                SELECT company_id INTO previous_company FROM company_classifications
                 WHERE id = NEW.supersedes_id;
                IF previous_company IS NOT NULL AND previous_company <> NEW.company_id THEN
                    RAISE EXCEPTION 'classification % belongs to another company',
                        NEW.supersedes_id USING ERRCODE = 'check_violation';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        f"CREATE TRIGGER {TABLE}_check BEFORE INSERT ON {TABLE} "
        "FOR EACH ROW EXECUTE FUNCTION atlas_check_classification()"
    )


def downgrade() -> None:
    op.execute(f"DROP TRIGGER {TABLE}_check ON {TABLE}")
    op.execute("DROP FUNCTION atlas_check_classification()")
    op.execute(f"DROP TRIGGER {TABLE}_append_only ON {TABLE}")
    op.drop_index(
        f"uq_{TABLE}_first", table_name=TABLE, postgresql_where=sa.text("supersedes_id IS NULL")
    )
    op.drop_index(f"ix_{TABLE}_company", table_name=TABLE)
    op.drop_table(TABLE)
