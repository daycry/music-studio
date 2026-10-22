"""Acceso indexado al cierre, por lotes limitados y sin cargar otras canciones."""

from collections import defaultdict

from sqlalchemy import select

BATCH_SIZE = 400


def chunks(values):
    values = list(values)
    for start in range(0, len(values), BATCH_SIZE):
        yield values[start : start + BATCH_SIZE]


class SQLRows:
    def __init__(self, connection, tables, canonical):
        self.connection = connection
        self.tables = tables
        self.canonical = canonical
        self.rows = {}
        self.matches = {}

    def remember(self, name, rows):
        result = [self.canonical(dict(row)) for row in rows]
        for row in result:
            self.rows[name, row["id"]] = row
        return result

    def fetch_many(self, keys):
        missing = defaultdict(set)
        for name, identifier in keys:
            if (name, identifier) not in self.rows:
                missing[name].add(identifier)
        for name, identifiers in missing.items():
            table = self.tables[name]
            for batch in chunks(identifiers):
                for identifier in batch:
                    self.rows[name, identifier] = None
                self.remember(
                    name,
                    self.connection.execute(
                        select(table).where(table.c.id.in_(batch))
                    ).mappings(),
                )

    def fetch(self, name, identifier):
        self.fetch_many([(name, identifier)])
        return self.rows[name, identifier]

    def lookup_many(self, requests):
        groups = defaultdict(set)
        for name, filters in requests:
            key = (name, tuple(sorted(filters.items())))
            if key in self.matches:
                continue
            # Todos los filtros vienen del mapa cerrado de closure: el ID varía,
            # subject_type/child_type es la constante del grupo polimórfico.
            column = next(k for k in filters if k.endswith("_id"))
            constants = tuple(sorted((k, v) for k, v in filters.items() if k != column))
            groups[name, column, constants].add(filters[column])
        for (name, column, constants), identifiers in groups.items():
            table = self.tables[name]
            for batch in chunks(identifiers):
                for identifier in batch:
                    filters = dict(constants, **{column: identifier})
                    self.matches[name, tuple(sorted(filters.items()))] = []
                statement = select(table).where(table.c[column].in_(batch))
                for field, value in constants:
                    statement = statement.where(table.c[field] == value)
                for row in self.remember(
                    name, self.connection.execute(statement).mappings()
                ):
                    filters = dict(constants, **{column: row[column]})
                    self.matches[name, tuple(sorted(filters.items()))].append(row)

    def lookup(self, name, filters):
        self.lookup_many([(name, filters)])
        return self.matches[name, tuple(sorted(filters.items()))]


class MemoryRows:
    def __init__(self, rows, relations):
        self.rows = {
            (name, row["id"]): row for name, values in rows.items() for row in values
        }
        self.matches = defaultdict(list)
        fields = defaultdict(set)
        for children in relations.values():
            for name, column in children:
                fields[name].add((column,))
        fields["analysis"].add(("take_id",))
        fields["asset"].add(("subject_id", "subject_type"))
        fields["lineage_edge"].add(("child_id", "child_type"))
        for name, combinations in fields.items():
            for row in rows[name]:
                for columns in combinations:
                    self.matches[
                        name, tuple((column, row[column]) for column in columns)
                    ].append(row)

    def fetch(self, name, identifier):
        return self.rows.get((name, identifier))

    def lookup(self, name, filters):
        return self.matches.get((name, tuple(sorted(filters.items()))), [])
