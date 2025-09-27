"""简易 YAML 解析与序列化工具。"""
from __future__ import annotations

import json
from typing import Any, Iterable


def _parse_value(raw: str) -> Any:
    raw = raw.strip()
    if raw.startswith("\"") and raw.endswith("\""):
        return raw[1:-1]
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    if raw in {"true", "True"}:
        return True
    if raw in {"false", "False"}:
        return False
    if raw.isdigit():
        return int(raw)
    try:
        return float(raw)
    except ValueError:
        return raw


def safe_load(stream: str | Iterable[str]) -> Any:
    if not isinstance(stream, str):
        stream = "".join(stream)
    text = str(stream).strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    lines = [line.rstrip("\n") for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    index = 0

    def parse_block(indent: int) -> Any:
        nonlocal index
        items = []
        mapping = {}
        is_list = False
        while index < len(lines):
            line = lines[index]
            current_indent = len(line) - len(line.lstrip(" "))
            if current_indent < indent:
                break
            if line.lstrip().startswith("- "):
                is_list = True
                value_part = line.lstrip()[2:]
                index += 1
                if value_part:
                    items.append(_parse_value(value_part))
                else:
                    items.append(parse_block(current_indent + 2))
            else:
                key, _, value_part = line.strip().partition(":")
                if not _:
                    raise ValueError(f"无法解析的行: {line}")
                if value_part.strip():
                    mapping[key] = _parse_value(value_part)
                    index += 1
                else:
                    index += 1
                    mapping[key] = parse_block(current_indent + 2)
        return items if is_list else mapping

    result = parse_block(0)
    return result


def _dump_value(value: Any, indent: int) -> list[str]:
    prefix = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, val in value.items():
            if isinstance(val, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(_dump_value(val, indent + 2))
            else:
                rendered = repr(val) if isinstance(val, str) and " " in val else val
                lines.append(f"{prefix}{key}: {rendered}")
        return lines
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(_dump_value(item, indent + 2))
            else:
                lines.append(f"{prefix}- {item}")
        return lines
    return [f"{prefix}{value}"]


def safe_dump(data: Any, allow_unicode: bool = True) -> str:  # noqa: ARG001
    return "\n".join(_dump_value(data, 0)) + "\n"


__all__ = ["safe_load", "safe_dump"]
