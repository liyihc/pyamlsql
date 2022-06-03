from pyamlsql.sql import Sql
from pyamlsql.yamlsql import YamlSql
import yaml


def test_yamlsql_to_from_yaml():
    ys = YamlSql()
    ys.add_split_sql("split",
                     """
    SELECT *
    FROM table
    WHERE a = 1""")
    ys.add_str_sql(
        "str", "SELECT * FROM table UNION SELECT * FROM table 2")

    yamltext = ys.to_yaml()
    assert yamltext == \
        """sqls:
- sql_id: split
  type: split
  base_id: null
  sql:
    SELECT: '*'
    FROM: table
    WHERE: a = 1
  extra: ''
- sql_id: str
  type: str
  sql: SELECT * FROM table UNION SELECT * FROM table 2
  default: null
  extra: ''
"""

    sqls = yaml.load(yamltext, yaml.CLoader)['sqls']
    sqls = {s['sql_id']: Sql.from_dict(s) for s in sqls}
    assert ys.sqls == sqls


def test_split():
    ys = YamlSql()
    ys.add_split_sql(
        "base",
        """
        SELECT * FROM test
        WHERE id == 5
        """,
        flag=False
    )
    ys.add_split_sql(
        "tmp",
        {
            "WHERE": "id < 3"
        },
        "base",
        flag=True
    )

    for sql in ys.sqls.values():
        if sql.extra.get('flag', False):
            assert sql.sql_id == "tmp"

    target = {
        "SELECT": "* FROM test",
        "WHERE": "id < 3"
    }
    assert ys.get_template("tmp") == target
    assert ys.cache_template["tmp"] == target


def test_str():
    ys = YamlSql()
    ys.add_str_sql(
        "base", "SELECT * FROM test {{ STATEMENT1 }}", default={"STATEMENT1": "WHERE id == 1"})
    ys.add_str_value("value", "base", {"STATEMENT1": "WHERE id == 2"})
    target = "SELECT * FROM test WHERE id == 1"
    assert ys.get_format("base", {}) == target
    assert ys.cache_sql["base"] == target
    target = "SELECT * FROM test WHERE id == 2"
    assert ys.get_format("value", {}) == target
    base = ys.sqls['base']
    assert ys.cache_template["base"] == (base.sql, base.default)
    assert ys.cache_sql["value"] == target
