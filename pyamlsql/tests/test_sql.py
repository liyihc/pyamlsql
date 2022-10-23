from io import StringIO
from ..sql import SQL, OR, AND, IF, SWITCH
from ruamel import yaml


def test_join():
    ys = SQL(
        sql_id="1",
        sql="""
            SELECT *
            FROM t1
            {{ CONDITION }}
        """,
        statements={
            "CONDITION": OR("WHERE", {
                "condition1": "v = 1",
                "condition2": "v = 2"
            })
        }
    )

    assert ys.get_template({"condition1": 1}) == """
            SELECT *
            FROM t1
            WHERE v = 1
        """


def test_join_recursive():
    s = OR("WHERE",
           {
               "a": "a = 1",
               "b": "b = 1",
               "c": AND("",
                        {
                            "d": "d = 1",
                            "e": "e = 1"
                        }
                        )
           }
           )

    assert s.get_template({"a", "c", "d", "e"}
                          ) == "WHERE a = 1 OR d = 1 AND e = 1"
    assert s.get_template({}) == ""
    text = """
base: WHERE
joiner: OR
elements:
  - condition: a
    text: a = 1
  - condition: b
    text: b = 1
  - condition: c
    text:
      base: ""
      joiner: AND
      elements:
        - condition: d
          text: d = 1
        - condition: e
          text: e = 1
    """
    assert s.dict() == yaml.safe_load(text)


def test_if():
    s = IF("a", "a > 1", "a < 1")
    assert s.get_template({"a"}) == "a > 1"
    assert s.get_template({}) == "a < 1"


def test_if_recursive():
    s = IF("a", AND("WHERE", {"a": "a > 1"}), OR("WHERE", {"b": "b > 1"}))
    assert s.get_template({"a"}) == "WHERE a > 1"
    assert s.get_template({"b"}) == "WHERE b > 1"

    s = IF("a", IF("b", "a = b", "a = 1"), IF("b", "b = 1"))
    assert s.get_template({"a", "b"}) == "a = b"
    assert s.get_template({"a"}) == "a = 1"
    assert s.get_template({"b"}) == "b = 1"
    assert s.get_template({}) == ""
    text = """
condition: a
true_text:
  condition: b
  true_text: a = b
  false_text: a = 1
false_text:
  condition: b
  true_text: b = 1
  false_text: ''
    """
    assert s.dict() == yaml.safe_load(text)


def test_switch():
    s = SWITCH(
        {
            "a": "a",
            "b": "b"
        },
        "c"
    )
    assert s.get_template({"a", "b"}) == "a"
    assert s.get_template({"b"}) == "b"
    assert s.get_template({}) == "c"
