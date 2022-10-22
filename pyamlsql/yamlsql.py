
from copy import deepcopy
from io import StringIO
from traceback import print_exc
from typing import Any, Dict, List, Optional, Tuple, Union, overload
from pathlib import Path
from ruamel.yaml import YAML

from .sql_format_parameter import format_parameter
from .sql import JoinStatement, SQL


class YamlSql:
    def __init__(self, file_path: Union[str, Path, None] = None) -> None:
        self.yaml = YAML()
        if file_path:
            p = self.file_path = Path(file_path)
            if p.exists():
                try:
                    with p.open('r') as i:
                        sqls: List[dict] = self.yaml.load(i)['sqls']
                    self.sqls = {s['sql_id']: SQL.parse_obj(s) for s in sqls}
                except Exception as e:
                    print_exc()
                    self.sqls = {}
            else:
                self.sqls: Dict[str, SQL] = {}
        else:
            self.file_path = None
            self.sqls: Dict[str, SQL] = {}

    def add_sql(self, sql_id: str, sql: str, statements: Optional[Dict[str, Union[str, JoinStatement]]] = None):
        if sql_id in self.sqls:
            return
        self.sqls[sql_id] = SQL(
            sql_id=sql_id,
            sql=sql,
            statements=statements
        )

    def to_dict_list(self):
        sqls = sorted(self.sqls.values(), key=lambda sql: sql.sql_id)
        ret = []
        for sql in sqls:
            ret.append(sql.to_yaml_dict())
        return ret

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

    def get_format(self, sql_id: str, values: dict = None, conditions: dict = None):
        sql = self.sqls[sql_id]
        return format_parameter(sql.get_template(conditions or {}), values or {})
