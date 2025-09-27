**可实施产品级设计规范（Design Spec）**

> 术语约定
>
> * **服务包（Service Package）**：单个微服务的源代码与元数据集合。
> * **开发编排器（Development Orchestrator，下称 Orchestrator）**：外部 CLI，负责拉起容器、注入数据资产、运行与评分测试、汇总报告。
> * **`service_definition.yaml`**：服务包内的唯一“身份证”，声明 API、依赖、测试与评分策略、资产等。
> * **资产（Asset）**：测试或运行所需的非结构化文件，如图片/音频/PDF/表格等。
> * **业务数据（Runtime Dataset）**：服务运行必需的数据，如 RAG 知识库。与**测试数据**严格分离。

---

## 议题一：可插拔、可扩展的测试评估引擎设计

### 1.1 在 `service_definition.yaml` 中支持多模式评分（exact/custom/llm）

**核心思路**

* 将“评分”抽象为**可组合的打分器（Scorer）**与**聚合策略（Aggregator）**。
* 每个测试用例可以声明多个 `scorers`，并用 `aggregator` 将它们合成为最终通过/不通过或数值分。
* Orchestrator 通过统一的**打分器接口**加载 `exact_match`、`custom_script`、`llm_scorer` 等插件。

**目录建议（服务包局部）**

```
service/
├─ service_definition.yaml
├─ api/
│  └─ openapi.yaml
├─ app/                     # 业务代码（示例为 Python/FastAPI）
├─ tests/
│  ├─ test_cases.json       # 测试用例声明（或 .yaml）
│  ├─ scorers/              # 自定义评分脚本（仅 custom_script 用）
│  │  ├─ order_rules.py
│  │  └─ requirements.txt   # 自定义评分脚本的独立依赖（可选）
│  └─ assets/               # 测试资产（见议题二）
└─ Dockerfile
```

**统一打分器接口（伪代码）**

```python
# orchestrator/scoring/base.py
from typing import Any, Dict, TypedDict

class ScoreResult(TypedDict):
    score: float          # 0.0~1.0
    pass_: bool
    reasoning: str

class Scorer:
    def __init__(self, config: Dict[str, Any]): ...
    def score(self, *, expected: Any, actual: Any, context: Dict[str, Any]) -> ScoreResult:
        raise NotImplementedError
```

**`service_definition.yaml`（节选：评分部分）**

```yaml
version: "1.0"
service:
  name: order-service
  language: python
tests:
  suite_file: tests/test_cases.json

  # 可注册复用的评分器
  registered_scorers:
    exact_body:
      kind: exact_match
      config:
        json_paths:
          - "$.status"
          - "$.body.order_id"
    business_rules:
      kind: custom_script
      config:
        entrypoint: "tests/scorers/order_rules.py:score"  # module:function
        python:
          version: "3.11"
          requirements: "tests/scorers/requirements.txt"
        sandbox:
          network: false
          filesystem_readonly: true
          cpu_limit: "1"
          mem_limit: "512m"
    semantic_quality:
      kind: llm_scorer
      config:
        provider: "openai"             # 抽象提供方
        model: "gpt-4-class"           # 自由字符串，具体路由由 Orchestrator 适配器负责
        prompt_template: "tests/prompts/quality_prompt.md"
        output_schema:
          type: object
          required: [score, reasoning]
          properties:
            score: {type: number, minimum: 0, maximum: 1}
            reasoning: {type: string, maxLength: 2000}
        pass_threshold: 0.85
        temperature: 0.2
        max_tokens: 512
        retry:
          max_attempts: 2
          backoff: "exponential"
        cost_guard:
          max_total_tokens: 50000
          hard_fail: true
```

**在单个测试用例中组合评分器（`tests/test_cases.json` 片段）**

