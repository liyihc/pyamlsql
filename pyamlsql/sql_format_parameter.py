import re
from collections.abc import Iterable
from enum import Enum

numeric = re.compile(r"-?\d+\.?\d*(e[+-]?\d+)?")


def fp(param):
    if isinstance(param, (bytes, str)):
        if isinstance(param, bytes):
            param = param.decode()
        return f"'{param}'"
    elif param is None:
        return 'Null'
    else:
        param = str(param)
        if numeric.fullmatch(param) is None:
            return f"'{param}'"
        return param


def format_parameter(sql: str, params: dict):
    for k, v in params.items():
        if isinstance(v, Enum):
            v = v.value
        if isinstance(v, Iterable):
            if isinstance(v, str):
                params[k] = f"'{v}'"
            elif isinstance(v, bytes):
                params[k] = f"'{v.decode()}'"
            else:
                params[k] = ','.join(map(fp, v))
        else:
            params[k] = fp(v)
    return sql.format(**params)
