"""baseline

Establishes Alembic version tracking. Intentionally schema-free: Phase 0 defines no
domain tables; later revisions build on this one.

Revision ID: 2fa53e542881
Revises:
Create Date: 2026-11-22 21:21:01.498184

"""

from collections.abc import Sequence

revision: str = "2fa53e542881"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
