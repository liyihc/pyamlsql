# PYamlSql

This is a simple tool to help me manage and generate SQL.

## Sql Template

### Split Sql

```python
from pyamlsql import YamlSql
ys = YamlSql()
ys.add_split_sql(
    "id1", 
    {
        "SELECT": "* FROM t1",
        "WHERE": "val > 5"
    }
)

ys.get_format("id1")
# SELECT * FROM t1
# WHERE val > 5

ys.add_split_sql(
    "id2",
    {
        "WHERE": "other_val = 3"
    }, base="id1"
)

ys.get_format("id2")
# SELECT * FROM t1
# WHERE other_val = 3

ys.to_yaml(no_base=True)
# sqls:
# - sql_id: id1
#   type: split
#   sql:
#     SELECT: '* FROM t1'
#     WHERE: val > 5
#   extra:
# - sql_id: id2
#   type: split
#   sql:
#     SELECT: '* FROM t1'
#     WHERE: other_val = 3
#   extra:
```

### Str Sql

```python
from pyamlsql import YamlSql
ys = YamlSql()
ys.add_str_sql(
    "id1",
    "select id, val from t1 {{ statement_1 }}",
    default={"statement_1":"where val = 3 limit 3"}
)

ys.get_format("id1")
# select id, val from t1 where val = 3 limit 3

ys.add_str_value(
    "id2",
    base="id1",
    values={
        "statement_1":"{{ where_statement }} {{ order_statement }}"
    },
    default={"where_statement":"val = 5", "order_statement":"order by val"}
)
ys.get_format("id2")
# select id, val from t1 val = 5 order by val

ys.to_yaml(no_base=True)
# sqls:
# - sql_id: id1
#   type: str
#   sql: select id, val from t1 {{ statement_1 }}
#   default:
#     statement_1: where val = 3 limit 3
#   extra:
# - sql_id: id2
#   type: str
#   sql: select id, val from t1 {{ where_statement }} {{ order_statement }}
#   default:
#     statement_1: where val = 3 limit 3
#     where_statement: val = 5
#     order_statement: order by val
#   extra:
```

## format value

> to be completed