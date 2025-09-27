"""服务定义加载与校验模块（纯标准库实现）。"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RegisteredScorer:
    """注册的评分器描述。"""

    kind: str
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatorConfig:
    name: str
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCaseEntry:
    id: str
    request: Dict[str, Any]
    expected: Dict[str, Any]
    scorers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    aggregator: Optional[AggregatorConfig] = None


@dataclass
class TestSuiteConfig:
    suite_file: str
    registered_scorers: Dict[str, RegisteredScorer] = field(default_factory=dict)


@dataclass
class ServiceRuntime:
    image: Optional[str] = None
    start_cmd: Optional[List[str]] = None
    port: Optional[int] = None


@dataclass
class ServiceInfo:
    name: str
    language: Optional[str] = None
    runtime: Optional[ServiceRuntime] = None


@dataclass
class ServiceDefinition:
    version: str
    service: ServiceInfo
    tests: TestSuiteConfig
    assets: Optional[Dict[str, Any]] = None
    datasets: Optional[Dict[str, Any]] = None


@dataclass
class LoadedTestSuite:
    base_path: Path
    entries: List[TestCaseEntry]


def _ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _parse_service_info(data: Dict[str, Any]) -> ServiceInfo:
    _ensure("name" in data, "service.name 字段缺失")
    runtime_data = data.get("runtime")
    runtime = None
    if isinstance(runtime_data, dict):
        runtime = ServiceRuntime(
            image=runtime_data.get("image"),
            start_cmd=runtime_data.get("start_cmd"),
            port=runtime_data.get("port"),
        )
    return ServiceInfo(name=data["name"], language=data.get("language"), runtime=runtime)


def _parse_tests(data: Dict[str, Any]) -> TestSuiteConfig:
    _ensure("suite_file" in data, "tests.suite_file 字段缺失")
    registered: Dict[str, RegisteredScorer] = {}
    for name, item in (data.get("registered_scorers") or {}).items():
        _ensure("kind" in item, f"评分器 {name} 缺少 kind 字段")
        registered[name] = RegisteredScorer(kind=item["kind"], config=dict(item.get("config", {})))
    return TestSuiteConfig(suite_file=data["suite_file"], registered_scorers=registered)


def load_service_definition(path: str | Path) -> ServiceDefinition:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"未找到服务定义文件：{path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"服务定义文件 JSON 解析失败：{exc}") from exc

    _ensure(isinstance(data, dict), "服务定义文件必须是对象结构")
    _ensure("service" in data, "缺少 service 节点")
    _ensure("tests" in data, "缺少 tests 节点")

    service = _parse_service_info(data["service"])
    tests = _parse_tests(data["tests"])
    version = str(data.get("version", "1.0"))
    return ServiceDefinition(version=version, service=service, tests=tests, assets=data.get("assets"), datasets=data.get("datasets"))


def _parse_test_case(item: Dict[str, Any]) -> TestCaseEntry:
    for key in ("id", "request", "expected"):
        _ensure(key in item, f"测试用例缺少 {key} 字段")
    aggregator = None
    if "aggregator" in item and isinstance(item["aggregator"], dict):
        agg_dict = item["aggregator"]
        _ensure("name" in agg_dict, "聚合器配置缺少 name 字段")
        aggregator = AggregatorConfig(name=agg_dict["name"], config=dict(agg_dict.get("config", {})))
    return TestCaseEntry(
        id=item["id"],
        request=dict(item["request"]),
        expected=dict(item["expected"]),
        scorers={name: dict(cfg) for name, cfg in (item.get("scorers") or {}).items()},
        aggregator=aggregator,
    )


def load_test_suite(definition: ServiceDefinition, base_dir: str | Path) -> LoadedTestSuite:
    suite_path = Path(base_dir) / definition.tests.suite_file
    if not suite_path.exists():
        raise FileNotFoundError(f"测试用例文件不存在：{suite_path}")
    text = suite_path.read_text(encoding="utf-8")
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"测试用例文件 JSON 解析失败：{exc}") from exc
    _ensure(isinstance(raw, list), "测试用例文件必须是数组结构")
    entries = [_parse_test_case(item) for item in raw]
    return LoadedTestSuite(base_path=suite_path.parent, entries=entries)


__all__ = [
    "ServiceDefinition",
    "TestCaseEntry",
    "TestSuiteConfig",
    "RegisteredScorer",
    "load_service_definition",
    "load_test_suite",
    "LoadedTestSuite",
]
