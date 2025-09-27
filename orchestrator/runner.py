"""测试运行器实现。"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict, Iterable, List, Optional, Protocol

from .loader import LoadedTestSuite, ServiceDefinition
from .scoring import ScoreResult, build_aggregator, build_scorer


class Transport(Protocol):
    def perform(self, request: Dict[str, Any]) -> Dict[str, Any]:
        ...


@dataclass
class HTTPTransport(Transport):
    base_url: str
    timeout: float = 5.0

    def perform(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method", "GET").upper()
        path = request.get("path", "/")
        url = self.base_url.rstrip("/") + path
        data = None
        headers = {}
        if "json" in request:
            data = json.dumps(request["json"]).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # pragma: no cover - 仅在真实 HTTP 时使用
                raw = resp.read()
                text = raw.decode("utf-8")
                try:
                    body = json.loads(text)
                except json.JSONDecodeError:
                    body = text
                return {"status": resp.getcode(), "body": body, "headers": dict(resp.headers)}
        except urllib.error.URLError as exc:
            raise RuntimeError(f"HTTP 请求失败: {exc}") from exc


@dataclass
class FunctionTransport(Transport):
    handler: Any

    def perform(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return self.handler(request)


@dataclass
class TestCaseResult:
    id: str
    scorer_results: Dict[str, ScoreResult]
    aggregate_result: ScoreResult
    request: Dict[str, Any]
    expected: Dict[str, Any]
    __test__ = False


@dataclass
class SuiteResult:
    service: str
    cases: List[TestCaseResult]

    @property
    def summary(self) -> Dict[str, int]:
        passed = sum(1 for case in self.cases if case.aggregate_result["pass_"])
        total = len(self.cases)
        return {"passed": passed, "failed": total - passed, "total": total}


def _build_default_transport(definition: ServiceDefinition) -> Transport:
    runtime = definition.service.runtime
    if runtime and runtime.start_cmd:
        module_name = None
        for part in runtime.start_cmd:
            if "." in part and not part.startswith("-"):
                module_name = part
        if module_name:
            module = import_module(module_name)
            if hasattr(module, "create_transport"):
                return getattr(module, "create_transport")()
            if hasattr(module, "handle_request"):
                return FunctionTransport(handler=getattr(module, "handle_request"))
    if runtime and runtime.port:
        return HTTPTransport(base_url=f"http://127.0.0.1:{runtime.port}")
    raise ValueError("无法推断服务的 Transport，请显式提供 start_cmd 或传入 transport")


class TestRunner:
    __test__ = False

    def __init__(self, definition: ServiceDefinition, suite: LoadedTestSuite, *, transport: Optional[Transport] = None):
        self.definition = definition
        self.suite = suite
        self.transport = transport or _build_default_transport(definition)

    def _build_scorers(self) -> Dict[str, Any]:
        registry = {}
        for name, scorer_def in self.definition.tests.registered_scorers.items():
            registry[name] = build_scorer(scorer_def.kind, scorer_def.config)
        return registry

    def run(self, selected_ids: Optional[Iterable[str]] = None) -> SuiteResult:
        registry = self._build_scorers()
        results: List[TestCaseResult] = []
        selected = set(selected_ids or [])
        for entry in self.suite.entries:
            if selected and entry.id not in selected:
                continue
            print(f"运行用例 {entry.id}")
            response = self.transport.perform(entry.request)
            scorer_results: Dict[str, ScoreResult] = {}
            for scorer_name, scorer_config in entry.scorers.items():
                if scorer_name not in registry:
                    raise KeyError(f"测试用例引用了未注册评分器：{scorer_name}")
                scorer = registry[scorer_name]
                expected_payload = None
                if isinstance(scorer_config, dict):
                    expected_payload = scorer_config.get("expected_override") or scorer_config.get("expected_text")
                if expected_payload is None:
                    expected_payload = entry.expected.get("body", entry.expected)
                scorer_results[scorer_name] = scorer.score(
                    expected=expected_payload,
                    actual=response.get("body"),
                    context={"response": response, "request": entry.request},
                )
            if entry.aggregator:
                aggregator = build_aggregator(entry.aggregator.name, entry.aggregator.config)
            else:
                weights = {name: 1.0 / max(len(entry.scorers), 1) for name in entry.scorers}
                aggregator = build_aggregator("weighted_sum", {"weights": weights, "pass_threshold": 1.0})
            aggregate_result = aggregator.aggregate(scorer_results)
            results.append(
                TestCaseResult(
                    id=entry.id,
                    scorer_results=scorer_results,
                    aggregate_result=aggregate_result,
                    request=entry.request,
                    expected=entry.expected,
                )
            )
        return SuiteResult(service=self.definition.service.name, cases=results)


__all__ = ["TestRunner", "SuiteResult", "TestCaseResult", "HTTPTransport", "FunctionTransport"]
