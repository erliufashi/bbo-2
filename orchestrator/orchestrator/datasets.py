"""运行期数据集装载模块。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from ._yaml import safe_load


class DatasetError(RuntimeError):
    """数据集声明异常。"""


@dataclass(slots=True)
class DatasetProfile:
    """单条运行期数据声明。"""

    name: str
    file: Path
    profile: str


def load_dataset(manifest: str | Path, profile: str) -> List[DatasetProfile]:
    """读取 DATASET.yaml，过滤匹配 profile 的数据集。"""

    manifest = Path(manifest)
    if not manifest.exists():
        raise FileNotFoundError(f"找不到数据集声明: {manifest}")
    with manifest.open("r", encoding="utf-8") as fh:
        data = safe_load(fh.read()) or []
    if not isinstance(data, Iterable):
        raise DatasetError("DATASET.yaml 需为列表")
    base = manifest.parent
    result: List[DatasetProfile] = []
    for item in data:
        if not isinstance(item, dict):
            raise DatasetError("数据集条目必须是字典")
        if item.get("profile") != profile:
            continue
        file_path = base / str(item.get("file", ""))
        if not file_path.exists():
            raise DatasetError(f"数据集文件缺失: {file_path}")
        name = str(item.get("name") or file_path.stem)
        result.append(DatasetProfile(name=name, file=file_path, profile=profile))
    return result


__all__ = ["DatasetError", "DatasetProfile", "load_dataset"]
