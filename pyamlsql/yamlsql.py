
from typing import Dict, List, Optional, Union, overload
from pathlib import Path
import yaml

from .sql_format_parameter import format_parameter
from .sql import SplitSql, StrSql, Sql, ValueSql


class YamlSql:
    def __init__(self, file_path: Union[str, Path, None] = None) -> None:
        if file_path:
            p = self.file_path = Path(file_path)
            if p.exists():
                with p.open('r') as i:
                    sqls: List[dict] = yaml.load(i, yaml.CLoader)['sqls']
                self.sqls = {s['sql_id']: Sql.from_dict(s) for s in sqls}
            else:
                self.sqls: Dict[str, Sql] = {}
        else:
            self.file_path = None
            self.sqls: Dict[str, Sql] = {}

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

    def add_str_value(self, sql_id: str, base: str, values: Dict[str, str], **extra):
        if sql_id in self.sqls:
            return
        self.sqls[sql_id] = ValueSql(sql_id, base, values, extra=extra)
        self.write()

    def to_dict_list(self):
        sqls = sorted(self.sqls.values(), key=lambda sql: sql.sql_id)
        return [sql.dict() for sql in sqls]

    def to_yaml(self):
        return yaml.dump({"sqls": self.to_dict_list()}, Dumper=yaml.CDumper, sort_keys=False)

    def to_yaml_file(self, path):
        with open(path, 'w') as o:
            yaml.dump({"sqls": self.to_dict_list()},
                      o, yaml.CDumper, sort_keys=False)

    def write(self):
        if self.file_path:
            self.to_yaml_file(self.file_path)

    def get_template(self, sql_id: str):
        sql = self.sqls[sql_id]
        if isinstance(sql, StrSql):
            return sql.get_template(None)
        return sql.get_template(self.get_template(sql.base_id) if sql.base_id else None)

    def get_format(self, sql_id: str, values: dict = None):
        sql = self.sqls[sql_id]
        if isinstance(sql, StrSql):
            ret = sql.get_str_sql(None)
        else:
            ret = sql.get_str_sql(self.get_template(
                sql.base_id) if sql.base_id else None)
        return format_parameter(ret, values or {})
