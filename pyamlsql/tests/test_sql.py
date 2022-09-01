from pyamlsql.sql import SplitSql, StrSql


def test_splitsql():
    sql = SplitSql.from_sql(
        "tmp",
        """
SELECT a,

    b,
    c
FROM
    d
WHERE a = 1
    AND b = 2
    OR
        c = 3
ORDER BY b desc""")

    assert sql.sql == {
        "SELECT":"a,\n\n    b,\n    c",
        "FROM":"\n    d",
        "WHERE":"a = 1\n    AND b = 2\n    OR\n        c = 3",
        "ORDER BY":"b desc"
    }