```json
[
  {
    "id": "create-order-success",
    "request": {
      "method": "POST",
      "path": "/orders",
      "json": {"user_id": "u-001", "items": [{"sku": "A1", "qty": 2}]}
    },
    "expected": {
      "status": 201,
      "json": {"ok": true, "order_id": "<any-non-empty>"}
    },
    "scoring": {
      "scorers": [
        {"use": "exact_body"},
        {"use": "business_rules"},
        {"use": "semantic_quality", "weight": 0.4}
      ],
      "aggregator": {
        "kind": "weighted_sum",
        "fail_fast_on": ["exact_body", "business_rules"],
        "weights": {"exact_body": 0.3, "business_rules": 0.3, "semantic_quality": 0.4},
        "pass_threshold": 0.9
      }
    }
  }
]
```

> 说明
>
> * `fail_fast_on`：任一前置硬性校验失败即整体失败（如 schema/业务规则）。
> * `weighted_sum`：将可量化评分合成为总分。`exact_match`/`custom_script` 也可返回 0/1 分。

---

### 1.2 `llm_scorer` 需要哪些参数（完整 YAML 示例）

````yaml
tests:
  registered_scorers:
    creative_write_grade:
      kind: llm_scorer
      config:
        provider: "openai"         # or "anthropic","azure_openai",...
        model: "gpt-4o-mini"       # 由 Orchestrator 的 ModelRouter 解析
        # 评分标准：系统提示 + 评分提示
        system: |
          You are a meticulous grader. Score only on the given rubric.
        prompt_template: |
          ## Task
          Evaluate the ASSISTANT_RESPONSE against the REQUIREMENTS.

          ## Requirements
          - Style: concise, friendly
          - Must include: {must_include}
          - Avoid: {avoid}

          ## Output Format (JSON):
          {"score": <0..1>, "reasoning": "<short explanation>"}

          ## Inputs
          ASSISTANT_RESPONSE:
          ```text
          {actual}
          ```
          GOLD_REFERENCE (optional):
          ```text
          {expected}
          ```
        variables:
          must_include: ["order id", "shipping date"]
          avoid: ["marketing fluff"]
        output_schema:
          type: object
          required: [score, reasoning]
          properties:
            score: {type: number, minimum: 0, maximum: 1}
            reasoning: {type: string}
        pass_threshold: 0.8
        temperature: 0.0
        top_p: 1.0
        max_tokens: 256
        json_mode: true               # 要求 LLM 严格输出 JSON
        stop: ["\n\nEND"]
        seed: 1234                    # 尽量稳定
        retry:
          max_attempts: 3
          backoff: "exponential"
          jitter_ms: 50
        redteam:
          allow_model_refusal: true   # 确保不因安全拒答而导致崩溃
        cost_guard:
          max_total_tokens: 200000
          hard_fail: false
        telemetry_tags:
          project: "black-box"
          service: "order-service"
````

> 实施要点
>
> * **ModelRouter**：Orchestrator 内部根据 `provider/model` 将调用路由到具体 SDK；统一**重试/日志/成本度量**与**输出 JSON 校验（jsonschema）**。
> * **Determinism**：通过 `seed`、`temperature=0`、`json_mode` 与严格 schema 验证降低抖动。
> * **治理**：`cost_guard` 限制 token；`telemetry_tags` 便于观测。

---

## 议题二：测试数据资产（Data Assets）标准化

### 2.1 资产目录组织

**建议结构（服务包内部）**

```
service/
├─ tests/
│  ├─ assets/                    # 仅测试用途
│  │  ├─ images/
│  │  ├─ audio/
│  │  ├─ pdf/
│  │  ├─ tables/
│  │  └─ manifest.yaml          # 资产清单（ID ↔ 路径/哈希/许可证）
│  └─ test_cases.json
├─ data/
│  ├─ runtime/                   # 仅运行期业务数据（RAG 等）
│  │  ├─ kb/                     # e.g., 原文档
│  │  ├─ index/                  # e.g., 向量索引/缓存
│  │  └─ DATASET.yaml            # 数据集清单（版本、来源、装载脚本）
│  └─ scripts/
│     └─ load_kb.py             # 业务数据装载器
```

