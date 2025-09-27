"""资产管理模块，负责解析 asset:// URI 并校验内容。"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Mapping

from ._yaml import safe_load


class AssetError(RuntimeError):
    """资产处理相关异常。"""


@dataclass(slots=True)
class AssetRecord:
    """资产清单中的单条记录。"""

    uri: str
    file: Path
    sha256: str


def load_manifest(path: str | Path) -> Dict[str, AssetRecord]:
    """读取资产清单并返回可查询字典。"""

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"找不到资产清单: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = safe_load(fh.read()) or {}
    if not isinstance(data, Mapping):
        raise AssetError("资产清单必须是字典")
    base = path.parent
    manifest: Dict[str, AssetRecord] = {}
    for uri, info in data.items():
        if not isinstance(info, Mapping):
            raise AssetError(f"资产 {uri} 配置必须是字典")
        file_path = base / str(info.get("file", ""))
        sha256 = str(info.get("sha256", ""))
        if not file_path.exists():
            raise AssetError(f"资产文件缺失: {file_path}")
        if not sha256:
            raise AssetError(f"资产 {uri} 缺少 sha256")
        manifest[uri] = AssetRecord(uri=uri, file=file_path, sha256=sha256)
    return manifest


def verify_asset(record: AssetRecord) -> None:
    """校验资产文件的哈希值是否匹配。"""

    digest = hashlib.sha256(record.file.read_bytes()).hexdigest()
    if digest != record.sha256:
        raise AssetError(f"资产 {record.uri} 校验失败，期望 {record.sha256} 实际 {digest}")


def resolve_assets(uris: Iterable[str], manifest: Mapping[str, AssetRecord]) -> Dict[str, Path]:
    """解析 asset:// URI 为本地路径并执行校验。"""

    resolved: Dict[str, Path] = {}
    for uri in uris:
        if uri not in manifest:
            raise AssetError(f"未在清单中找到资产: {uri}")
        record = manifest[uri]
        verify_asset(record)
        resolved[uri] = record.file
    return resolved


__all__ = ["AssetError", "AssetRecord", "load_manifest", "verify_asset", "resolve_assets"]
