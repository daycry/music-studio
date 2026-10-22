"""Alembic: configuración de ruta explícita, sin leer secretos."""

from pathlib import Path

from alembic import context
from sqlalchemy import event

from app.db import create_db_engine

config = context.config
path = config.attributes.get("database_path")
if path is None:
    arguments = context.get_x_argument(as_dictionary=True)
    path = arguments.get("database_path", "data/db/studio.sqlite")
engine = create_db_engine(Path(path))
initial_user = config.attributes.get("initial_user")
if initial_user is not None:

    @event.listens_for(engine, "before_cursor_execute", retval=True)
    def seed_user(connection, cursor, statement, parameters, ctx, many):
        # Adapt only the initial seed invocation; no persisted identity is rewritten.
        if statement.startswith(
            'INSERT INTO "user" (id, owner_id, name, created_at, updated_at) VALUES'
        ):
            statement = 'INSERT INTO "user" (id,owner_id,name,created_at,updated_at,deleted_at) VALUES (?,?,?,?,?,?)'
            parameters = tuple(
                initial_user[key]
                for key in (
                    "id",
                    "owner_id",
                    "name",
                    "created_at",
                    "updated_at",
                    "deleted_at",
                )
            )
        return statement, parameters


try:
    with engine.connect() as connection:
        connection.commit()
        context.configure(connection=connection, transactional_ddl=True)
        with context.begin_transaction():
            context.run_migrations()
finally:
    engine.dispose()
