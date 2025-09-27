"""运行期数据加载测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from orchestrator.datasets import DatasetLoader


def test_dataset_loader_success(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    manifest = tmp_path / "DATASET.yaml"
    manifest.write_text(
        "{\"profiles\": {\"test\": {\"path\": \"data\"}}}",
        encoding="utf-8",
    )
    loader = DatasetLoader(tmp_path)

    mount = loader.load(manifest, profile="test")

    assert mount.is_ready()
    assert mount.mounted_path == data_dir


def test_dataset_loader_missing_profile(tmp_path: Path) -> None:
    manifest = tmp_path / "DATASET.yaml"
    manifest.write_text("{\"profiles\": {}}", encoding="utf-8")
    loader = DatasetLoader(tmp_path)

    with pytest.raises(KeyError):
        loader.load(manifest, profile="prod")
