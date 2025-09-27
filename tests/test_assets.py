"""资产解析逻辑测试。"""

from pathlib import Path

import pytest

from orchestrator.assets import AssetError, AssetResolver, load_manifest


def test_resolve_asset_success() -> None:
    """应能正确解析 asset:// URI 并校验哈希。"""

    manifest = load_manifest("tests/data/service/tests/assets/manifest.yaml")
    resolver = AssetResolver(manifest)
    path = resolver.resolve("asset://sample")
    assert path.read_text(encoding="utf-8").strip() == "示例资产文件"


def test_resolve_asset_checksum_failed(tmp_path: Path) -> None:
    """校验失败时需要抛出异常。"""

    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        """
assets:
  broken:
    path: sample.txt
    sha256: deadbeef
        """.strip(),
        encoding="utf-8",
    )
    sample_path = tmp_path / "sample.txt"
    sample_path.write_text("demo", encoding="utf-8")
    manifest = load_manifest(manifest_path)
    resolver = AssetResolver(manifest)
    with pytest.raises(AssetError):
        resolver.resolve("asset://broken")