**资产清单（`tests/assets/manifest.yaml`）**

```yaml
version: "1"
assets:
  - id: "img.cat.001"
    path: "images/cat-001.jpg"
    sha256: "af3e...e91"
    mime: "image/jpeg"
    license: "CC-BY-4.0"
  - id: "doc.invoice.sampleA"
    path: "pdf/invoice-A.pdf"
    sha256: "b71c...a20"
    mime: "application/pdf"
    license: "internal"
mount:
  container_path: "/__assets__"       # Orchestrator 统一挂载点（只读）
```

### 2.2 资产在用例中如何“可移植地”引用

**推荐使用**统一的 URI 方案：`asset://<asset_id>`

* 避免在用例里写相对路径（易随目录变化而失效）。
* Orchestrator 解析 `asset://` → 查 `manifest.yaml` → 校验 `sha256` → 挂载容器内只读路径 `/__assets__/...` → 将用例中出现的 `asset://img.cat.001` 动态替换为容器内路径。

**用例引用示例（节选）**

```json
{
  "id": "upload-invoice",
  "request": {
    "method": "POST",
    "path": "/upload",
    "files": [
      {"field": "file", "asset": "asset://doc.invoice.sampleA"}
    ]
  },
  "expected": {"status": 200},
  "scoring": {"scorers": [{"use": "exact_body"}], "aggregator": {"kind": "all"}}
}
```

**跨环境鲁棒性**

* 本地与 CI/CD 一致：永远通过 `asset://` 与 `manifest.yaml` 解析；不依赖宿主绝对路径。
* 大文件：建议用 Git‑LFS（或对象存储）+ `manifest.yaml` 中 `remote` 字段与 `pull_policy`（如 `if-not-present`），由 Orchestrator 预拉取并校验哈希。
* 许可证字段保证合规可追踪。

### 2.3 业务数据（runtime）与测试数据分离

**DATASET 清单（`data/runtime/DATASET.yaml`）**

```yaml
dataset:
  id: "kb.orders.v2025_09_01"
  version: "2025.09.01"
  source:
    type: "git|s3|gcs|http"
    uri: "s3://mybucket/kb/orders/2025-09-01/"
  integrity:
    sha256_manifest: "e1d2...9aa"
  loader:
    script: "data/scripts/load_kb.py"
    args:
      target_dir: "data/runtime/index"
  license: "internal"
  notes: "Used by /search and /summary endpoints"
mount:
  container_path: "/__runtime__"
```

**实践要点**

* 业务数据**不进入**测试资产目录；二者生命周期不同。
* Orchestrator 在 `mode=test` 时，可通过 `datasets` 的 `profile=test` 装载“瘦身版”数据，保证测试快速稳定。
* RAG 类服务：将**原文档**和**索引**放在 `data/runtime/`，索引由 `loader` 再现，避免把二进制索引直接纳入 Git。

---

## 议题三：多微服务的代码仓库策略

### 3.1 Monorepo vs Multi‑repo（结合“黑盒开发”）

**Monorepo 优点**

* 单一事实来源：统一的 `service_definition.yaml` 规范、统一脚手架与 Lint/格式化工具、单点升级更容易。
* Orchestrator 可以**一次性**构建依赖图并做**跨服务矩阵测试**（真实依赖 vs mock）。
* 共享库/契约/测试资产更易复用；原子化提交可同时修改多服务与其契约。

**Monorepo 缺点**

* CI 规模与耦合上升，权限与发布粒度需要额外治理（路径级触发、缓存与分治）。
* 大型仓库会影响克隆/索引速度（可用稀疏检出、子树划分缓解）。

**Multi‑repo 优点**

* 团队边界清晰，权限/发布独立，仓库轻量。
* 外部供应商/子团队可独立生命周期与合规。

**Multi‑repo 缺点**

