"""资产模块测试。"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from orchestrator.assets import AssetError, load_manifest, resolve_assets


@pytest.fixture()
def manifest_file(tmp_path: Path) -> Path:
    asset = tmp_path / "example.txt"
    asset.write_text("hello", encoding="utf-8")
    sha256 = hashlib.sha256(asset.read_bytes()).hexdigest()
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        json.dumps({"asset://example": {"file": "example.txt", "sha256": sha256}}),
        encoding="utf-8",
    )
    return manifest


def test_resolve_assets_success(manifest_file: Path) -> None:
    manifest = load_manifest(manifest_file)
    resolved = resolve_assets(["asset://example"], manifest)
    assert resolved["asset://example"].read_text(encoding="utf-8") == "hello"


def test_resolve_assets_missing(manifest_file: Path) -> None:
    manifest = load_manifest(manifest_file)
    with pytest.raises(AssetError):
        resolve_assets(["asset://missing"], manifest)
