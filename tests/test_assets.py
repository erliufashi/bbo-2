"""资产解析模块测试。"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from orchestrator.assets import AssetRegistry


def _create_file(path: Path, content: bytes) -> str:
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def test_asset_registry_resolve(tmp_path: Path) -> None:
    asset_file = tmp_path / "foo.txt"
    digest = _create_file(asset_file, b"hello world")
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        "{\"assets\": [{\"uri\": \"asset://foo\", \"file\": \"%s\", \"sha256\": \"%s\"}]}"
        % (asset_file.name, digest),
        encoding="utf-8",
    )

    registry = AssetRegistry(manifest)
    asset = registry.resolve("asset://foo", base_dir=tmp_path)

    assert asset.path == asset_file
    assert asset.verify() is None


def test_asset_registry_sha_mismatch(tmp_path: Path) -> None:
    asset_file = tmp_path / "bar.txt"
    _create_file(asset_file, b"content")
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        "{\"assets\": [{\"uri\": \"asset://bar\", \"file\": \"%s\", \"sha256\": \"0000\"}]}"
        % asset_file.name,
        encoding="utf-8",
    )
    registry = AssetRegistry(manifest)

    with pytest.raises(ValueError):
        registry.resolve("asset://bar", base_dir=tmp_path)
