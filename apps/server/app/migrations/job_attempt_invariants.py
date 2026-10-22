"""Validación contractual y guardas SQLite aditivas de los intentos."""

import json
from datetime import datetime

from engine_contract import EVENT_DATA, Event, Input, JobRequest, LoadRequest
from pydantic import BaseModel, ConfigDict, field_validator


class FrozenDict(dict):
    """Contenedor JSON inmutable también en sus niveles anidados."""

    def _immutable(self, *args, **kwargs):
        raise TypeError("Frozen attempt request")

    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = (
        __ior__
    ) = _immutable


def freeze_json(value):
    if isinstance(value, dict):
        return FrozenDict({key: freeze_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(freeze_json(item) for item in value)
    return value


class FrozenInput(Input):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class FrozenJobRequest(JobRequest):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    inputs: tuple[FrozenInput, ...] = ()

    @field_validator("params", mode="after")
    @classmethod
    def frozen_params(cls, value):
        return freeze_json(value)


class FrozenLoadOptions(LoadRequest):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


TYPES = {"request": FrozenJobRequest, "load": FrozenLoadOptions, "event": Event}
STATES = {"succeeded": "done", "failed": "error", "cancelled": "cancelled"}


def validate_contract(value, kind):
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if kind == "event" and (not isinstance(value, dict) or "ts" not in value):
        raise ValueError("Durable attempt event requires explicit timestamp")
    encoded = json.dumps(value, allow_nan=False, ensure_ascii=False)

    def check(item):
        if isinstance(item, dict):
            for key, child in item.items():
                if key.lower() in {
                    "token",
                    "api_key",
                    "access_token",
                    "authorization",
                    "password",
                    "secret",
                    "engine_token",
                }:
                    raise ValueError("Attempt contains secret fields")
                check(child)
        elif isinstance(item, list):
            for child in item:
                check(child)

    check(value)
    result = TYPES[kind].model_validate_json(encoded, strict=True)
    if kind == "event":
        if (
            not isinstance(value["ts"], str)
            or not value["ts"].endswith("Z")
            or result.ts.utcoffset() is None
            or result.ts.utcoffset().total_seconds() != 0
        ):
            raise ValueError("Attempt terminal timestamp must be UTC")
        EVENT_DATA[result.type].model_validate_json(
            json.dumps(value["data"], allow_nan=False), strict=True
        )

    def no_discard(original, normalized):
        if isinstance(original, dict):
            for key, child in original.items():
                if key not in normalized:
                    raise ValueError("Unknown contractual field would be discarded")
                no_discard(child, normalized[key])
        elif isinstance(original, list):
            for child, actual in zip(original, normalized, strict=True):
                no_discard(child, actual)

    no_discard(value, result.model_dump(mode="json"))
    return result


def validate_attempt(row):
    request = validate_contract(row["engine_request"], "request")
    options = validate_contract(row["load_options"], "load")
    if (request.job_id, request.model_id, request.mode) != (
        row["id"],
        row["model_id"],
        row["mode"],
    ):
        raise ValueError("Attempt request identity mismatch")
    if (options.model_id, options.mode) != (row["model_id"], row["mode"]):
        raise ValueError("Attempt load identity mismatch")
    for key, minimum in (("ordinal", 1), ("last_seq", 0)):
        if type(row[key]) is not int or row[key] < minimum:
            raise ValueError("Invalid attempt ordinal or cursor")
    status = row["status"]
    terminal = row["terminal"]
    if status in {"prepared", "submitted"}:
        if terminal is not None:
            raise ValueError("Nonterminal attempt has terminal")
    elif status in STATES and terminal is not None:
        event = validate_contract(terminal, "event")
        if (event.job_id, event.type, event.seq) != (
            row["id"],
            STATES[status],
            row["last_seq"],
        ):
            raise ValueError("Attempt terminal identity or cursor mismatch")
        if event.ts.utcoffset() is None or event.ts.utcoffset().total_seconds() != 0:
            raise ValueError("Attempt terminal timestamp must be UTC")
    else:
        raise ValueError("Invalid attempt status or missing terminal")
    for key in ("id", "owner_id", "job_id"):
        value = row[key]
        if (
            len(value) != 26
            or value[0] not in "01234567"
            or any(c not in "0123456789ABCDEFGHJKMNPQRSTVWXYZ" for c in value)
        ):
            raise ValueError("Invalid attempt ULID")
    for key in ("created_at", "updated_at", "deleted_at"):
        value = row[key]
        if value is not None and (
            not value.endswith("Z")
            or datetime.fromisoformat(value).utcoffset().total_seconds() != 0
        ):
            raise ValueError("Invalid attempt UTC timestamp")
    if (
        not isinstance(row["engine_id"], str)
        or not row["engine_id"]
        or not row["model_id"]
    ):
        raise ValueError("Attempt engine and model required")


def _literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def _utc_sql(value):
    """Calendario gregoriano estricto sin redondear las fracciones UTC.

    SQLite normaliza días imposibles y acepta hora 24; el lector no.
    La comparación del día normalizado conserva la precisión del texto original.
    """
    return (
        f"length({value})>=20 AND substr({value},-1)='Z'"
        f" AND substr({value},1,10) GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'"
        f" AND substr({value},1,4) BETWEEN '0001' AND '9999'"
        f" AND date(substr({value},1,10),'+0 days')=substr({value},1,10)"
        f" AND substr({value},11,1) IN ('T','t',' ')"
        f" AND substr({value},12,8) GLOB '[0-9][0-9]:[0-9][0-9]:[0-9][0-9]'"
        f" AND substr({value},12,2) BETWEEN '00' AND '23'"
        f" AND substr({value},15,2) BETWEEN '00' AND '59'"
        f" AND substr({value},18,2) BETWEEN '00' AND '59'"
        f" AND (length({value})=20 OR (length({value})>=22"
        f" AND substr({value},20,1)='.'"
        f" AND substr({value},21,length({value})-21) NOT GLOB '*[^0-9]*'))"
    )


def _schema_sql(schema, source, definitions, path="$", counter=None):
    """Compila el subconjunto usado por los tipos /v1 a predicados JSON1.

    No requiere UDF: las conexiones sqlite3 y SQL bulk reciben las mismas guardas.
    Las definiciones contractuales siguen procediendo de engine_contract.
    """
    counter = [0] if counter is None else counter
    if "$ref" in schema:
        schema = definitions[schema["$ref"].split("/")[-1]]
    kind = f"json_type({source},{_literal(path)})"
    value = f"json_extract({source},{_literal(path)})"
    if "anyOf" in schema:
        return (
            "("
            + " OR ".join(
                _schema_sql(s, source, definitions, path, counter)
                for s in schema["anyOf"]
            )
            + ")"
        )
    constraints = []
    types = {
        "object": "'object'",
        "array": "'array'",
        "string": "'text'",
        "integer": "'integer'",
        "number": "'integer','real'",
        "boolean": "'true','false'",
        "null": "'null'",
    }
    if "type" in schema:
        constraints.append(f"{kind} IN ({types[schema['type']]})")
    if "enum" in schema:
        constraints.append(
            f"{value} IN ({','.join(_literal(v) for v in schema['enum'])})"
        )
    if "const" in schema:
        constraints.append(f"{value}={_literal(schema['const'])}")
    for key, op in (
        ("minimum", ">="),
        ("maximum", "<="),
        ("exclusiveMinimum", ">"),
        ("exclusiveMaximum", "<"),
    ):
        if key in schema:
            constraints.append(f"{value}{op}{schema[key]}")
    if "minLength" in schema:
        constraints.append(f"length({value})>={schema['minLength']}")
    if "pattern" in schema:
        if schema["pattern"] == r"^[a-f0-9]{64}$":
            constraints.append(f"length({value})=64 AND {value} NOT GLOB '*[^a-f0-9]*'")
        elif schema["pattern"] == r"^[0-7][0-9A-HJKMNP-TV-Z]{25}$":
            constraints.append(
                f"length({value})=26 AND substr({value},1,1) BETWEEN '0' AND '7' AND {value} NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'"
            )
        else:
            raise ValueError("Unsupported contractual SQL pattern")
    if schema.get("format") == "date-time":
        constraints.append(_utc_sql(value))
    if path.endswith((".path", ".output_dir")):
        constraints.append(
            f"length({value})>0 AND substr({value},1,1)!='/' AND instr({value},':')=0 AND instr({value},char(92))=0 AND instr({value},char(0))=0 AND instr('/'||{value}||'/','/../')=0 AND instr('/'||{value}||'/','/./')=0"
        )
    properties = schema.get("properties", {})
    for key, child in properties.items():
        child_path = path + "." + key
        condition = _schema_sql(child, source, definitions, child_path, counter)
        if key not in schema.get("required", []):
            condition = (
                f"(json_type({source},{_literal(child_path)}) IS NULL OR ({condition}))"
            )
        constraints.append(condition)
    if properties and not isinstance(schema.get("additionalProperties"), dict):
        counter[0] += 1
        alias = "j" + str(counter[0])
        constraints.append(
            f"NOT EXISTS(SELECT 1 FROM json_each({source},{_literal(path)}) {alias} WHERE {alias}.key NOT IN ({','.join(_literal(k) for k in properties)}))"
        )
    if "items" in schema:
        counter[0] += 1
        alias = "j" + str(counter[0])
        item_source = f"CASE WHEN {alias}.type IN ('object','array') THEN {alias}.value ELSE json_quote({alias}.value) END"
        condition = _schema_sql(
            schema["items"], item_source, definitions, counter=counter
        )
        constraints.append(
            f"NOT EXISTS(SELECT 1 FROM json_each({source},{_literal(path)}) {alias} WHERE NOT coalesce(({condition}),0))"
        )
    return "(" + " AND ".join(constraints or ["1"]) + ")"


def _contract_sql(model, source):
    schema = model.model_json_schema()
    if model is Event:
        # El contrato wire tiene default; el sobre durable exige fecha almacenada.
        schema["required"] = [*schema["required"], "ts"]
    result = _schema_sql(schema, source, schema.get("$defs", {}))
    if model is Event:
        for kind, data_model in EVENT_DATA.items():
            data_schema = data_model.model_json_schema()
            condition = _schema_sql(
                data_schema, source, data_schema.get("$defs", {}), "$.data"
            )
            result += f" AND (json_extract({source},'$.type')!={_literal(kind)} OR ({condition}))"
    return result


def install_validation_triggers(connection, *, syntax_guard=False):
    """Crea las dos guardas; False conserva el SQL legado de 0005."""
    for operation in ("INSERT", "UPDATE"):
        body = ""
        if syntax_guard:
            for column in ("engine_request", "load_options", "terminal"):
                source = 'NEW."' + column + '"'
                body += f"SELECT RAISE(ABORT,'Invalid attempt JSON') WHERE {source} IS NOT NULL AND NOT json_valid({source});"
        if operation == "INSERT":
            # REPLACE no ejecuta las guardas UPDATE y puede reciclar una reserva.
            body += "SELECT RAISE(ABORT,'Immutable attempt reservation') WHERE EXISTS(SELECT 1 FROM job_attempt a WHERE a.id=NEW.id OR (a.job_id=NEW.job_id AND a.ordinal=NEW.ordinal));"
        for column in ("created_at", "updated_at", "deleted_at"):
            source = 'NEW."' + column + '"'
            body += f"SELECT RAISE(ABORT,'Invalid attempt UTC timestamp') WHERE {source} IS NOT NULL AND NOT coalesce(({_utc_sql(source)}),0);"
        for column, model in (
            ("engine_request", FrozenJobRequest),
            ("load_options", FrozenLoadOptions),
            ("terminal", Event),
        ):
            source = 'NEW."' + column + '"'
            condition = _contract_sql(model, source)
            body += f"SELECT RAISE(ABORT,'Invalid attempt contract') WHERE {source} IS NOT NULL AND NOT coalesce(({condition}),0);"
            body += f"SELECT RAISE(ABORT,'Unsafe attempt JSON') WHERE EXISTS(SELECT 1 FROM json_tree({source}) WHERE (type='real' AND abs(atom)>1.7976931348623157e308) OR lower(key) IN ('token','api_key','access_token','authorization','password','secret','engine_token'));"
        body += "SELECT RAISE(ABORT,'Attempt request identity mismatch') WHERE json_extract(NEW.engine_request,'$.job_id') IS NOT NEW.id OR json_extract(NEW.engine_request,'$.model_id') IS NOT NEW.model_id OR json_extract(NEW.engine_request,'$.mode') IS NOT NEW.mode OR rtrim(json_extract(NEW.engine_request,'$.output_dir'),'/') IS NOT 'tmp/'||NEW.id OR json_extract(NEW.load_options,'$.model_id') IS NOT NEW.model_id OR json_extract(NEW.load_options,'$.mode') IS NOT NEW.mode;"
        body += "SELECT RAISE(ABORT,'Attempt terminal mismatch') WHERE (NEW.status IN ('prepared','submitted') AND NEW.terminal IS NOT NULL) OR (NEW.status IN ('succeeded','failed','cancelled') AND (NEW.terminal IS NULL OR json_extract(NEW.terminal,'$.job_id') IS NOT NEW.id OR json_extract(NEW.terminal,'$.seq') IS NOT NEW.last_seq OR json_extract(NEW.terminal,'$.type') IS NOT CASE NEW.status WHEN 'succeeded' THEN 'done' WHEN 'failed' THEN 'error' WHEN 'cancelled' THEN 'cancelled' END));"
        body += "SELECT RAISE(ABORT,'Attempt owner mismatch') WHERE EXISTS(SELECT 1 FROM job WHERE id=NEW.job_id AND owner_id!=NEW.owner_id);"
        if operation == "UPDATE":
            body += (
                "SELECT RAISE(ABORT,'Immutable attempt reservation') WHERE "
                + " OR ".join(
                    f"NEW.{key} IS NOT OLD.{key}"
                    for key in (
                        "id",
                        "owner_id",
                        "created_at",
                        "job_id",
                        "ordinal",
                        "engine_id",
                        "model_id",
                        "mode",
                        "engine_request",
                        "load_options",
                    )
                )
                + ";"
            )
        connection.exec_driver_sql(
            f"CREATE TRIGGER attempt_validate_{operation.lower()} BEFORE {operation} ON job_attempt BEGIN {body} END"
        )


def install(connection):
    original = connection.exec_driver_sql(
        "SELECT sql FROM sqlite_master WHERE name='entity_song'"
    ).scalar_one()
    connection.exec_driver_sql("DROP VIEW entity_song")
    connection.exec_driver_sql(
        original
        + " UNION ALL SELECT 'job_attempt',a.id,a.owner_id,j.song_id FROM job_attempt a JOIN job j ON j.id=a.job_id"
    )
    install_validation_triggers(connection)
    connection.exec_driver_sql(
        "CREATE TRIGGER attempt_parent_owner BEFORE UPDATE OF owner_id ON job BEGIN SELECT RAISE(ABORT,'Attempt owner mismatch') WHERE EXISTS(SELECT 1 FROM job_attempt WHERE job_id=OLD.id AND owner_id!=NEW.owner_id); END"
    )
    for operation in ("INSERT", "UPDATE", "DELETE"):
        sides = (
            ["NEW"]
            if operation == "INSERT"
            else ["OLD"]
            if operation == "DELETE"
            else ["OLD", "NEW"]
        )
        support = " OR ".join(
            f"EXISTS(SELECT 1 FROM job j JOIN song s ON s.id=j.song_id WHERE j.id={side}.job_id AND s.is_dependency_only=1 AND NOT EXISTS(SELECT 1 FROM snapshot_import i WHERE i.song_id=s.id))"
            for side in sides
        )
        connection.exec_driver_sql(
            f"CREATE TRIGGER attempt_support_{operation.lower()} BEFORE {operation} ON job_attempt WHEN {support} BEGIN SELECT RAISE(ABORT,'Support project requires validated import or promotion'); END"
        )
        connection.exec_driver_sql(
            f"CREATE TRIGGER attempt_clock_{operation.lower()} AFTER {operation} ON job_attempt BEGIN UPDATE snapshot_clock SET revision=revision+1 WHERE id=1; END"
        )
    for name, timing, operation, side in (
        ("insert", "AFTER", "INSERT", "NEW"),
        ("update_old", "BEFORE", "UPDATE", "OLD"),
        ("update_new", "AFTER", "UPDATE", "NEW"),
        ("delete", "BEFORE", "DELETE", "OLD"),
    ):
        selectors = f"SELECT song_id FROM job WHERE id={side}.job_id UNION SELECT root_id FROM snapshot_member WHERE entity_type='job' AND entity_id={side}.job_id UNION SELECT root_id FROM snapshot_member WHERE entity_type='job_attempt' AND entity_id={side}.id"
        connection.exec_driver_sql(
            f"CREATE TRIGGER attempt_dirty_{name} {timing} {operation} ON job_attempt BEGIN UPDATE song SET snapshot_dirty=1,snapshot_generation=snapshot_generation+1 WHERE is_dependency_only=0 AND id IN ({selectors}); END"
        )
    # Las proyecciones publicadas antes de la migración carecen de la tabla nueva.
    connection.exec_driver_sql(
        "UPDATE song SET snapshot_dirty=1,snapshot_generation=snapshot_generation+1 WHERE is_dependency_only=0"
    )


def uninstall(connection):
    names = (
        connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'attempt_%'"
        )
        .scalars()
        .all()
    )
    for name in names:
        connection.exec_driver_sql(f'DROP TRIGGER "{name}"')
    connection.exec_driver_sql(
        "DELETE FROM snapshot_member WHERE entity_type='job_attempt'"
    )
    connection.exec_driver_sql("DROP VIEW entity_song")
    from .initial_invariants import MEMBERS

    connection.exec_driver_sql(
        "CREATE VIEW entity_song AS "
        + " UNION ALL ".join(
            f"SELECT '{table}' AS type,id,owner_id,{column} AS song_id FROM \"{table}\""
            for table, column in MEMBERS.items()
        )
    )
    connection.exec_driver_sql(
        "UPDATE song SET snapshot_dirty=1,snapshot_generation=snapshot_generation+1 WHERE is_dependency_only=0"
    )