* 跨仓库契约演进与测试矩阵复杂（需要独立的“契约仓库”或制品库）。
* 黑盒自动开发 Agent 难以做“全局修改 + 一次性回归”。

**建议（分阶段策略）**

* **0→1 阶段**：**Monorepo‑first**（速度和一致性优先），结合路径感知 CI 仅构建受影响服务。
* **规模化后**：引入**制品仓库**（内网 PyPI/NPM/Docker Registry）与**契约/镜像发布流程**；必要时将稳定服务拆为独立仓库，但保留 Monorepo 作为“集成母仓”（通过 Git Subtree / 自动同步脚本维持镜像）。

**Monorepo 顶层结构建议**

```
black-box/
├─ orchestrator/           # Orchestrator CLI/SDK
├─ libs/                   # 共享库（见 3.2）
│  ├─ py/common-logging/
│  ├─ py/auth-sdk/
│  └─ ts/http-client/
├─ services/
│  ├─ user-service/
│  ├─ order-service/
│  └─ billing-service/
├─ contracts/              # OpenAPI / Pact / JSON Schema 等
├─ .github/workflows/      # 或其他 CI 系统配置
└─ docs/
```

### 3.2 共享代码与依赖管理

**最佳实践**

* 建立内部共享库（语言分包），遵循 **SemVer**。
* 通过**内部制品仓库**发布（如私有 PyPI/devpi、npm 私库、GHCR）。
* 服务依赖固定**次要版本上限**（如 `^1.4`），并在 CI 中有**定期依赖升级任务**与**跨服务回归测试**。

**Python 共享库发布流程（示例）**

```
libs/py/common-logging/
├─ pyproject.toml
├─ common_logging/
│  ├─ __init__.py
│  └─ logger.py
└─ tests/
```

`pyproject.toml`（节选）

```toml
[project]
name = "common-logging"
version = "1.4.0"
dependencies = ["structlog>=24.1,<25"]

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
```

**服务引用**

```toml
# services/order-service/pyproject.toml
[project]
dependencies = [
  "common-logging>=1.4,<2.0",
  "fastapi>=0.111,<0.112"
]

[[tool.pdm.source]]
name = "internal"
url = "https://pypi.internal.example/simple"
verify_ssl = true
```

---

## 议题四：服务间依赖声明与测试隔离

### 4.1 在 `service_definition.yaml` 显式声明依赖

```yaml
dependencies:
  - id: "user-service"
    contract:
      type: "openapi"                          # 也可 "pact"
      file: "../user-service/api/openapi.yaml" # 或 contracts/user-service.yaml
      version: ">=1.3,<2.0"
    endpoints:
      base: "http://user-service:8080"
      health: "/healthz"
    runtime:
      default_mode: "mock"                     # "mock" | "real"
      mock:
        kind: "openapi_stub"                   # Orchestrator 内置（Prism/WireMock 类）
        fixtures_dir: "tests/fixtures/user-service"
      real:
        image: "ghcr.io/org/user-service:1.4.2"
        env:
          DATABASE_URL: "postgres://user:pass@db:5432/user"
        healthcheck:
          method: "GET"
          path: "/healthz"
          timeout_s: 10
        datasets:
          - id: "seed.users.minimal"
            seeder: "../user-service/scripts/seed_test_data.py"
```

### 4.2 测试时如何处理依赖：真实实例 vs Mock

**a. 自动拉起真实实例（Real）**

* **优点**：高保真，发现跨服务集成/数据耦合问题。
* **缺点**：慢且脆弱，需要数据库/队列/缓存等配套，数据播种复杂。

**b. 使用 Mock Server**

* **优点**：快、确定性强、易并行。消费者驱动契约（Pact/OpenAPI 示例+fixture）可避免漂移。
* **缺点**：可能遗漏真实运行中的边界条件/性能问题。

**建议的分层测试策略（内置于 Orchestrator）**

