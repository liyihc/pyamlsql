import re
from collections.abc import Iterable
from enum import Enum

numeric = re.compile(r"-?\d+\.?\d*(e[+-]?\d+)?")


def fp(param):
    if param is None:
        return 'Null'
    if isinstance(param, Enum):
        param = param.value
    if isinstance(param, bytes):
        param = param.decode()
    param = str(param)
    if numeric.fullmatch(param) is None:
        param = param.replace("'", "''")
        return f"'{param}'"
    return param


def format_parameter(sql: str, params: dict):
    for k, v in params.items():
        if isinstance(v, Iterable) and not isinstance(v, (bytes, str)):
            v = ','.join(map(fp, v))
        else:
            v = fp(v)
        params[k] = v
    return sql.format(**params)
