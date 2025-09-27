"""数据集装载测试。"""
from __future__ import annotations

from pathlib import Path

import pytest

from orchestrator.datasets import DatasetLoader


def test_dataset_loader(tmp_path: Path) -> None:
    loader = DatasetLoader(Path("services/order_service/data/runtime/DATASET.yaml"))
    assert "test" in loader.profiles()
    mount = loader.load("test")
    assert mount.mounted_path.exists()
    assert any(file.name == "sample-data.json" for file in mount.files)


def test_dataset_loader_missing_profile(tmp_path: Path) -> None:
    loader = DatasetLoader(Path("services/order_service/data/runtime/DATASET.yaml"))
    with pytest.raises(ValueError):
        loader.load("prod")
