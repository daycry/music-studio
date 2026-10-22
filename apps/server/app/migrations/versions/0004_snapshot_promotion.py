"""Promoción validada de canciones de soporte, sin cambiar revisiones previas."""

from alembic import op

from app.migrations.fix3_invariants import install, uninstall

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    install(op.get_bind())


def downgrade():
    uninstall(op.get_bind())
