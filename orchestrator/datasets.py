"""运行期数据加载模块。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Mapping

import yaml


class DatasetError(Exception):
    """数据集操作相关错误。"""


@dataclass(slots=True)
class DatasetProfile:
    """单个数据集配置。"""

    name: str
    files: tuple[Path, ...]


class DatasetLoader:
    """负责加载 DATASET.yaml 并校验文件存在。"""

    def __init__(self, profiles: Mapping[str, DatasetProfile]):
        self._profiles = dict(profiles)

    @classmethod
    def from_file(cls, path: str | Path) -> "DatasetLoader":
        """从 DATASET.yaml 构造加载器。"""

        dataset_path = Path(path)
        if not dataset_path.exists():
            raise DatasetError(f"数据集文件 {dataset_path} 不存在")
        try:
            data = yaml.safe_load(dataset_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:  # pragma: no cover
            raise DatasetError(f"解析数据集文件失败: {exc}") from exc
        profiles_data = data.get("profiles") if isinstance(data, Mapping) else None
        if not isinstance(profiles_data, Mapping):
            raise DatasetError("DATASET.yaml 必须包含 profiles 映射")

        profiles: Dict[str, DatasetProfile] = {}
        base_dir = dataset_path.parent
        for name, entry in profiles_data.items():
            if not isinstance(entry, Mapping):
                raise DatasetError(f"数据集 {name} 配置应为映射类型")
            raw_files = entry.get("files")
            if not isinstance(raw_files, Iterable):
                raise DatasetError(f"数据集 {name} 缺少 files 列表")
            paths = tuple(base_dir / str(item) for item in raw_files)
            for file_path in paths:
                if not file_path.exists():
                    raise DatasetError(f"数据集文件 {file_path} 不存在")
            profiles[name] = DatasetProfile(name=name, files=paths)
        return cls(profiles)

    def available(self) -> Iterable[str]:
        """返回可用配置名称。"""

        return self._profiles.keys()

    def get(self, name: str) -> DatasetProfile:
        """返回指定配置，若不存在则抛出异常。"""

        if name not in self._profiles:
            raise DatasetError(f"未找到名为 {name} 的数据集配置")
        return self._profiles[name]


__all__ = ["DatasetLoader", "DatasetProfile", "DatasetError"]
