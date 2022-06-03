from pyamlsql import YamlSql


def test_recursive():
    ys = YamlSql()
    ys.add_str_sql(
        'base',
        """
            SELECT *
            FROM t1
            WHERE v = 1
            {{ FINAL }} """
    )
    ys.add_str_value(
        'value1',
        base='base',
        values={
            "FINAL": "ORDER BY id {{ ORDER }}"
        },
        default={"ORDER": ""}
    )

    ys.add_str_value(
        'value2',
        base='value1',
        values={"ORDER": "DESC"}
    )

    assert ys.get_format('value1') == """
            SELECT *
            FROM t1
            WHERE v = 1
            ORDER BY id  """

    assert ys.get_format('value2') == """
            SELECT *
            FROM t1
            WHERE v = 1
            ORDER BY id DESC """