* **层 1：单元 + 黑盒功能** → **Mock（默认）**，快、稳定（开发内环/PR 校验）。
* **层 2：契约测试** → 与依赖服务的**契约验证**（mock 对照真实契约）。
* **层 3：最小化集成（Smoke‑Integration）** → **Real**，仅关键路径与健康检查。
* **层 4：全链路回归（Nightly/Release）** → **Real** + 近似真实数据集（瘦身版）。

**测试矩阵在 `service_definition.yaml` 中配置**

```yaml
test_matrix:
  - name: "fast-mock"
    description: "PR 快速校验"
    dependency_mode: "mock"
    include_tags: ["smoke", "core"]
  - name: "contract-verify"
    dependency_mode: "mock"
    run_contract_tests: true
  - name: "real-smoke"
    dependency_mode: "real"
    include_tags: ["smoke"]
  - name: "real-regression"
    dependency_mode: "real"
    include_tags: ["regression"]
    dataset_profile: "test"
```

---

# 产品级设计规范（完整）

以下规范汇总上文，并扩展 Orchestrator 的模块职责、配置与测试约定。

## A. 顶层目录与生成物

```
black-box/
├─ orchestrator/
│  ├─ cli.py
│  ├─ core/
│  │  ├─ loader.py            # 读 service_definition.yaml & 用例
│  │  ├─ assets.py            # asset:// 解析与挂载
│  │  ├─ datasets.py          # runtime 数据装载
│  │  ├─ sandbox.py           # 容器/隔离执行
│  │  ├─ scoring/
│  │  │  ├─ base.py
│  │  │  ├─ exact.py
│  │  │  ├─ custom.py
│  │  │  └─ llm.py
│  │  ├─ deps.py              # 依赖图 & mock/real 管理
│  │  ├─ runner.py            # 测试执行引擎
│  │  ├─ aggregator.py
│  │  └─ report.py            # JUnit/HTML/JSON 报告
│  └─ plugins/                # 可选扩展
├─ libs/ ...
├─ services/
│  ├─ user-service/ ...
│  ├─ order-service/ ...
│  └─ billing-service/ ...
└─ contracts/ ...
```

**编译产物与报告**

```
.orchestrator/
├─ runs/<timestamp>/
│  ├─ matrix.json            # 实际执行矩阵
│  ├─ results.json           # 每用例评分结果（含原始 reasoning）
│  ├─ junit.xml              # 供 CI 可视化
│  └─ report.html            # 人类可读报告
└─ cache/
   ├─ assets/                # 校验后的本地缓存
   └─ datasets/              # 运行期数据缓存（按版本号）
```

## B. `service_definition.yaml` 的 JSON Schema（节选）

> 目的：在 Orchestrator 入口处做**强校验**，避免“配置即代码”的脆弱性。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ServiceDefinition",
  "type": "object",
  "required": ["version", "service", "tests"],
  "properties": {
    "version": {"type": "string"},
    "service": {
      "type": "object",
      "required": ["name", "language"],
      "properties": {
        "name": {"type": "string"},
        "language": {"type": "string"},
        "runtime": {
          "type": "object",
          "properties": {
            "image": {"type": "string"},
            "start_cmd": {"type": "array", "items": {"type": "string"}},
            "port": {"type": "integer"}
          }
        }
      }
    },
    "tests": {
      "type": "object",
      "required": ["suite_file"],
      "properties": {
        "suite_file": {"type": "string"},
        "registered_scorers": {"type": "object"},
        "default_aggregator": {"type": "object"}
      }
    },
    "dependencies": {"type": "array"},
    "test_matrix": {"type": "array"},
    "assets": {"type": "object"},
    "datasets": {"type": "object"}
  }
}
```

## C. Orchestrator CLI 规范

**命令面（示例）**

```
bb init               # 生成服务脚手架
bb up [service]       # 本地拉起目标服务（及其依赖）
bb test [service]     # 运行 test_matrix
  --matrix fast-mock
  --filter id=upload-*
  --report html,json
