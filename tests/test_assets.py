"""资产模块测试。"""
from __future__ import annotations

from pathlib import Path

import json
import pytest

from orchestrator.assets import AssetManifest


def test_asset_manifest_verify_success(tmp_path: Path) -> None:
    manifest_path = Path("services/order_service/tests/assets/manifest.yaml")
    manifest = AssetManifest(manifest_path.parent, manifest_path)
    assert list(manifest.verify()) == []
    resolved = manifest.resolve("asset://sample")
    assert resolved.exists()


def test_asset_manifest_failure(tmp_path: Path) -> None:
    bad_manifest = tmp_path / "manifest.yaml"
    asset_file = tmp_path / "asset.txt"
    asset_file.write_text("内容", encoding="utf-8")
    bad_manifest.write_text(
        json.dumps({"assets": [{"name": "bad", "path": "asset.txt", "sha256": "123"}]}),
        encoding="utf-8",
    )
    manifest = AssetManifest(tmp_path, bad_manifest)
    errors = list(manifest.verify())
    assert "sha256 不匹配" in errors[0]
    with pytest.raises(KeyError):
        manifest.resolve("asset://missing")
