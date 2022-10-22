from io import StringIO
from ..sql import SQL, OR, AND
from ruamel import yaml


def test_recursive():
    ys = SQL(
        sql_id="1",
        sql="""
            SELECT *
            FROM t1
            WHERE {{ CONDITION }}
        """,
        statements={
            "CONDITION": OR({
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


def test_deep_recursive():
    s = OR(
        {
            "a": "a = 1",
            "b": "b = 1",
            "c": AND(
                {
                    "d": "d = 1",
                    "e": "e = 1"
                }
            )
        }
    )

    assert s.get_template({"a", "c", "d", "e"}
                          ) == "a = 1 OR d = 1 AND e = 1"
    text = """
joiner: OR
elements:
  - condition: a
    text: a = 1
  - condition: b
    text: b = 1
  - condition: c
    text:
      joiner: AND
      elements:
        - condition: d
          text: d = 1
        - condition: e
          text: e = 1
    """
    assert s.dict() == yaml.safe_load(text)