bb score regrade      # 对历史 actual/expected 重新评分（更换 LLM 规则）
bb pack [service]     # 打包镜像/制品
bb release [service]  # 生成版本与契约快照
```

**执行流程（伪代码）**

```python
def run_tests(service, matrix_name):
    cfg = load_service_definition(service)
    matrix = select_matrix(cfg, matrix_name)
    deps = build_dependency_graph(cfg, mode=matrix.dependency_mode)
    with provision(deps):  # mock or real
        with mount_assets(cfg.tests.assets_manifest):
            with mount_datasets(cfg.datasets, profile=matrix.dataset_profile):
                cases = load_cases(cfg.tests.suite_file, filter=matrix.include_tags)
                results = []
                for case in cases:
                    actual = invoke_http(service, case.request)
                    result = score_case(case, actual, cfg.tests.registered_scorers)
                    results.append(result)
    write_reports(results)
```

## D. 打分器实现要点与示例

**ExactMatch（字段级匹配 + JSONPath）**

```yaml
tests:
  registered_scorers:
    exact_body:
      kind: exact_match
      config:
        json_paths:
          - "$.status"
          - "$.json.ok"
        allow_placeholders:
          "<any-non-empty>": "non_empty"
          "<uuid>": "uuid_v4"
```

**CustomScript（受限沙箱执行）**

* 以**独立 Python 环境**执行，避免污染被测服务依赖。
* 限制网络和只读文件系统，传入 `expected/actual/context` 三元。
* 返回 `{"score": float, "pass_": bool, "reasoning": str}`。

`tests/scorers/order_rules.py`

```python
def score(expected, actual, context):
    # 业务校验示例：金额=∑(单价*数量)，订单状态机合法
    body = actual["json"]
    items = body["items"]
    calc_total = sum(i["price"] * i["qty"] for i in items)
    ok = abs(calc_total - body["amount"]) < 0.01 and body["status"] in {"CREATED","PAID"}
    return {
        "score": 1.0 if ok else 0.0,
        "pass_": ok,
        "reasoning": "amount & status verified"
    }
```

**LLMScorer（见 1.2）**

* Orchestrator 中 `llm.py` 负责：模板渲染 → 调用模型 → JSON 校验 → 归一化分数。
* 失败回退（如输出非 JSON）→ **重试**；仍失败则**给出 0 分 + 失败原因**。

## E. 合规与安全

* **资产与数据许可证**字段必填；报告中呈现使用清单。
* **脱敏**：测试报告中自动遮盖 `pii` 字段（在 `service_definition.yaml` 中可配置 JSONPath）。
* **网络隔离**：被测服务仅暴露容器网络；`custom_script` 默认无网络。
* **审计**：保存完整评分 `reasoning` 与 LLM 提示（可选脱敏）。

## F. CI/CD 流水线蓝图（以 GitHub Actions 为例）

```yaml
name: ci
on:
  pull_request:
    paths: ["services/**", "libs/**", "orchestrator/**"]
jobs:
  impact:
    runs-on: ubuntu-latest
    outputs:
      services: ${{ steps.detect.outputs.services }}
    steps:
      - uses: actions/checkout@v4
      - name: Detect impacted services
        run: python orchestrator/ci/detect_changed_services.py > changed.txt
        id: detect
  test:
    needs: impact
    strategy:
      matrix:
        service: ${{ fromJson(needs.impact.outputs.services) }}
        profile: [fast-mock, contract-verify]
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e orchestrator
      - run: bb test services/${{ matrix.service }} --matrix ${{ matrix.profile }} --report junit,json
      - uses: actions/upload-artifact@v4
        with:
          name: reports-${{ matrix.service }}-${{ matrix.profile }}
          path: .orchestrator/runs/**/*
