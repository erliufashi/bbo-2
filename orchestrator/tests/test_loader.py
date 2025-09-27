from pathlib import Path

import pytest

from orchestrator.loader import ValidationError, load_service_definition, resolve_scorer
from orchestrator.scoring.exact import ExactMatchScorer


@pytest.fixture()
def service_definition_file(tmp_path: Path) -> Path:
    suite_path = tmp_path / "suite.json"
    suite_path.write_text("[]", encoding="utf-8")
    file = tmp_path / "service_definition.yaml"
    file.write_text(
        (
            '{"version": "1.0", "service": {"name": "demo"}, '
            '"tests": {"suite_file": "suite.json", "registered_scorers": '
            '{"exact_body": {"kind": "exact_match", "config": {"json_paths": ["$.value"]}}}}}'
        ),
        encoding="utf-8",
    )
    return file


def test_load_service_definition(service_definition_file: Path) -> None:
    definition = load_service_definition(service_definition_file)
    assert definition.version == "1.0"
    assert definition.tests.suite_file.name == "suite.json"
    scorer = resolve_scorer("exact_body", definition)
    assert isinstance(scorer, ExactMatchScorer)


def test_load_missing_fields(tmp_path: Path) -> None:
    file = tmp_path / "service_definition.yaml"
    file.write_text("{}", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_service_definition(file)
