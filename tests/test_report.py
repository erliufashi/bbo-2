"""报告输出测试。"""

import json
from pathlib import Path

from orchestrator.loader import load_service_definition
from orchestrator.report import ReportWriter
from orchestrator.runner import TestRunner


def test_report_writer_creates_files(tmp_path: Path) -> None:
    """应生成 JSON 与 JUnit 报告。"""

    definition = load_service_definition(Path("tests/data/service/service_definition.yaml"))
    results = TestRunner(definition).run()
    writer = ReportWriter(results)
    paths = writer.write_all(tmp_path)
    assert paths["json"].exists()
    assert paths["junit"].exists()
    data = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert data["summary"]["total"] == 2
