import uuid
from enum import unique, Enum


def float_scale(x: float) -> str:
    return f"{x:.2f}"


@unique
class ExpenseSplitType(str, Enum):
    EQUAL = "EQUAL"
    EXACT = "EXACT"
    PERCENT = "PERCENT"
    WEIGHT = "WEIGHT"


def id_factory():
    return str(uuid.uuid4())
