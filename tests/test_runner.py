"""测试执行器相关测试。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestrator.runner import TestSuiteRunner


def _executor(request):
    return request.get("mock_response")


def test_runner_success(tmp_path: Path) -> None:
    suite = [
        {
            "id": "case-1",
            "request": {"mock_response": {"status": 201, "body": {"important": "x"}}},
            "expected": {"status": 201, "body": {"important": "x"}},
            "scorers": ["exact", "custom"],
            "aggregator": {
                "kind": "weighted_sum",
                "weights": {"exact": 0.7, "custom": 0.3},
                "pass_threshold": 0.9,
            },
        }
    ]
    suite_file = tmp_path / "cases.json"
    suite_file.write_text(json.dumps(suite), encoding="utf-8")

    scorer_configs = {
        "exact": {"kind": "exact_match", "config": {"json_paths": ["$.status"]}},
        "custom": {"kind": "custom_script", "config": {"entrypoint": "tests.sample_scorer:score"}},
    }

    runner = TestSuiteRunner(scorer_configs=scorer_configs, request_executor=_executor)
    result = runner.run(suite_file)

    assert result.summary["passed"] == 1
    assert result.results[0].passed


def test_runner_unknown_scorer(tmp_path: Path) -> None:
    suite = [
        {
            "id": "case-1",
            "request": {"mock_response": {}},
            "expected": {},
            "scorers": ["missing"],
        }
    ]
    suite_file = tmp_path / "cases.json"
    suite_file.write_text(json.dumps(suite), encoding="utf-8")

    runner = TestSuiteRunner(scorer_configs={}, request_executor=_executor)

    with pytest.raises(KeyError):
        runner.run(suite_file)
