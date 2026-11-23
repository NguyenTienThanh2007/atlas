"""verification reviews and figure provenance (Phase 2 WS1)

- `verification_reviews`: append-only two-person review decisions; the only way to change
  `evidence.verification_status`. Allowed transitions are enforced here, in the database.
- `rejected` verification state.
- Evidence is immutable apart from review-driven status changes; new evidence starts as
  `unverified` (real) or `sample` (fixture) and can never be inserted as `verified`.
- Per-figure provenance on `financial_metrics`: `source_page`, `reported_value`,
  `reported_scale` (value = reported_value x reported_scale, exactly). Required for real
  figures inserted from now on; existing rows are left untouched (NULL).

See docs/VERIFICATION_WORKFLOW.md.

Revision ID: 31b1317163eb
Revises: 981ec5176312
Create Date: 2026-11-23 19:42:21.295994

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "31b1317163eb"
down_revision: str | Sequence[str] | None = "981ec5176312"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_STATUSES_OLD = "'unverified', 'verified', 'disputed', 'superseded', 'sample'"
_STATUSES_NEW = "'unverified', 'verified', 'disputed', 'rejected', 'superseded', 'sample'"

# (from_status, decision) pairs a review may record. Anything else is refused.
TRANSITIONS = (
    ("unverified", "verified"),
    ("unverified", "rejected"),
    ("unverified", "disputed"),
    ("unverified", "superseded"),
    ("disputed", "verified"),
    ("disputed", "rejected"),
    ("disputed", "unverified"),
    ("disputed", "superseded"),
    ("verified", "disputed"),
    ("verified", "superseded"),
    ("rejected", "unverified"),
)


# Never silently discard review history or figure provenance (tested in test_verification).
DOWNGRADE_GUARD = """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM verification_reviews)
               OR EXISTS (SELECT 1 FROM evidence WHERE verification_status = 'rejected')
               OR EXISTS (SELECT 1 FROM financial_metrics
                          WHERE source_page IS NOT NULL OR reported_value IS NOT NULL) THEN
                RAISE EXCEPTION 'downgrade would discard review history or figure provenance; '
                    'export it and clear it deliberately first';
            END IF;
        END $$;
        """


def upgrade() -> None:
    op.create_table(
        "verification_reviews",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column(
            "from_status",
            sa.Enum(
                "unverified",
                "verified",
                "disputed",
                "rejected",
                "superseded",
                "sample",
                name="review_from_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "decision",
            sa.Enum(
                "verified",
                "rejected",
                "disputed",
                "unverified",
                "superseded",
                name="review_decision",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("curator", sa.String(length=120), nullable=False),
        sa.Column("reviewer", sa.String(length=120), nullable=False),
        sa.Column("checked_against", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "btrim(checked_against) <> ''",
            name=op.f("ck_verification_reviews_checked_against_present"),
        ),
        sa.CheckConstraint(
            "btrim(curator) <> '' AND btrim(reviewer) <> ''",
            name=op.f("ck_verification_reviews_names_present"),
        ),
        sa.CheckConstraint(
            "lower(btrim(reviewer)) !~ '^(system|atlas|auto|automated|automatic|bot|import|"
            "importer|ingestion|claude|ai)$'",
            name=op.f("ck_verification_reviews_reviewer_is_a_person"),
        ),
        sa.CheckConstraint(
            "lower(btrim(curator)) <> lower(btrim(reviewer))",
            name=op.f("ck_verification_reviews_curator_is_not_reviewer"),
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            ["evidence.id"],
            name=op.f("fk_verification_reviews_evidence_id_evidence"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_verification_reviews")),
    )
    op.create_index(
        "ix_verification_reviews_evidence",
        "verification_reviews",
        ["evidence_id", "reviewed_at"],
        unique=False,
    )

    op.add_column("financial_metrics", sa.Column("source_page", sa.Integer(), nullable=True))
    op.add_column(
        "financial_metrics",
        sa.Column("reported_value", sa.Numeric(precision=38, scale=6), nullable=True),
    )
    op.add_column("financial_metrics", sa.Column("reported_scale", sa.Integer(), nullable=True))
    for name, condition in (
        ("source_page_positive", "source_page >= 1"),
        ("reported_scale_allowed", "reported_scale IN (1, 1000, 1000000)"),
        ("reported_pair", "(reported_value IS NULL) = (reported_scale IS NULL)"),
        (
            "value_is_reported_times_scale",
            "reported_value IS NULL OR value = reported_value * reported_scale",
        ),
    ):
        op.create_check_constraint(
            op.f(f"ck_financial_metrics_{name}"), "financial_metrics", condition
        )

    # Existing rows keep their status; `rejected` is only added to the allowed set.
    op.drop_constraint(op.f("ck_evidence_verification_status"), "evidence", type_="check")
    op.create_check_constraint(
        op.f("ck_evidence_verification_status"),
        "evidence",
        f"verification_status IN ({_STATUSES_NEW})",
    )

    allowed = " OR ".join(f"(cur = '{a}' AND NEW.decision = '{b}')" for a, b in TRANSITIONS)
    # Interpolates only the TRANSITIONS constant above, never input.
    op.execute(
        f"""
        CREATE FUNCTION atlas_apply_review() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE cur text;
        BEGIN
            SELECT verification_status INTO cur FROM evidence WHERE id = NEW.evidence_id FOR UPDATE;
            IF cur IS NULL THEN
                RAISE EXCEPTION 'evidence % does not exist', NEW.evidence_id
                    USING ERRCODE = 'foreign_key_violation';
            END IF;
            IF cur <> NEW.from_status THEN
                RAISE EXCEPTION 'evidence % is %, not %: review the current state',
                    NEW.evidence_id, cur, NEW.from_status USING ERRCODE = 'check_violation';
            END IF;
            IF NOT ({allowed}) THEN
                RAISE EXCEPTION 'transition % -> % is not allowed', cur, NEW.decision
                    USING ERRCODE = 'check_violation';
            END IF;
            UPDATE evidence SET verification_status = NEW.decision WHERE id = NEW.evidence_id;
            RETURN NEW;
        END;
        $$;
        """  # noqa: S608
    )
    op.execute(
        "CREATE TRIGGER verification_reviews_apply BEFORE INSERT ON verification_reviews "
        "FOR EACH ROW EXECUTE FUNCTION atlas_apply_review()"
    )
    op.execute(
        """
        CREATE FUNCTION atlas_reject_review_change() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION '% on verification_reviews is not allowed: reviews are append-only',
                TG_OP USING ERRCODE = 'restrict_violation';
        END;
        $$;
        """
    )
    op.execute(
        "CREATE TRIGGER verification_reviews_append_only BEFORE UPDATE OR DELETE "
        "ON verification_reviews FOR EACH ROW EXECUTE FUNCTION atlas_reject_review_change()"
    )

    # Evidence: born unverified (or sample); immutable except a status change made by a review
    # (the review trigger's UPDATE runs at trigger depth 2; a direct UPDATE runs at depth 1).
    op.execute(
        """
        CREATE FUNCTION atlas_guard_evidence() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                IF NEW.verification_status NOT IN ('unverified', 'sample') THEN
                    RAISE EXCEPTION 'new evidence must be unverified or sample, not %',
                        NEW.verification_status USING ERRCODE = 'check_violation';
                END IF;
                RETURN NEW;
            END IF;
            IF (to_jsonb(NEW) - 'verification_status') <> (to_jsonb(OLD) - 'verification_status') THEN
                RAISE EXCEPTION 'evidence is immutable; record new evidence instead'
                    USING ERRCODE = 'restrict_violation';
            END IF;
            IF NEW.verification_status <> OLD.verification_status AND pg_trigger_depth() < 2 THEN
                RAISE EXCEPTION 'verification_status changes only through verification_reviews'
                    USING ERRCODE = 'restrict_violation';
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        "CREATE TRIGGER evidence_guard BEFORE INSERT OR UPDATE ON evidence "
        "FOR EACH ROW EXECUTE FUNCTION atlas_guard_evidence()"
    )

    # Real figures need their page and their as-reported value; sample fixtures don't.
    op.execute(
        """
        CREATE FUNCTION atlas_require_figure_provenance() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF (NEW.source_page IS NULL OR NEW.reported_value IS NULL) AND NOT (
                SELECT c.is_sample FROM financial_statements s
                JOIN companies c ON c.id = s.company_id
                WHERE s.id = NEW.financial_statement_id
            ) THEN
                RAISE EXCEPTION 'real figure % needs source_page and reported_value/scale',
                    NEW.metric_code USING ERRCODE = 'not_null_violation';
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        "CREATE TRIGGER financial_metrics_provenance BEFORE INSERT ON financial_metrics "
        "FOR EACH ROW EXECUTE FUNCTION atlas_require_figure_provenance()"
    )


def downgrade() -> None:
    op.execute(DOWNGRADE_GUARD)
    op.execute("DROP TRIGGER financial_metrics_provenance ON financial_metrics")
    op.execute("DROP FUNCTION atlas_require_figure_provenance()")
    op.execute("DROP TRIGGER evidence_guard ON evidence")
    op.execute("DROP FUNCTION atlas_guard_evidence()")
    op.execute("DROP TRIGGER verification_reviews_append_only ON verification_reviews")
    op.execute("DROP FUNCTION atlas_reject_review_change()")
    op.execute("DROP TRIGGER verification_reviews_apply ON verification_reviews")
    op.execute("DROP FUNCTION atlas_apply_review()")

    op.drop_constraint(op.f("ck_evidence_verification_status"), "evidence", type_="check")
    op.create_check_constraint(
        op.f("ck_evidence_verification_status"),
        "evidence",
        f"verification_status IN ({_STATUSES_OLD})",
    )
    for name in (
        "value_is_reported_times_scale",
        "reported_pair",
        "reported_scale_allowed",
        "source_page_positive",
    ):
        op.drop_constraint(op.f(f"ck_financial_metrics_{name}"), "financial_metrics", type_="check")
    op.drop_column("financial_metrics", "reported_scale")
    op.drop_column("financial_metrics", "reported_value")
    op.drop_column("financial_metrics", "source_page")
    op.drop_index("ix_verification_reviews_evidence", table_name="verification_reviews")
    op.drop_table("verification_reviews")
