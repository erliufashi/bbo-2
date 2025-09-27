"""CLI 模块测试。"""
from __future__ import annotations

from pathlib import Path

from orchestrator.cli import main


def test_cli_test_command(tmp_path, capsys) -> None:  # type: ignore[override]
    source_dir = Path(__file__).parent / "data"
    service_dir = tmp_path / "service"
    service_dir.mkdir()
    for file in ["service_definition.yaml", "testsuite.json"]:
        (service_dir / file).write_text((source_dir / file).read_text(encoding="utf-8"), encoding="utf-8")
    exit_code = main(["test", str(service_dir / "service_definition.yaml"), "--output", str(tmp_path / "reports")])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "通过 2 条" in captured.out
    assert (tmp_path / "reports" / "results.json").exists()
