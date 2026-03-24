# API Police 🚔

[English](README.md) | [简体中文](readme_zh.md)

API Police 是一个多维度的模型真伪审计工具，用于验证第三方 API 服务商是否真的在提供其声称的模型。

## 更新日志

### v0.1.0（2026-03-24）

- 从少量测试升级为 **7 层交叉验证框架**。
- 增加审计模式：`quick`（快速筛查）与 `full`（高置信审计）。
- 增加 **指纹校准** 流程，可先在官方端点建立可信基线。
- 增加批量校准脚本：`api-police-batch-calibrate`。
- 扩展检测覆盖：分词、能力、行为、logprobs、性能、知识边界、直接探针。

## 核心思路

单一测试容易被绕过；多维信号交叉验证会显著提高伪造成本。

当前版本实现以下 7 层检测：

1. Tokenizer Fingerprint（分词指纹）
2. Capability Ladder（能力阶梯）
3. Behavioral Fingerprint（行为统计）
4. LogProbs Distribution（概率分布）
5. Performance Profile（性能画像）
6. Knowledge Boundary（知识边界）
7. Direct Probes（直接探针：magic string / 身份 / prompt 提取 / 一致性）

## 安装

```bash
pip install -e .
```

## 使用方式

### 为什么建议先做“指纹校准”？

指纹校准会先从官方 API 采集并建立可信基线。后续你在审计第三方接口时，API Police 会把目标行为与这套基线做对照，而不是仅凭单次问答结论来判断。

不做校准也能运行检测，但在边界场景中，结论的可解释性与置信度会更弱。

### `quick` 和 `full` 的区别

- `quick`：探针更少、成本更低、速度更快，适合日常巡检和大批量初筛。
- `full`：探针更多、维度更全、耗时更高，适合上线前、风控前或合规场景。

### 快速检测（低成本）

```bash
api-police \
  --base-url https://api.provider.com/v1 \
  --api-key sk-xxx \
  --claimed-model claude-3-5-sonnet-20241022 \
  --mode quick
```

### 完整审计（高置信度）

```bash
api-police \
  --base-url https://api.provider.com/v1 \
  --api-key sk-xxx \
  --claimed-model gpt-4o \
  --mode full \
  --output report.json
```

### 指纹校准（官方 API 一次性操作）

```bash
api-police --calibrate \
  --base-url https://api.openai.com/v1 \
  --api-key sk-official \
  --model-family gpt \
  --model-name gpt-4o
```

## 参数说明

- `--base-url`：目标 API 基础 URL（OpenAI-compatible）
- `--api-key`：API Key
- `--claimed-model`：服务商声称的模型名
- `--mode`：`quick` 或 `full`
- `--calibrate`：进入校准模式
- `--model-family` / `--model-name`：校准模式下必填
- `--fingerprint-dir`：指纹目录（默认 `fingerprints`）
- `--output`：输出 JSON 报告
- `--timeout`：请求超时秒数

## 批量校准（Claude / GPT / Gemini）

批量校准脚本：`api-police-batch-calibrate`，用于一次性校准主流模型家族。

### OpenRouter 一键批量（推荐先用）

```bash
api-police-batch-calibrate \
  --provider openrouter \
  --api-key sk-or-xxx \
  --skip-existing
```

### 官方 API 分家族批量

```bash
api-police-batch-calibrate \
  --provider official \
  --claude-api-key sk-ant-xxx \
  --gpt-api-key sk-openai-xxx \
  --gemini-api-key sk-gemini-xxx \
  --skip-existing
```

### 常用参数

- `--families claude,gpt,gemini`：只跑指定家族
- `--delay-seconds 1.5`：模型之间延迟，减少限流
- `--fingerprint-dir fingerprints`：指纹输出目录
- `--summary-output fingerprints/batch_calibration_summary.json`：批量结果汇总

## 结果解释

- `✅ GENUINE`：多维指标整体一致
- `⚠️ SUSPICIOUS`：有明显异常，建议扩大样本复检
- `❌ LIKELY FAKE`：多项关键证据冲突，疑似替换模型

## 开发与测试

```bash
pip install -e ".[dev]"
pytest -q
```
