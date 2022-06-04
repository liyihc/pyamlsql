from dataclasses import dataclass, asdict, field
from typing import Any, Dict, Literal, Optional, Tuple, Union

import jinja2
from ruamel.yaml.scalarstring import LiteralScalarString


def dict_to_literal(d: Dict[str, str]):
    return {k: sql_to_literal(v) for k, v in d.items()}


def sql_to_literal(sql):
    if not sql:
        return sql
    if '\n' in sql:
        return LiteralScalarString(sql)
    return sql


@dataclass
class Sql:
    sql_id: str

    dict = asdict

    @staticmethod
    def from_dict(d: Dict[str, Any]):
        if d["type"] == "split":
            return SplitSql(d["sql_id"], d.get("base_id", None) or None, d["sql"], extra=d.get("extra", {}) or {})
        elif d["type"] == "str":
            return StrSql(d["sql_id"], d["sql"], d.get("default", {}) or {}, extra=d.get("extra", {}) or {})
        elif d["type"] == "str_value":
            return ValueSql(d["sql_id"], d.get("base_id", None) or None, d.get("values", {}) or {}, d.get('default', {}) or {}, extra=d.get("extra", {}) or {})
        else:
            raise NotImplementedError()

    @classmethod
    def template_to_str(self, template):
        pass

    def get_template(self, template=None):
        return ...

    def get_str_sql(self, template=None):
        pass

    @classmethod
    def from_template(cls, sql_id: str, template: Any, extra=None):
        return Sql("no implemented")


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

    @classmethod
    def from_template(cls, sql_id: str, template: Dict[str, str], extra=None):
        return cls(sql_id, "", template, extra=extra or {})

    def dict(self):
        return dict(
            sql_id=self.sql_id,
            type=self.type,
            base_id=self.base_id,
            sql=dict_to_literal(self.sql),
            extra=self.extra or None)

    @classmethod
    def template_to_str(cls, template: Dict[str, str]):
        return '\n'.join(f"{k} {v}" for k, v in template.items() if v and v.strip()) # in case v is None

    def get_str_sql(self, template: Optional[Dict[str, str]] = None):
        return self.template_to_str(self.get_template(template))

    def get_template(self, template: Optional[Dict[str, str]] = None):
        if self.base_id and not template:
            raise ValueError()
        if template:
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
            sql=sql_to_literal(self.sql),
            default=dict_to_literal(self.default) or None,
            extra=self.extra or None)

    @classmethod
    def from_template(cls, sql_id, template: Tuple[str, Dict[str, str]], extra=None):
        return cls(
            sql_id,
            template[0],
            template[1],
            extra=extra or {})

    @classmethod
    def template_to_str(cls, template: Tuple[str, Dict[str, str]]):
        sql, default = template
        return jinja2.Template(sql, undefined=jinja2.StrictUndefined).render(default)

    def get_str_sql(self, template):
        return self.template_to_str(self.get_template(template))

    def get_template(self, template):
        assert template is None
        return self.sql, self.default


@dataclass
class ValueSql(Sql):
    base_id: str
    values: Dict[str, str]
    default: Dict[str, str] = field(default_factory=dict)
    type: str = "str_value"
    extra: Any = field(default_factory=dict)

    def dict(self):
        return dict(
            sql_id=self.sql_id,
            type=self.type,
            base_id=self.base_id,
            values=dict_to_literal(self.values) or None,
            default=dict_to_literal(self.default) or None,
            extra=self.extra or None)

    @classmethod
    def from_template(cls, sql_id, template: Tuple[str, Dict[str, str]], extra=None):
        return StrSql.from_template(sql_id, template, extra)

    @classmethod
    def template_to_str(cls, template: Tuple[str, Dict[str, str]]):
        sql, default = template
        return jinja2.Template(sql, undefined=jinja2.StrictUndefined).render(default)

    def get_str_sql(self, template: Tuple[str, Dict[str, str]]):
        return self.template_to_str(self.get_template(template))

    def get_template(self, template: Tuple[str, Dict[str, str]]):
        assert template
        t, default = template
        default.update(self.default)
        return jinja2.Template(t, undefined=jinja2.DebugUndefined).render(self.values), default
