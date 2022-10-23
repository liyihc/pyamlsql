from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Mapping, Optional, Sequence, Set, Tuple, Union

import jinja2
from ruamel.yaml.scalarstring import LiteralScalarString

Condition = Union[Dict[str, bool], None]


def to_literal(d: Union[str, dict, list]):
    if isinstance(d, str):
        if not d or '\n' not in d:
            return d
        return LiteralScalarString(d)
    if isinstance(d, Mapping):
        return {k: vv for k, v in d.items() if (vv := to_literal(v))}
    if isinstance(d, Sequence):
        return list(map(to_literal, d))


"""
sql_id: 123
sql: {{ STATE1 }}
statements:
  STATE1:
    joiner: OR
    elements:
      - condition: condition1
        text: v = 1
      - text: w = 2
      - text:
          joiner: AND
          elements:
            - condition: condition3
              value: u = 4
            - condition: condition4
              value: c = 5
"""


class JoinStatementElement(BaseModel):
    condition: Union[str, None] = None
    text: Union[str, "JoinStatement", "IfStatement"]

    def get_template(self, conditions: Set[str]):
        if self.condition is not None and self.condition not in conditions:
            return None
        if isinstance(self.text, str):
            return self.text
        return self.text.get_template(conditions)


class JoinStatement(BaseModel):
    base: str
    joiner: str = ""
    elements: List[JoinStatementElement]

    @classmethod
    def from_statements(self, base: str, joiner: str, elements: Dict[str, Union[str, "JoinStatement", "IfStatement"]]):
        return JoinStatement(
            base=base,
            joiner=joiner,
            elements=[JoinStatementElement(condition=k, text=v) for k, v in elements.items()])

    def get_template(self, conditions: Set[str]):
        inner = f" {self.joiner} ".join(
            t for e in self.elements if (t := e.get_template(conditions)))
        if inner:
            return f"{self.base} {inner}" if self.base else inner
        return ""


class IfStatement(BaseModel):
    condition: str
    true_text: Union[str, JoinStatement, "IfStatement"]
    false_text: Union[str, JoinStatement, "IfStatement"] = ""

    def get_template(self, conditions: Set[str]):
        if self.condition in conditions:
            if isinstance(self.true_text, str):
                return self.true_text
            else:
                return self.true_text.get_template(conditions)
        if isinstance(self.false_text, str):
            return self.false_text
        return self.false_text.get_template(conditions)


JoinStatementElement.update_forward_refs(**locals())
IfStatement.update_forward_refs(**locals())


class HashSet(set):
    def __hash__(self):
        h = len(self)
        for item in self:
            h ^= hash(item)
        return h


class SQL(BaseModel):
    sql_id: str
    sql: str
    statements: Union[Dict[str, Union[str,
                                      JoinStatement, IfStatement]], None] = None
    extra: Dict[str, str] = {}
    cache: Dict[HashSet, str] = {}

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)

    def to_yaml_dict(self):
        return to_literal(self.dict())

    def get_template(self, conditions: Dict[str, bool]) -> str:
        condition_set = HashSet(k for k, v in conditions.items() if v)
        if condition_set in self.cache:
            return self.cache[condition_set]
        if self.statements:
            statements = {k: v if isinstance(v, str) else v.get_template(condition_set)
                          for k, v in self.statements.items()}
        else:
            statements = {}
        ret = jinja2.Template(
            self.sql, undefined=jinja2.StrictUndefined).render(statements)
        self.cache[condition_set] = ret
        return ret


# TODO: wrap with ()
def OR(base: str, statements: Dict[str, Union[str, JoinStatement, IfStatement]]):
    return JoinStatement.from_statements(base, "OR", statements)


def AND(base: str, statements: Dict[str, Union[str, JoinStatement, IfStatement]]):
    return JoinStatement.from_statements(base, "AND", statements)


def IF(condition: str, true_text: Union[str, JoinStatement, IfStatement], false_text: Union[str, JoinStatement, IfStatement] = ""):
    return IfStatement(condition=condition, true_text=true_text, false_text=false_text)