```

---

# 示例服务包（可直接落地）

```
services/order-service/
├─ service_definition.yaml
├─ api/openapi.yaml
├─ app/main.py                       # FastAPI 示例
├─ tests/
│  ├─ test_cases.json
│  ├─ assets/
│  │  ├─ manifest.yaml
│  │  └─ pdf/invoice-A.pdf
│  ├─ fixtures/user-service/         # 供 mock server 使用的响应样例
│  └─ scorers/order_rules.py
├─ data/
│  ├─ runtime/kb/...
│  ├─ runtime/index/.gitignore
│  └─ scripts/load_kb.py
└─ Dockerfile
```

`app/main.py`（极简）

```python
from fastapi import FastAPI, UploadFile
import uuid

app = FastAPI()

@app.post("/orders")
def create_order(payload: dict):
    return {"ok": True, "order_id": str(uuid.uuid4()), "items": payload.get("items", []), "amount": 19.98, "status": "CREATED"}

@app.post("/upload")
async def upload(file: UploadFile):
    assert file.filename.endswith(".pdf")
    return {"ok": True, "name": file.filename}
```

---

# 单元测试与契约测试蓝图（可交付）

> 使用 **pytest** + **pytest‑httpx/requests‑mock** + **jsonschema** + **testcontainers**（如需真实依赖）

## 1. Orchestrator 级单测

**1.1 配置加载**

```python
# orchestrator/tests/test_loader.py
def test_service_definition_schema_validates():
    cfg = load_yaml("services/order-service/service_definition.yaml")
    assert validate_against_schema(cfg) is True
```

**1.2 资产解析**

```python
# orchestrator/tests/test_assets.py
def test_asset_uri_resolution(tmp_path):
    manifest = load_yaml("services/order-service/tests/assets/manifest.yaml")
    path = resolve_asset("asset://doc.invoice.sampleA", manifest, cache_dir=tmp_path)
    assert path.exists()
    assert sha256(path) == manifest["assets"][1]["sha256"]
```

**1.3 exact_match 打分器**

```python
def test_exact_match_paths():
    scorer = ExactMatch({"json_paths": ["$.status","$.json.ok"]})
    res = scorer.score(
        expected={"status":200, "json":{"ok":True}},
        actual={"status":200, "json":{"ok":True}},
        context={}
    )
    assert res["pass_"] and res["score"] == 1.0
```

**1.4 custom_script 沙箱**

```python
def test_custom_script_runs_in_sandbox():
    res = run_custom_script(
        entrypoint="services/order-service/tests/scorers/order_rules.py:score",
        expected={}, actual={"json":{"items":[],"amount":0,"status":"CREATED"}},
        sandbox={"network": False, "filesystem_readonly": True}
    )
    assert "score" in res and "reasoning" in res
```

**1.5 llm_scorer 输出 JSON 校验（无需真连外部，使用 stub/mock）**

```python
def test_llm_scorer_json_schema_enforced(mock_model):
    mock_model.return_value = '{"score":0.9,"reasoning":"ok"}'
    res = LLMScorer(cfg).score(expected="...", actual="...", context={})
    assert res["pass_"] is True and 0 <= res["score"] <= 1
```

**1.6 聚合策略**

```python
def test_weighted_sum_with_fail_fast():
    agg = WeightedSum(weights={"a":0.5,"b":0.5}, pass_threshold=0.8, fail_fast_on=["a"])
    a = {"pass_": True, "score": 1.0}
    b = {"pass_": True, "score": 0.6}
    assert agg.aggregate({"a":a,"b":b})["pass_"] is True
```

**1.7 依赖管理（mock 模式）**

```python
def test_dependency_mock_server(prism_stub):
    dep = provision_dependency(kind="openapi_stub", contract=".../openapi.yaml", fixtures=".../fixtures")
    assert dep.is_ready()
```

**1.8 依赖管理（real 模式 + testcontainers）**

```python
def test_dependency_real_smoke(testcontainers_env):
    svc = up_service(image="ghcr.io/org/user-service:1.4.2", health="/healthz")
    assert http_get(svc.url+"/healthz").status_code == 200
