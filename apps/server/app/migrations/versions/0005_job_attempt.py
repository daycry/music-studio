"""Identidad durable aditiva; DDL propio congelado, baseline0001–4 intacto."""

from alembic import op

from app.migrations.job_attempt_invariants import install, uninstall

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

DDL = "\nCREATE TABLE job_attempt (\n\tjob_id VARCHAR(26) NOT NULL, \n\tordinal INTEGER NOT NULL, \n\tengine_id TEXT NOT NULL, \n\tmodel_id TEXT NOT NULL, \n\tmode TEXT, \n\tengine_request JSON NOT NULL, \n\tload_options JSON NOT NULL, \n\tlast_seq INTEGER DEFAULT '0' NOT NULL, \n\tstatus TEXT DEFAULT 'prepared' NOT NULL, \n\tterminal JSON, \n\tid VARCHAR(26) NOT NULL, \n\towner_id VARCHAR(26) NOT NULL, \n\tcreated_at TEXT NOT NULL, \n\tupdated_at TEXT NOT NULL, \n\tdeleted_at TEXT, \n\tPRIMARY KEY (id), \n\tUNIQUE (job_id, ordinal), \n\tCONSTRAINT ck_status CHECK (status IN ('prepared','submitted','succeeded','failed','cancelled')), \n\tCHECK (typeof(ordinal)='integer' AND ordinal>=1), \n\tCHECK (typeof(last_seq)='integer' AND last_seq>=0), \n\tCHECK (length(engine_id)>0 AND length(model_id)>0), \n\tCHECK (engine_request IS NULL OR (json_valid(engine_request) AND json_type(engine_request)='object')), \n\tCHECK (load_options IS NULL OR (json_valid(load_options) AND json_type(load_options)='object')), \n\tCHECK (terminal IS NULL OR (json_valid(terminal) AND json_type(terminal)='object')), \n\tFOREIGN KEY(job_id) REFERENCES job (id) DEFERRABLE INITIALLY DEFERRED, \n\tFOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, \n\tCHECK (length(\"job_id\")=26 AND substr(\"job_id\",1,1) BETWEEN '0' AND '7' AND \"job_id\" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), \n\tCHECK (length(\"id\")=26 AND substr(\"id\",1,1) BETWEEN '0' AND '7' AND \"id\" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), \n\tCHECK (length(\"owner_id\")=26 AND substr(\"owner_id\",1,1) BETWEEN '0' AND '7' AND \"owner_id\" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), \n\tCHECK (\"created_at\" IS NULL OR (substr(\"created_at\",-1)='Z' AND datetime(\"created_at\") IS NOT NULL)), \n\tCHECK (\"updated_at\" IS NULL OR (substr(\"updated_at\",-1)='Z' AND datetime(\"updated_at\") IS NOT NULL)), \n\tCHECK (\"deleted_at\" IS NULL OR (substr(\"deleted_at\",-1)='Z' AND datetime(\"deleted_at\") IS NOT NULL))\n)\n\n"
INDEXES = [
    "CREATE INDEX ix_job_attempt_deleted_at ON job_attempt (deleted_at)",
    "CREATE INDEX ix_job_attempt_job_id ON job_attempt (job_id)",
    "CREATE INDEX ix_job_attempt_owner_id ON job_attempt (owner_id)",
]


def upgrade():
    connection = op.get_bind()
    connection.exec_driver_sql(DDL)
    for statement in INDEXES:
        connection.exec_driver_sql(statement)
    install(connection)


def downgrade():
    connection = op.get_bind()
    uninstall(connection)
    connection.exec_driver_sql("DROP TABLE job_attempt")
