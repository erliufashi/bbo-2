"""运行时数据集装载模块（JSON 格式）。"""
from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


@dataclass
class DatasetMount:
    mounted_path: Path
    files: List[Path]


class DatasetLoader:
    def __init__(self, manifest_file: Path):
        self.manifest_file = manifest_file
        raw = json.loads(manifest_file.read_text(encoding="utf-8")) or {}
        self._runtime_entries = raw.get("runtime", [])

    def profiles(self) -> Iterable[str]:
        return sorted({item.get("profile") for item in self._runtime_entries if item.get("profile")})

    def load(self, profile: str) -> DatasetMount:
        selected = [item for item in self._runtime_entries if item.get("profile") == profile]
        if not selected:
            raise ValueError(f"未找到 profile={profile} 对应的数据集条目")
        mount_dir = Path(tempfile.mkdtemp(prefix=f"dataset-{profile}-"))
        copied: List[Path] = []
        for item in selected:
            src = self.manifest_file.parent / item["file"]
            if not src.exists():
                raise FileNotFoundError(f"数据文件不存在：{src}")
            dst = mount_dir / src.name
            _ensure_directory(dst.parent)
            shutil.copy2(src, dst)
            copied.append(dst)
        return DatasetMount(mounted_path=mount_dir, files=copied)


__all__ = ["DatasetLoader", "DatasetMount"]