```

**1.9 运行期数据装载**

```python
def test_dataset_loader():
    ds = load_dataset("services/order-service/data/runtime/DATASET.yaml", profile="test")
    assert ds.mounted_path.exists()
```

**1.10 报告生成**

```python
def test_report_json_and_junit_created(tmp_path):
    results = run_dummy_suite()
    write_reports(results, outdir=tmp_path)
    assert (tmp_path/"results.json").exists()
    assert (tmp_path/"junit.xml").exists()
```

## 2. 服务包级黑盒测试（示例用例直跑）

```python
# services/order-service/tests/test_blackbox.py
def test_create_order_success(orchestrator_runner):
    out = orchestrator_runner.run(service="order-service", matrix="fast-mock", filter="id=create-order-success")
    assert out.summary.passed >= 1
```

## 3. 契约测试（消费者驱动）

* 生成 `contracts/user-service.pact.json`，在 `contract-verify` 阶段与提供方服务进行校验。
* 若使用 OpenAPI：对照 `openapi.yaml` + fixtures 自动生成 stub，验证响应示例与 schema 匹配。

---

# 附：推荐的 Dockerfile 与运行命令（示例）

`services/order-service/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app/ app/
COPY api/ api/
COPY pyproject.toml pdm.lock ./
RUN pip install -U pip && pip install pdm && pdm install --prod
EXPOSE 8000
CMD ["python", "-m", "app.main"]
```

`service_definition.yaml`（运行节选）

```yaml
service:
  runtime:
    image: "ghcr.io/org/order-service:local"   # 可被 bb build 填充
    start_cmd: ["python","-m","app.main"]
    port: 8000
assets:
  manifest: "tests/assets/manifest.yaml"
datasets:
  runtime:
    - file: "data/runtime/DATASET.yaml"
      profile: "test"
```

---

## 实施清单（交付给项目组）

1. **在 Monorepo 建好骨架**（上文顶层结构）。
2. **在 Orchestrator 中完成以下模块**：

   * `loader.py`（Schema 校验，错误信息人类可读）
   * `assets.py`（asset:// 解析 + SHA 校验 + 只读挂载）
   * `datasets.py`（DATASET.yaml 拉取与挂载）
   * `deps.py`（依赖图 & mock/real 提供器；OpenAPI 到 stub 的生成）
   * `scoring/`（exact/custom/llm 三类打分器 + 聚合策略）
   * `runner.py`（测试执行；请求构造：HTTP/多 part/文件上传；重试/超时）
   * `report.py`（JSON/JUnit/HTML）
   * `cli.py`（`bb test`, `bb up`, `bb pack`, `bb release`）
3. **服务模板**：脚手架命令 `bb init` 生成 `service_definition.yaml`、`tests/test_cases.json`、`tests/assets/manifest.yaml`、`tests/scorers/`。
4. **CI**：按上文 Actions 配置运行 `fast-mock` 与 `contract-verify`；主干或 nightly 运行 `real-smoke` 与 `real-regression`。
5. **制品仓库**：搭建内部 PyPI/NPM/Docker Registry；`libs/` 采用 SemVer 与自动化发布脚本。
6. **治理**：

   * LLM 成本与输出合规（红队配置、脱敏）
   * 资产与数据许可证记录
   * 依赖版本上限与周期性升级
   * 测试随机性的种子固化与重跑（`bb score regrade`）

---

**总结建议**

* **评分引擎**以“多打分器 + 聚合”的可插拔架构实现 exact/custom/llm 的原生支持，且通过 JSONSchema 与沙箱执行保证稳定性与安全性。
* **资产管理**采用 `asset://` + `manifest.yaml` 的内容寻址，确保本地/CI 一致与可追溯。
* **仓库策略**建议 Monorepo 起步，配合路径感知 CI 和内部制品库；规模化后可做“母仓 + 子仓”演进。
* **依赖与隔离**通过 `dependencies` 声明 + 测试矩阵区分 mock/real 层次，既保证开发效率又兼顾集成真实性。
