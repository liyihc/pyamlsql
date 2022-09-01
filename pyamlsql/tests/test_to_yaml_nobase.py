
from pyamlsql.yamlsql import YamlSql


def test_split_nobase():
    ys = YamlSql()
    ys.add_split_sql("base",
                     """
    SELECT *
    FROM t1
    WHERE a == b
    """)
    ys.add_split_sql("s1", "WHERE a > b", "base")

    sqls = ys.to_dict_list(True)
    assert sqls[1]['sql'] == {
        "SELECT": "*",
        "FROM": "t1",
        "WHERE": "a > b"
    }


def test_str_value():
    ys = YamlSql()
    ys.add_str_sql("base", """
    {{ select }}
    {{ from }}
    """, {"select": "select *", "from": "from t1"})

    ys.add_str_value("s1", 'base', {"select": "select a"})
    ys.add_str_value("s2", 's1', {}, {"from": "from t2"})
    sqls = ys.to_dict_list(True)
    assert sqls[2]['sql'] == """
    select a
    {{ from }}
    """
