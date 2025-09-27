"""资产解析与校验模块。"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Dict, Iterable, Mapping

import yaml


@dataclass(slots=True)
class AssetRecord:
    """资产清单中的条目。"""

    name: str
    path: Path
    checksum: str


class AssetError(Exception):
    """资产相关操作的统一异常类型。"""


def _calc_sha256(path: Path) -> str:
    """计算文件的 SHA256，用于完整性校验。"""

    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: str | Path) -> Dict[str, AssetRecord]:
    """读取资产清单文件。"""

    manifest_path = Path(path)
    if not manifest_path.exists():
        raise AssetError(f"资产清单 {manifest_path} 不存在")
    try:
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:  # pragma: no cover
        raise AssetError(f"解析资产清单失败: {exc}") from exc
    assets_data = data.get("assets") if isinstance(data, Mapping) else None
    if not isinstance(assets_data, Mapping):
        raise AssetError("资产清单必须包含 assets 映射")

    records: Dict[str, AssetRecord] = {}
    base_dir = manifest_path.parent
    for name, entry in assets_data.items():
        if not isinstance(entry, Mapping):
            raise AssetError(f"资产 {name} 配置应为映射类型")
        if "path" not in entry or "sha256" not in entry:
            raise AssetError(f"资产 {name} 缺少 path 或 sha256 字段")
        record = AssetRecord(
            name=name,
            path=base_dir / str(entry["path"]),
            checksum=str(entry["sha256"]),
        )
        records[name] = record
    return records


class AssetResolver:
    """负责根据 URI 解析资产并执行校验。"""

    def __init__(self, records: Mapping[str, AssetRecord]):
        self._records = dict(records)

    def available(self) -> Iterable[str]:
        """返回可用资产名称。"""

        return self._records.keys()

    def resolve(self, uri: str) -> Path:
        """根据 `asset://` URI 返回本地文件路径并校验。"""

        if not uri.startswith("asset://"):
            raise AssetError("仅支持 asset:// URI")
        name = uri[len("asset://") :]
        if name not in self._records:
            raise AssetError(f"未在清单中找到资产 {name}")
        record = self._records[name]
        if not record.path.exists():
            raise AssetError(f"资产文件 {record.path} 不存在")
        actual = _calc_sha256(record.path)
        if actual != record.checksum:
            raise AssetError(
                f"资产 {name} 校验失败，期望 {record.checksum} 实际 {actual}"
            )
        return record.path


__all__ = ["AssetRecord", "AssetResolver", "AssetError", "load_manifest"]
