"""运行器模块测试。"""
from __future__ import annotations

from pathlib import Path

import pytest

from orchestrator.loader import load_service_definition
from orchestrator.runner import TestRunner


@pytest.fixture()
def sample_definition(tmp_path: Path) -> Path:
    source_dir = Path(__file__).parent / "data"
    target_dir = tmp_path / "service"
    target_dir.mkdir()
    for file in ["service_definition.yaml", "testsuite.json"]:
        (target_dir / file).write_text((source_dir / file).read_text(encoding="utf-8"), encoding="utf-8")
    return target_dir / "service_definition.yaml"


def test_runner_end_to_end(sample_definition: Path, tmp_path: Path) -> None:
    definition = load_service_definition(sample_definition)
    runner = TestRunner(definition)
    summary = runner.run()
    assert summary.passed == 2
    assert summary.failed == 0
