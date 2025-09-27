import json
from pathlib import Path

import pytest

from orchestrator.datasets import DatasetError, load_dataset


@pytest.fixture()
def dataset_manifest(tmp_path: Path) -> Path:
    (tmp_path / "demo.txt").write_text("demo", encoding="utf-8")
    (tmp_path / "prod.txt").write_text("prod", encoding="utf-8")
    manifest = tmp_path / "DATASET.yaml"
    manifest.write_text(
        json.dumps(
            [
                {"name": "demo", "file": "demo.txt", "profile": "test"},
                {"name": "prod-only", "file": "prod.txt", "profile": "prod"},
            ]
        ),
        encoding="utf-8",
    )
    return manifest


def test_load_dataset_filter(dataset_manifest: Path) -> None:
    profiles = load_dataset(dataset_manifest, "test")
    assert len(profiles) == 1
    assert profiles[0].name == "demo"


def test_load_dataset_missing_file(tmp_path: Path) -> None:
    manifest = tmp_path / "DATASET.yaml"
    manifest.write_text(json.dumps([{"file": "missing.txt", "profile": "test"}]), encoding="utf-8")
    with pytest.raises(DatasetError):
        load_dataset(manifest, "test")
