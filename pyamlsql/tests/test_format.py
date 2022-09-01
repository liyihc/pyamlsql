import sqlite3
from pyamlsql.sql_format_parameter import format_parameter
from datetime import datetime


def test_select():
    sql = "SELECT * FROM test LIMIT {num}"
    target = "SELECT * FROM test LIMIT 20"
    ret = format_parameter(sql, {'num': 20})
    assert target == ret


def test_list():
    sql = "SELECT * FROM test WHERE id in ({ids})"
    target = sql.format(ids="1,2,3,4,5,6,7,8,9")
    ret = format_parameter(sql, {'ids': range(1, 10)})
    assert target == ret


def test_str():
    sql = "SELECT * FROM test WHERE id = {id}"
    id = "abc123"
    target = sql.format(id=f"'{id}'")
    ret = format_parameter(sql, {'id': id})
    assert target == ret


def test_datetime():
    sql = "SELECT * FROM test WHERE id = {dt}"
    dt = datetime.now()
    target = sql.format(dt=f"'{dt}'")
    ret = format_parameter(sql, {"dt": dt})
    assert target == ret


def test_multiline():
    conn = sqlite3.Connection(":memory:")
    conn.execute("CREATE TABLE tmp(v text)")
    v = "123'\n\r12332\"\""
    conn.execute(format_parameter(
        "INSERT INTO tmp VALUES({v})",
        {
            "v": v
        }
    ))

    assert conn.execute("SELECT v FROM tmp").fetchone()[0] == v
