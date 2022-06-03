from dataclasses import dataclass, asdict, field
from typing import Any, Dict, Literal, Optional, Tuple, Union

import jinja2


@dataclass
class Sql:
    sql_id: str

    dict = asdict

    @staticmethod
    def from_dict(d: Dict[str, Any]):
        if d["type"] == "split":
            return SplitSql(d["sql_id"], d["base_id"] or None, d["sql"], extra=d["extra"] or {})
        elif d["type"] == "str":
            return StrSql(d["sql_id"], d["sql"], d["default"] or {}, extra=d["extra"] or {})
        elif d["type"] == "str_value":
            return ValueSql(d["sql_id"], d["base_id"], d["values"], extra=d["extra"] or {})
        else:
            raise NotImplementedError()

    def get_template(self, template=None):
        return ...

    def get_str_sql(self, template=None):
        pass


line_breaks = {
    "INSERT",
    "VALUES",
    "UPDATE",
    "SET",
    "SELECT",
    "REPLACE INTO",
    "FROM",
    "GROUP BY",
    "ORDER BY",
    "WHERE",
    "LIMIT"
}


@dataclass
class SplitSql(Sql):
    base_id: Optional[str]
    sql: Dict[str, str]
    type: str = "split"
    extra: Any = field(default_factory=dict)

    @classmethod
    def from_sql(cls, sql_id: str, sql: str, base_id: Optional[str] = None, extra=None):
        lines = sql.splitlines()
        d = {}
        last: str = None
        for l in lines:
            if not l.strip():
                if last is not None:
                    d[last] += f"\n"
                continue
            words = l.split(maxsplit=1)
            lb = words[0]
            if lb in line_breaks:
                d[lb] = words[1] if len(words) > 1 else ""
                last = lb
                continue

            words = l.split(maxsplit=2)
            if len(words) >= 2:
                lb = ' '.join(words[:2])
                if lb in line_breaks:
                    d[lb] = words[2] if len(words) > 2 else ""
                    last = lb
                    continue
            d[last] += f"\n{l}"
        return cls(sql_id, base_id, d, extra=extra or {})

    def dict(self):
        return dict(
            sql_id=self.sql_id,
            type=self.type,
            base_id=self.base_id,
            sql=self.sql,
            extra=self.extra or "")

    def get_str_sql(self, template: Optional[Dict[str, str]] = None):
        sql = self.get_template(template)
        return '\n'.join(f"{k} {v}" for k, v in sql.items() if v.strip())

    def get_template(self, template: Optional[Dict[str, str]] = None):
        if self.base_id and not template:
            raise ValueError()
        if template:
            template = template.copy()
            template.update(self.sql)
        else:
            template = self.sql
        return template


@dataclass
class StrSql(Sql):
    sql: str
    default: Dict[str, str]
    type: str = "str"
    extra: Any = field(default_factory=dict)

    def dict(self):
        return dict(
            sql_id=self.sql_id,
            type=self.type,
            sql=self.sql,
            default=self.default or None,
            extra=self.extra or "")

    def get_str_sql(self, template):
        sql, values = self.get_template(template)
        return jinja2.Template(sql, undefined=jinja2.StrictUndefined).render(values)

    def get_template(self, template):
        assert template is None
        return self.sql, self.default.copy()


@dataclass
class ValueSql(Sql):
    base_id: str
    values: Dict[str, str]
    type: str = "str_value"
    extra: Any = field(default_factory=dict)

    def dict(self):
        return dict(
            sql_id=self.sql_id,
            type=self.type,
            base_id=self.base_id,
            values=self.values,
            extra=self.extra or "")

    get_str_sql = StrSql.get_str_sql

    def get_template(self, template: Optional[Tuple[str, Dict[str, str]]] = None):
        assert template
        template[1].update(self.values)
        return template
