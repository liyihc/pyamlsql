
from copy import deepcopy
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple, Union, overload
from pathlib import Path
from ruamel.yaml import YAML

from .sql_format_parameter import format_parameter
from .sql import SplitSql, StrSql, Sql, ValueSql


class YamlSql:
    def __init__(self, file_path: Union[str, Path, None] = None) -> None:
        self.yaml = YAML()
        if file_path:
            p = self.file_path = Path(file_path)
            if p.exists():
                with p.open('r') as i:
                    sqls: List[dict] = self.yaml.load(i)['sqls']
                self.sqls = {s['sql_id']: Sql.from_dict(s) for s in sqls}
            else:
                self.sqls: Dict[str, Sql] = {}
        else:
            self.file_path = None
            self.sqls: Dict[str, Sql] = {}
        self.cache_sql: Dict[str, str] = {}
        self.cache_template: Dict[str, Any] = {}

    @overload
    def add_split_sql(self, sql_id: str, sql: str, **extra): ...

    @overload
    def add_split_sql(self, sql_id: str, sql: str, base: str = None, **
                      extra): ...

    @overload
    def add_split_sql(self, sql_id: str, sql: Dict[str, str], **extra): ...

    @overload
    def add_split_sql(self, sql_id: str,
                      sql: Dict[str, str], base: str = None, **extra): ...

    def add_split_sql(self, sql_id: str, sql: Union[str, Dict[str, str]], base: str = None, **extra):
        if sql_id in self.sqls:
            return
        if isinstance(sql, dict):
            split_sql = SplitSql(sql_id, base, sql, extra=extra)
        else:
            split_sql = SplitSql.from_sql(sql_id, sql, base, extra=extra)
        self.sqls[sql_id] = split_sql
        self.write()

    def add_str_sql(self, sql_id: str, sql: str, default: Dict[str, str] = None, **extra):
        if sql_id in self.sqls:
            return

        str_sql = StrSql(sql_id, sql, default or {}, extra=extra)
        self.sqls[sql_id] = str_sql
        self.write()

    def add_str_value(self, sql_id: str, base: str, values: Dict[str, str], default: Dict[str, str] = None, **extra):
        if sql_id in self.sqls:
            return
        self.sqls[sql_id] = ValueSql(
            sql_id, base, values, default or {}, extra=extra)
        self.write()

    def to_dict_list(self):
        sqls = sorted(self.sqls.values(), key=lambda sql: sql.sql_id)
        return [sql.dict() for sql in sqls]

    def to_yaml(self):
        buf = StringIO()
        self.yaml.dump({"sqls": self.to_dict_list()}, buf)
        return buf.getvalue()

    def to_yaml_file(self, path):
        with open(path, 'w') as o:
            self.yaml.dump({"sqls": self.to_dict_list()}, o)

    def write(self):
        if self.file_path:
            self.to_yaml_file(self.file_path)

    def get_template(self, sql_id: str):
        if sql_id in self.cache_template:
            return deepcopy(self.cache_template[sql_id])
        sql = self.sqls[sql_id]
        template: Union[Tuple[str, Dict[str, str]], Dict[str, str], None]
        if isinstance(sql, StrSql):
            template = sql.get_template(None)
        else:
            template = sql.get_template(
                self.get_template(sql.base_id) if sql.base_id else None)
        self.cache_template[sql_id] = deepcopy(template)
        return template

    def get_format(self, sql_id: str, values: dict = None):
        if sql_id in self.cache_sql:
            ret = self.cache_sql[sql_id]
        else:
            sql = self.sqls[sql_id]
            if isinstance(sql, StrSql):
                ret = sql.get_str_sql(None)
            else:
                ret = sql.get_str_sql(self.get_template(
                    sql.base_id) if sql.base_id else None)
            self.cache_sql[sql_id] = ret
        return format_parameter(ret, values or {})

    def get_format_with(self, sql_id: str, sql_or_values: Dict[str, str], values: dict = None):
        sql = self.sqls[sql_id]
        template = self.get_template(sql_id)
        if isinstance(sql, SplitSql):
            template.update(sql_or_values)
            ret = sql.template_to_str(template)
        else:
            t1, t2 = template
            t2.update(sql_or_values)
            ret = sql.template_to_str((t1, t2))
        return format_parameter(ret, values or {})
