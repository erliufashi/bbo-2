"""数据集加载测试。"""

import pytest

from orchestrator.datasets import DatasetError, DatasetLoader


def test_dataset_loader_success() -> None:
    """应能正确加载测试配置。"""

    loader = DatasetLoader.from_file("tests/data/service/data/runtime/DATASET.yaml")
    profile = loader.get("test")
    assert profile.files[0].exists()


def test_dataset_loader_missing_profile(tmp_path) -> None:
    """缺失文件时需要抛出异常。"""

    dataset = tmp_path / "DATASET.yaml"
    dataset.write_text(
        "profiles:\n  demo:\n    files:\n      - missing.json\n",
        encoding="utf-8",
    )
    with pytest.raises(DatasetError):
        DatasetLoader.from_file(dataset)
