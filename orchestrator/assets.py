"""资产解析与校验模块（使用 JSON 格式清单）。"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable


@dataclass
class AssetEntry:
    name: str
    path: Path
    sha256: str


class AssetManifest:
    def __init__(self, base_dir: Path, manifest_file: Path):
        self.base_dir = base_dir
        self.manifest_file = manifest_file
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        self._entries: Dict[str, AssetEntry] = {}
        for item in data.get("assets", []):
            entry = AssetEntry(
                name=item["name"],
                path=base_dir / Path(item["path"]),
                sha256=item["sha256"],
            )
            self._entries[entry.name] = entry

    def verify(self) -> Iterable[str]:
        failures = []
        for entry in self._entries.values():
            if not entry.path.exists():
                failures.append(f"资产 {entry.name} 对应文件不存在")
                continue
            digest = hashlib.sha256(entry.path.read_bytes()).hexdigest()
            if digest != entry.sha256:
                failures.append(f"资产 {entry.name} 的 sha256 不匹配")
        return failures

    def resolve(self, uri: str) -> Path:
        if not uri.startswith("asset://"):
            raise ValueError("仅支持 asset:// URI")
        name = uri[len("asset://") :]
        if name not in self._entries:
            raise KeyError(f"未在清单中找到资产：{name}")
        return self._entries[name].path


__all__ = ["AssetManifest", "AssetEntry"]
