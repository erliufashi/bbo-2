"""运行期数据装载模块。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .utils import load_yaml_text


@dataclass
class DatasetMount:
    """表示一次运行期数据挂载结果。"""

    name: str
    mounted_path: Path

    def is_ready(self) -> bool:
        """检查挂载路径是否就绪。"""

        return self.mounted_path.exists()


class DatasetLoader:
    """根据 ``DATASET.yaml`` 将运行期数据挂载到本地。"""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir

    def load(self, manifest: Path, profile: str) -> DatasetMount:
        """加载指定 profile 的运行期数据。"""

        if not manifest.exists():
            raise FileNotFoundError(f"运行期数据描述文件不存在: {manifest}")
        data = load_yaml_text(manifest.read_text(encoding="utf-8"))
        if not isinstance(data, Mapping) or "profiles" not in data:
            raise ValueError("DATASET.yaml 缺少 profiles 字段")
        profiles = data["profiles"]
        if not isinstance(profiles, Mapping) or profile not in profiles:
            raise KeyError(f"DATASET.yaml 中不存在 profile: {profile}")
        entry = profiles[profile]
        if not isinstance(entry, Mapping) or "path" not in entry:
            raise ValueError("profile 定义必须包含 path")
        path = (self.root_dir / entry["path"]).resolve()
        if not path.exists():
            raise FileNotFoundError(f"运行期数据路径不存在: {path}")
        return DatasetMount(name=profile, mounted_path=path)


__all__ = ["DatasetLoader", "DatasetMount"]
