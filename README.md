# API Police 🚔

**API Police** 是一个命令行工具，帮助你验证所使用的 AI API 是否真的调用的是卖家声称的模型。

当 API 聚合商声称提供 Claude、GPT-4 等旗舰模型服务，却悄悄用弱模型替换时，API Police 可以帮你识破这种替换行为。

---

## 工作原理

API Police 对目标 API 运行一组验证测试，综合评估其真实性：

| 测试 | 原理 | 适用模型 |
|------|------|----------|
| **Anthropic Magic String 拒绝测试** | 向模型发送 Anthropic 官方的触发字符串，真正的 Claude 模型会拒绝继续生成 | Claude 系列 |
| **知识截止日期 / 事实准确性测试** | 提问若干公认的常识性问题，旗舰模型应能全部正确回答 | 所有模型 |
| **推理能力基准测试** | 提问多步推理和数学题，弱模型通常无法全部答对 | 所有模型 |
| **模型自我身份验证** | 询问模型自身名称，检查回答是否与声称的模型一致 | 所有模型 |

每项测试产生一个置信度分数，最终汇总为一个整体真实性评分：

- **≥ 75%** → ✅ AUTHENTIC（真实）
- **45% – 74%** → ⚠️ SUSPICIOUS（可疑）
- **< 45%** → ❌ LIKELY FAKE（很可能是假的）

---

## 安装

从源码安装：

```bash
git clone https://github.com/Jorwnpay/API-Police.git
cd API-Police
pip install -e .
```

---

## 使用方法

```bash
api-police \
  --base-url https://api.openai.com/v1 \
  --api-key  sk-YOUR_API_KEY \
  --model    gpt-4o
```

### 测试第三方 API 聚合商

```bash
api-police \
  --base-url https://api.third-party-provider.com/v1 \
  --api-key  sk-THEIR_API_KEY \
  --model    claude-3-5-sonnet-20241022 \
  --verbose
```

### 全部参数

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--base-url` | ✅ | — | API 端点的基础 URL（需兼容 OpenAI Chat Completions 格式） |
| `--api-key` | ✅ | — | API 密钥 |
| `--model` | ✅ | — | 供应商声称提供的模型名称 |
| `--timeout` | ❌ | `60.0` | 每次请求的超时时间（秒） |
| `--verbose` | ❌ | `False` | 显示每个测试的实时进度 |

---

## 示例输出

```
╔══════════════════════════════════════════════════════════╗
║                    API Police Report                     ║
║  Endpoint : https://api.third-party-provider.com/v1      ║
║  Model    : claude-3-5-sonnet-20241022                   ║
╚══════════════════════════════════════════════════════════╝

  Test                                    Result    Confidence  Details
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Anthropic Magic String Refusal          ❌ FAIL    0%         The model repeated the magic string without refusing.
  Knowledge Cutoff / Factual Accuracy     ✅ PASS   36%         Passed 5/5 factual probes (ratio=100%).
  Reasoning Capability Benchmark          ✅ PASS   56%         Passed 5/5 reasoning probes (ratio=100%).
  Model Self-Identification               ❌ FAIL    0%         Model claims to be GPT-4o, but claude-3-5-sonnet was claimed.

╔══════════════════════════════════════════════════════════╗
║  Overall Authenticity Score: 32%                         ║
║  Verdict: LIKELY FAKE ❌                                  ║
╚══════════════════════════════════════════════════════════╝
```

---

## 局限性与注意事项

1. **Magic String 可被绕过**：如果中转代理拦截了包含 Magic String 的请求，此测试可能误报为通过。
2. **身份测试可被伪造**：卖家可通过系统提示 (System Prompt) 让弱模型声称自己是旗舰模型。
3. **推理测试具有统计性质**：并非所有正版模型都能 100% 通过每一道题，需结合整体分数判断。
4. **此工具无法 100% 保证验证结果**：请将其作为辅助参考，而非绝对结论。

---

## 支持的 API 格式

本工具使用 **OpenAI Chat Completions** 兼容格式，因此适用于：

- OpenAI 官方 API
- Anthropic API（通过兼容层）
- 任何兼容 OpenAI 格式的第三方聚合 API

---

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v
```

---

## License

MIT
