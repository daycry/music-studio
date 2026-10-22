"""Rechazo JSON estricto antes de evaluar contratos; sin reescribir datos."""

from alembic import op
from app.migrations.job_attempt_invariants import install_validation_triggers

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def _replace(*, syntax_guard):
    connection = op.get_bind()
    for name in ("attempt_validate_insert", "attempt_validate_update"):
        connection.exec_driver_sql(f'DROP TRIGGER "{name}"')
    install_validation_triggers(connection, syntax_guard=syntax_guard)


def upgrade():
    _replace(syntax_guard=True)


def downgrade():
    _replace(syntax_guard=False)
