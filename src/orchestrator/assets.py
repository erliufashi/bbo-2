"""资产解析与校验模块。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Mapping

from .utils import load_yaml_text


@dataclass
class Asset:
    """代表一个可被测试使用的资产文件。"""

    uri: str
    path: Path
    sha256: str

    def verify(self) -> None:
        """验证资产文件的 SHA256 哈希值，确保内容未被篡改。"""

        hasher = hashlib.sha256()
        with self.path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                hasher.update(chunk)
        digest = hasher.hexdigest()
        if digest != self.sha256:
            raise ValueError(
                f"资产 {self.uri} 的校验值不匹配，期望 {self.sha256}，实际 {digest}"
            )


class AssetRegistry:
    """管理资产清单 ``manifest.yaml`` 的工具类。"""

    def __init__(self, manifest_path: Path) -> None:
        self.manifest_path = manifest_path
        self._assets = self._load_manifest(manifest_path)

    @staticmethod
    def _load_manifest(path: Path) -> Dict[str, Dict[str, str]]:
        if not path.exists():
            raise FileNotFoundError(f"资产清单文件不存在: {path}")
        data = load_yaml_text(path.read_text(encoding="utf-8"))
        if not isinstance(data, Mapping):
            raise ValueError("资产清单必须是映射结构")
        assets = data.get("assets")
        if not isinstance(assets, Iterable):
            raise ValueError("资产清单缺少 assets 列表")
        index: Dict[str, Dict[str, str]] = {}
        for item in assets:
            if not isinstance(item, Mapping):
                raise ValueError("资产项必须是字典")
            uri = item.get("uri")
            sha256 = item.get("sha256")
            file = item.get("file")
            if not (uri and sha256 and file):
                raise ValueError("资产项缺少必需字段 uri/sha256/file")
            index[str(uri)] = {"sha256": str(sha256), "file": str(file)}
        return index

    def resolve(self, uri: str, *, base_dir: Path) -> Asset:
        """根据 ``asset://`` URI 查找资产，并验证其存在性。"""

        if not uri.startswith("asset://"):
            raise ValueError("仅支持 asset:// URI")
        if uri not in self._assets:
            raise KeyError(f"未在资产清单中找到 {uri}")
        meta = self._assets[uri]
        asset_path = (base_dir / meta["file"]).resolve()
        if not asset_path.exists():
            raise FileNotFoundError(f"资产文件不存在: {asset_path}")
        asset = Asset(uri=uri, path=asset_path, sha256=meta["sha256"])
        asset.verify()
        return asset

    def list_assets(self) -> Dict[str, Dict[str, str]]:
        """返回原始资产索引的拷贝，便于测试。"""

        return dict(self._assets)


__all__ = ["Asset", "AssetRegistry"]
