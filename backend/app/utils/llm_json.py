import json
from typing import Any, Dict, Type, TypeVar

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


def parse_json_strict(text: str) -> Dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Empty response text")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Attempt to recover JSON embedded in extra text.
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def validate_model(model_cls: Type[T], data: Dict[str, Any]) -> T:
    return model_cls.model_validate(data)
