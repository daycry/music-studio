"""Impide promover soporte parcial fuera de la importación validada."""


def install(connection):
    connection.exec_driver_sql(
        "CREATE TRIGGER fix3_song_promotion BEFORE UPDATE OF is_dependency_only ON song "
        "WHEN OLD.is_dependency_only != NEW.is_dependency_only AND "
        "(NEW.is_dependency_only=1 OR NOT EXISTS "
        "(SELECT 1 FROM snapshot_import WHERE song_id=OLD.id)) "
        "BEGIN SELECT RAISE(ABORT,'Support project requires validated promotion; "
        "complete projects cannot be demoted'); END"
    )


def uninstall(connection):
    connection.exec_driver_sql("DROP TRIGGER fix3_song_promotion")
