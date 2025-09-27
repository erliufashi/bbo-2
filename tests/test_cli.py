"""CLI 测试，保证关键命令可执行。"""
from __future__ import annotations

from pathlib import Path

import shutil

from orchestrator import cli


def _prepare_service(tmp_path: Path) -> None:
    shutil.copytree(Path("services"), tmp_path / "services")


def test_cli_test_command(tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_service(tmp_path)
    monkeypatch.chdir(tmp_path)
    cli.main(["test", "services/order_service/service_definition.yaml"])
    report_dir = Path(".bb/reports")
    assert (report_dir / "results.json").exists()
    assert (report_dir / "junit.xml").exists()
    captured = capsys.readouterr()
    assert "报告已生成" in captured.out


def test_cli_pack_command(tmp_path: Path, monkeypatch) -> None:
    _prepare_service(tmp_path)
    monkeypatch.chdir(tmp_path)
    output = Path("pkg.tar")
    cli.main(["pack", "services/order_service/service_definition.yaml", "--output", str(output)])
    assert output.exists()


def test_cli_release_command(capsys) -> None:
    cli.main(["release", "v1.0.0"])
    assert "v1.0.0" in capsys.readouterr().out
