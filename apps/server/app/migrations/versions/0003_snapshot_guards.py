"""Pertenencia transitiva, soporte y revisión de lectura consistente."""

from alembic import op

from app.migrations.fix2_invariants import install, uninstall

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    install(op.get_bind())


def downgrade():
    uninstall(op.get_bind())
