"""轻量级 YAML 解析器，仅支持项目示例所需语法。"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import List, Tuple


class YAMLError(Exception):
    """与 PyYAML 保持一致的异常命名。"""


@dataclass
class _Line:
    indent: int
    content: str


class _MiniYAMLParser:
    def __init__(self, text: str):
        self.lines: List[_Line] = []
        for raw in text.splitlines():
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            self.lines.append(_Line(indent=indent, content=stripped))
        self.index = 0

    def parse(self):
        if not self.lines:
            return None
        return self._parse_block(expected_indent=self.lines[0].indent)

    def _parse_block(self, expected_indent: int):
        if self.index >= len(self.lines):
            return None
        # 判断当前块类型
        indent, content = self._peek()
        if content.startswith("- ") or content == "-":
            return self._parse_list(expected_indent)
        return self._parse_mapping(expected_indent)

    def _parse_mapping(self, expected_indent: int):
        result = {}
        while self.index < len(self.lines):
            indent, content = self._peek()
            if indent < expected_indent:
                break
            if indent > expected_indent:
                raise YAMLError(f"缩进错误: {content}")
            if content.startswith("- "):
                raise YAMLError("映射内不应直接出现列表项，请缩进正确")
            if ":" not in content:
                raise YAMLError(f"无效的映射行: {content}")
            key, remainder = content.split(":", 1)
            key = key.strip()
            remainder = remainder.strip()
            self.index += 1
            if remainder:
                result[key] = self._convert_value(remainder)
            else:
                result[key] = self._parse_block(expected_indent + 2)
        return result

    def _parse_list(self, expected_indent: int):
        items = []
        while self.index < len(self.lines):
            indent, content = self._peek()
            if indent < expected_indent or not (content.startswith("- ") or content == "-"):
                break
            if indent > expected_indent:
                raise YAMLError(f"列表项缩进错误: {content}")
            value_text = content[1:].strip() if content == "-" else content[2:].strip()
            self.index += 1
            if value_text:
                items.append(self._convert_value(value_text))
            else:
                items.append(self._parse_block(expected_indent + 2))
        return items

    def _convert_value(self, text: str):
        if text.startswith("\"") and text.endswith("\""):
            return text[1:-1]
        if text.startswith("'") and text.endswith("'"):
            return text[1:-1]
        lowered = text.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if lowered == "null":
            return None
        # 尝试数字
        try:
            if "." in text:
                return float(text)
            return int(text)
        except ValueError:
            pass
        if text.startswith("[") or text.startswith("{"):
            try:
                return ast.literal_eval(text)
            except (ValueError, SyntaxError) as exc:
                raise YAMLError(f"无法解析内联结构: {text}") from exc
        return text

    def _peek(self) -> Tuple[int, str]:
        line = self.lines[self.index]
        return line.indent, line.content


def safe_load(text: str):
    """解析 YAML 文本。"""

    parser = _MiniYAMLParser(text)
    return parser.parse()


__all__ = ["safe_load", "YAMLError"]
