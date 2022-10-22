from pyamlsql.sql import SQL, HashSet
from pyamlsql.yamlsql import YamlSql


def test_yamlsql_to_from_yaml():
    ys = YamlSql()
    ys.add_sql(
        "a",
        """SELECT *
FROM table
WHERE a = 1""")

    yamltext = ys.to_yaml()
    assert ys.yaml.load(ys.to_yaml()) == ys.yaml.load(
        """sqls:
- sql_id: a
  sql: |
    SELECT *
    FROM table
    WHERE a = 1""")
    sqls = ys.yaml.load(yamltext)['sqls']
    sqls = {s['sql_id']: SQL.from_dict(s) for s in sqls}
    assert ys.sqls == sqls


def test_str():
    ys = YamlSql()
    ys.add_sql(
        "base", "SELECT * FROM test {{ STATEMENT1 }}", {"STATEMENT1": "WHERE id == 1"})
    target = "SELECT * FROM test WHERE id == 1"
    assert ys.get_format("base") == target
    assert ys.sqls["base"].cache[HashSet()] == target
