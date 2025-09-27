"""通用辅助函数。"""

from __future__ import annotations

import json
from typing import Any

try:  # pragma: no cover - 根据环境可能导入失败
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def load_yaml_text(text: str) -> Any:
    """在 PyYAML 不可用时退化为 JSON 解析。"""

    if yaml is not None:
        return yaml.safe_load(text)
    return json.loads(text)
