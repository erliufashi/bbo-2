"""命令行接口测试。"""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from orchestrator.cli import cli


def _prepare_service(tmp_path: Path) -> Path:
    service_dir = tmp_path / "service"
    tests_dir = service_dir / "tests"
    tests_dir.mkdir(parents=True)
    (service_dir / "service_definition.yaml").write_text(
        """
{
  "version": "1.0",
  "service": {"name": "demo"},
  "tests": {
    "suite_file": "tests/test_cases.json",
    "registered_scorers": {
      "exact_body": {
        "kind": "exact_match",
        "config": {"json_paths": ["$.status"]}
      }
    }
  }
}
""",
        encoding="utf-8",
    )
    cases = [
        {
            "id": "ok",
            "request": {"mock_response": {"status": 200}},
            "expected": {"status": 200},
            "scorers": ["exact_body"],
        }
    ]
    (tests_dir / "test_cases.json").write_text(json.dumps(cases), encoding="utf-8")
    return service_dir


def test_cli_test_command(tmp_path: Path) -> None:
    runner = CliRunner()
    service_dir = _prepare_service(tmp_path)
    result = runner.invoke(cli, ["test", "--service-dir", str(service_dir), "--reports", str(tmp_path / "out")])
    assert result.exit_code == 0
    assert "通过 1 个" in result.output


def test_cli_other_commands(tmp_path: Path) -> None:
    runner = CliRunner()
    service_dir = _prepare_service(tmp_path)
    for command in ["up", "pack", "release"]:
        result = runner.invoke(cli, [command, "--service-dir", str(service_dir)])
        assert result.exit_code == 0
        assert str(service_dir) in result.output
