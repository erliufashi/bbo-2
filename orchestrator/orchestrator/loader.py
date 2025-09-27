"""`service_definition.yaml` 加载与校验模块。"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping

from ._yaml import safe_load

from .scoring.base import RegisteredScorer, ScoringError


class ValidationError(RuntimeError):
    """声明文件结构异常时抛出的错误。"""


@dataclass(slots=True)
class TestsConfig:
    """测试相关配置。"""

    suite_file: Path
    registered_scorers: Mapping[str, RegisteredScorer] = field(default_factory=dict)


@dataclass(slots=True)
class ServiceDefinition:
    """服务定义的聚合对象。"""

    version: str
    service: Dict[str, Any]
    tests: TestsConfig
    raw: Dict[str, Any]


REQUIRED_TOP_LEVEL = {"version", "service", "tests"}


def _parse_registered_scorers(data: Mapping[str, Any]) -> Dict[str, RegisteredScorer]:
    result: Dict[str, RegisteredScorer] = {}
    for name, payload in data.items():
        if not isinstance(payload, Mapping):
            raise ValidationError(f"registered_scorers.{name} 必须是映射")
        try:
            kind = str(payload["kind"])
            config = dict(payload.get("config", {}))
        except KeyError as exc:
            raise ValidationError(f"评分器 {name} 缺少字段 {exc.args[0]}") from exc
        result[name] = RegisteredScorer(name=name, kind=kind, config=config)
    return result


def load_service_definition(path: str | Path) -> ServiceDefinition:
    """读取并校验 `service_definition.yaml`。"""

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"找不到 service_definition 文件: {path}")
    with path.open("r", encoding="utf-8") as fh:
        raw_data = safe_load(fh.read()) or {}
    if not isinstance(raw_data, dict):
        raise ValidationError("service_definition.yaml 顶层必须是字典")
    missing = REQUIRED_TOP_LEVEL - raw_data.keys()
    if missing:
        raise ValidationError(f"缺少必要字段: {', '.join(sorted(missing))}")
    tests = raw_data.get("tests", {})
    if not isinstance(tests, Mapping):
        raise ValidationError("tests 必须为字典")
    suite_file = Path(path.parent, tests.get("suite_file", "")).resolve()
    if not suite_file.name:
        raise ValidationError("tests.suite_file 不能为空")
    registered = tests.get("registered_scorers", {})
    if not isinstance(registered, Mapping):
        raise ValidationError("tests.registered_scorers 必须为字典")
    tests_config = TestsConfig(
        suite_file=suite_file,
        registered_scorers=_parse_registered_scorers(registered),
    )
    version = str(raw_data["version"])
    service = dict(raw_data.get("service", {}))
    return ServiceDefinition(version=version, service=service, tests=tests_config, raw=raw_data)


def resolve_scorer(name: str, definition: ServiceDefinition):
    """根据名称实例化评分器。"""

    scorer = definition.tests.registered_scorers.get(name)
    if not scorer:
        raise ScoringError(f"评分器 {name} 未注册")
    if scorer.kind == "exact_match":
        from .scoring.exact import ExactMatchScorer

        return ExactMatchScorer(scorer.config)
    if scorer.kind == "custom_script":
        from .scoring.custom import CustomScriptScorer

        return CustomScriptScorer(scorer.config)
    if scorer.kind == "llm_scorer":
        from .scoring.llm import SimpleLLMScorer

        return SimpleLLMScorer(scorer.config)
    raise ScoringError(f"未知的评分器类型: {scorer.kind}")


__all__ = [
    "ServiceDefinition",
    "TestsConfig",
    "ValidationError",
    "load_service_definition",
    "resolve_scorer",
]
