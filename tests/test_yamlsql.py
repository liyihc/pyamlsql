from pyamlsql.sql import Sql
from pyamlsql.yamlsql import YamlSql


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
    assert ys.yaml.load(ys.to_yaml()) == ys.yaml.load(
        """sqls:
- sql_id: split
  type: split
  base_id:
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
""")
    sqls = ys.yaml.load(yamltext)['sqls']
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


def test_split_get_format_with():
    ys = YamlSql()
    ys.add_split_sql("base",
                     """
    SELECT *
    FROM test
    WHERE a = 1
    """)
    assert ys.get_format_with(
        "base", {"WHERE": "b = 3"}) == "SELECT *\nFROM test\nWHERE b = 3"


def test_str_get_format_with():
    ys = YamlSql()
    ys.add_str_sql("base", "SELECT * FROM {{ table }}")
    assert ys.get_format_with("base", {"table": "myt"}) == "SELECT * FROM myt"
