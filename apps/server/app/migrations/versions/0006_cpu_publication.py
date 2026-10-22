"""Esquema aditivo CPU/publicación, ADR-0055; DDL propio congelado."""

from alembic import op

from app.migrations.cpu_publication_invariants import install, uninstall

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


DDL = [
    '\nCREATE TABLE cpu_execution (\n\tjob_id VARCHAR(26) NOT NULL, \n\tordinal INTEGER NOT NULL, \n\thandler TEXT DEFAULT \'post.audio\' NOT NULL, \n\thandler_version INTEGER DEFAULT \'1\' NOT NULL, \n\tcontract_version INTEGER DEFAULT \'1\' NOT NULL, \n\tstate TEXT DEFAULT \'prepared\' NOT NULL, \n\trevision INTEGER DEFAULT \'1\' NOT NULL, \n\t"plan" JSON NOT NULL, \n\tplan_sha256 VARCHAR(64) NOT NULL, \n\toutcome JSON, \n\terror_code TEXT, \n\tfinished_at TEXT, \n\tsupervisor_epoch TEXT, \n\tlease_token TEXT, \n\tprocess_identity JSON, \n\tcleanup_state TEXT DEFAULT \'unknown\' NOT NULL, \n\tid VARCHAR(26) NOT NULL, \n\towner_id VARCHAR(26) NOT NULL, \n\tcreated_at TEXT NOT NULL, \n\tupdated_at TEXT NOT NULL, \n\tdeleted_at TEXT, \n\tPRIMARY KEY (id), \n\tUNIQUE (job_id, ordinal), \n\tFOREIGN KEY(job_id) REFERENCES job (id) DEFERRABLE INITIALLY DEFERRED, \n\tFOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, \n\tCHECK (length("job_id")=26 AND substr("job_id",1,1) BETWEEN \'0\' AND \'7\' AND "job_id" NOT GLOB \'*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*\'), \n\tCHECK (length("plan_sha256")=64 AND "plan_sha256" NOT GLOB \'*[^0-9a-f]*\'), \n\tCHECK ("outcome" IS NULL OR (json_valid("outcome") AND json_type("outcome")=\'object\')), \n\tCHECK ("finished_at" IS NULL OR (substr("finished_at",-1)=\'Z\' AND datetime("finished_at") IS NOT NULL)), \n\tCHECK ("process_identity" IS NULL OR (json_valid("process_identity") AND json_type("process_identity")=\'object\')), \n\tCHECK (length("id")=26 AND substr("id",1,1) BETWEEN \'0\' AND \'7\' AND "id" NOT GLOB \'*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*\'), \n\tCHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN \'0\' AND \'7\' AND "owner_id" NOT GLOB \'*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*\'), \n\tCHECK ("created_at" IS NULL OR (substr("created_at",-1)=\'Z\' AND datetime("created_at") IS NOT NULL)), \n\tCHECK ("updated_at" IS NULL OR (substr("updated_at",-1)=\'Z\' AND datetime("updated_at") IS NOT NULL)), \n\tCHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)=\'Z\' AND datetime("deleted_at") IS NOT NULL))\n)\n\n',
    '\nCREATE TABLE publication_intent (\n\tsong_id VARCHAR(26) NOT NULL, \n\ttake_id VARCHAR(26) NOT NULL, \n\toutput_index INTEGER NOT NULL, \n\tseed TEXT NOT NULL, \n\tstate TEXT DEFAULT \'reserved\' NOT NULL, \n\trevision INTEGER DEFAULT \'1\' NOT NULL, \n\tactive_revision_id VARCHAR(26), \n\terror_code TEXT, \n\tcommitted_at TEXT, \n\tid VARCHAR(26) NOT NULL, \n\towner_id VARCHAR(26) NOT NULL, \n\tcreated_at TEXT NOT NULL, \n\tupdated_at TEXT NOT NULL, \n\tdeleted_at TEXT, \n\tPRIMARY KEY (id), \n\tUNIQUE (take_id), \n\tFOREIGN KEY(song_id) REFERENCES song (id) DEFERRABLE INITIALLY DEFERRED, \n\tFOREIGN KEY(take_id) REFERENCES take (id) DEFERRABLE INITIALLY DEFERRED, \n\tFOREIGN KEY(active_revision_id) REFERENCES publication_intent_revision (id) DEFERRABLE INITIALLY DEFERRED, \n\tFOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, \n\tCHECK (length("song_id")=26 AND substr("song_id",1,1) BETWEEN \'0\' AND \'7\' AND "song_id" NOT GLOB \'*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*\'), \n\tCHECK (length("take_id")=26 AND substr("take_id",1,1) BETWEEN \'0\' AND \'7\' AND "take_id" NOT GLOB \'*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*\'), \n\tCHECK (length("seed")>0 AND "seed" NOT GLOB \'*[^0-9]*\' AND ("seed"=\'0\' OR substr("seed",1,1)!=\'0\')), \n\tCHECK (length("active_revision_id")=26 AND substr("active_revision_id",1,1) BETWEEN \'0\' AND \'7\' AND "active_revision_id" NOT GLOB \'*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*\'), \n\tCHECK ("committed_at" IS NULL OR (substr("committed_at",-1)=\'Z\' AND datetime("committed_at") IS NOT NULL)), \n\tCHECK (length("id")=26 AND substr("id",1,1) BETWEEN \'0\' AND \'7\' AND "id" NOT GLOB \'*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*\'), \n\tCHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN \'0\' AND \'7\' AND "owner_id" NOT GLOB \'*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*\'), \n\tCHECK ("created_at" IS NULL OR (substr("created_at",-1)=\'Z\' AND datetime("created_at") IS NOT NULL)), \n\tCHECK ("updated_at" IS NULL OR (substr("updated_at",-1)=\'Z\' AND datetime("updated_at") IS NOT NULL)), \n\tCHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)=\'Z\' AND datetime("deleted_at") IS NOT NULL))\n)\n\n',
    '\nCREATE TABLE publication_intent_revision (\n\tintent_id VARCHAR(26) NOT NULL, \n\tcpu_execution_id VARCHAR(26) NOT NULL, \n\tsong_id VARCHAR(26) NOT NULL, \n\tpost_job_id VARCHAR(26) NOT NULL, \n\tgeneration_job_id VARCHAR(26) NOT NULL, \n\twinning_attempt_id VARCHAR(26) NOT NULL, \n\twinning_ordinal INTEGER NOT NULL, \n\tterminal_seq INTEGER NOT NULL, \n\tterminal_sha256 VARCHAR(64) NOT NULL, \n\ttake_id VARCHAR(26) NOT NULL, \n\toutput_index INTEGER NOT NULL, \n\tseed TEXT NOT NULL, \n\tprovenance_sha256 VARCHAR(64) NOT NULL, \n\tsource_sha256 VARCHAR(64) NOT NULL, \n\tstage_path TEXT NOT NULL, \n\tfinal_path TEXT NOT NULL, \n\tpackage JSON, \n\tpackage_sha256 VARCHAR(64), \n\terror_code TEXT, \n\tid VARCHAR(26) NOT NULL, \n\towner_id VARCHAR(26) NOT NULL, \n\tcreated_at TEXT NOT NULL, \n\tupdated_at TEXT NOT NULL, \n\tdeleted_at TEXT, \n\tPRIMARY KEY (id), \n\tUNIQUE (intent_id, generation_job_id, winning_attempt_id, output_index), \n\tFOREIGN KEY(intent_id) REFERENCES publication_intent (id) DEFERRABLE INITIALLY DEFERRED, \n\tFOREIGN KEY(cpu_execution_id) REFERENCES cpu_execution (id) DEFERRABLE INITIALLY DEFERRED, \n\tFOREIGN KEY(song_id) REFERENCES song (id) DEFERRABLE INITIALLY DEFERRED, \n\tFOREIGN KEY(post_job_id) REFERENCES job (id) DEFERRABLE INITIALLY DEFERRED, \n\tFOREIGN KEY(generation_job_id) REFERENCES job (id) DEFERRABLE INITIALLY DEFERRED, \n\tFOREIGN KEY(winning_attempt_id) REFERENCES job_attempt (id) DEFERRABLE INITIALLY DEFERRED, \n\tFOREIGN KEY(take_id) REFERENCES take (id) DEFERRABLE INITIALLY DEFERRED, \n\tFOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, \n\tCHECK (length("intent_id")=26 AND substr("intent_id",1,1) BETWEEN \'0\' AND \'7\' AND "intent_id" NOT GLOB \'*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*\'), \n\tCHECK (length("cpu_execution_id")=26 AND substr("cpu_execution_id",1,1) BETWEEN \'0\' AND \'7\' AND "cpu_execution_id" NOT GLOB \'*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*\'), \n\tCHECK (length("song_id")=26 AND substr("song_id",1,1) BETWEEN \'0\' AND \'7\' AND "song_id" NOT GLOB \'*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*\'), \n\tCHECK (length("post_job_id")=26 AND substr("post_job_id",1,1) BETWEEN \'0\' AND \'7\' AND "post_job_id" NOT GLOB \'*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*\'), \n\tCHECK (length("generation_job_id")=26 AND substr("generation_job_id",1,1) BETWEEN \'0\' AND \'7\' AND "generation_job_id" NOT GLOB \'*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*\'), \n\tCHECK (length("winning_attempt_id")=26 AND substr("winning_attempt_id",1,1) BETWEEN \'0\' AND \'7\' AND "winning_attempt_id" NOT GLOB \'*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*\'), \n\tCHECK (length("terminal_sha256")=64 AND "terminal_sha256" NOT GLOB \'*[^0-9a-f]*\'), \n\tCHECK (length("take_id")=26 AND substr("take_id",1,1) BETWEEN \'0\' AND \'7\' AND "take_id" NOT GLOB \'*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*\'), \n\tCHECK (length("seed")>0 AND "seed" NOT GLOB \'*[^0-9]*\' AND ("seed"=\'0\' OR substr("seed",1,1)!=\'0\')), \n\tCHECK (length("provenance_sha256")=64 AND "provenance_sha256" NOT GLOB \'*[^0-9a-f]*\'), \n\tCHECK (length("source_sha256")=64 AND "source_sha256" NOT GLOB \'*[^0-9a-f]*\'), \n\tCHECK (length("package_sha256")=64 AND "package_sha256" NOT GLOB \'*[^0-9a-f]*\'), \n\tCHECK (length("id")=26 AND substr("id",1,1) BETWEEN \'0\' AND \'7\' AND "id" NOT GLOB \'*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*\'), \n\tCHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN \'0\' AND \'7\' AND "owner_id" NOT GLOB \'*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*\'), \n\tCHECK ("created_at" IS NULL OR (substr("created_at",-1)=\'Z\' AND datetime("created_at") IS NOT NULL)), \n\tCHECK ("updated_at" IS NULL OR (substr("updated_at",-1)=\'Z\' AND datetime("updated_at") IS NOT NULL)), \n\tCHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)=\'Z\' AND datetime("deleted_at") IS NOT NULL))\n)\n\n',
]
INDEXES = [
    "CREATE INDEX ix_cpu_execution_deleted_at ON cpu_execution (deleted_at)",
    "CREATE INDEX ix_cpu_execution_job_id ON cpu_execution (job_id)",
    "CREATE INDEX ix_cpu_execution_owner_id ON cpu_execution (owner_id)",
    "CREATE INDEX ix_publication_intent_active_revision_id ON publication_intent (active_revision_id)",
    "CREATE INDEX ix_publication_intent_deleted_at ON publication_intent (deleted_at)",
    "CREATE INDEX ix_publication_intent_owner_id ON publication_intent (owner_id)",
    "CREATE INDEX ix_publication_intent_song_id ON publication_intent (song_id)",
    "CREATE INDEX ix_publication_intent_take_id ON publication_intent (take_id)",
    "CREATE INDEX ix_publication_intent_revision_cpu_execution_id ON publication_intent_revision (cpu_execution_id)",
    "CREATE INDEX ix_publication_intent_revision_deleted_at ON publication_intent_revision (deleted_at)",
    "CREATE INDEX ix_publication_intent_revision_generation_job_id ON publication_intent_revision (generation_job_id)",
    "CREATE INDEX ix_publication_intent_revision_intent_id ON publication_intent_revision (intent_id)",
    "CREATE INDEX ix_publication_intent_revision_owner_id ON publication_intent_revision (owner_id)",
    "CREATE INDEX ix_publication_intent_revision_post_job_id ON publication_intent_revision (post_job_id)",
    "CREATE INDEX ix_publication_intent_revision_song_id ON publication_intent_revision (song_id)",
    "CREATE INDEX ix_publication_intent_revision_take_id ON publication_intent_revision (take_id)",
    "CREATE INDEX ix_publication_intent_revision_winning_attempt_id ON publication_intent_revision (winning_attempt_id)",
]


def upgrade():
    connection = op.get_bind()
    connection.exec_driver_sql("ALTER TABLE job_attempt ADD COLUMN provenance JSON")
    connection.exec_driver_sql(
        "ALTER TABLE job_attempt ADD COLUMN provenance_sha256 VARCHAR(64)"
    )
    connection.exec_driver_sql("ALTER TABLE take ADD COLUMN error_code TEXT")
    for statement in DDL + INDEXES:
        connection.exec_driver_sql(statement)
    install(connection)


def downgrade():
    connection = op.get_bind()
    uninstall(connection)
    connection.exec_driver_sql("DELETE FROM publication_intent_revision")
    connection.exec_driver_sql("DELETE FROM publication_intent")
    connection.exec_driver_sql("DELETE FROM cpu_execution")
    for name in ("publication_intent_revision", "publication_intent", "cpu_execution"):
        connection.exec_driver_sql(f'DROP TABLE "{name}"')
    connection.exec_driver_sql("ALTER TABLE take DROP COLUMN error_code")
    connection.exec_driver_sql("ALTER TABLE job_attempt DROP COLUMN provenance_sha256")
    connection.exec_driver_sql("ALTER TABLE job_attempt DROP COLUMN provenance")
