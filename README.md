# API Police 🚔

[English](README.md) | [简体中文](readme_zh.md)

API Police is a multi-dimensional model authenticity auditing tool for verifying whether a third-party API provider is truly serving the model it claims.

## Changelog

### v0.1.0 (2026-03-24)

- Upgraded from a small set of checks to a **7-layer verification framework**.
- Added audit modes: `quick` (fast triage) and `full` (high-confidence audit).
- Added **fingerprint calibration** workflow to build trusted baselines from official endpoints.
- Added batch calibration CLI: `api-police-batch-calibrate`.
- Expanded detector coverage (tokenizer, capability, behavior, logprobs, performance, knowledge boundary, direct probes).

## Core Idea

Single tests are easy to evade. Cross-validating multiple independent signals significantly increases spoofing cost.

Current version implements 7 verification layers:

1. Tokenizer Fingerprint
2. Capability Ladder
3. Behavioral Fingerprint
4. LogProbs Distribution
5. Performance Profile
6. Knowledge Boundary
7. Direct Probes (magic string / identity / prompt extraction / consistency)

## Installation

```bash
pip install -e .
```

## Usage

### Why run fingerprint calibration first?

Calibration creates a trusted local fingerprint from an official API for each model family. Later, when you audit a third-party endpoint, API Police compares observed behavior against this baseline instead of relying on a single prompt-response judgment.

Without calibration, you can still run checks, but confidence and explainability are weaker for borderline cases.

### `quick` vs `full`

- `quick`: low-cost triage, fewer probes, faster turnaround, good for routine screening and large endpoint lists.
- `full`: more probes and dimensions, slower but more robust, recommended before compliance/risk decisions.

### Quick audit (lower cost)

```bash
api-police \
  --base-url https://api.provider.com/v1 \
  --api-key sk-xxx \
  --claimed-model claude-3-5-sonnet-20241022 \
  --mode quick
```

### Full audit (higher confidence)

```bash
api-police \
  --base-url https://api.provider.com/v1 \
  --api-key sk-xxx \
  --claimed-model gpt-4o \
  --mode full \
  --output report.json
```

### Fingerprint calibration (one-time, official API)

```bash
api-police --calibrate \
  --base-url https://api.openai.com/v1 \
  --api-key sk-official \
  --model-family gpt \
  --model-name gpt-4o
```

## CLI Options

- `--base-url`: target API base URL (OpenAI-compatible)
- `--api-key`: API key
- `--claimed-model`: claimed model name
- `--mode`: `quick` or `full`
- `--calibrate`: calibration mode
- `--model-family` / `--model-name`: required in calibration mode
- `--fingerprint-dir`: fingerprint directory (default: `fingerprints`)
- `--output`: output JSON report path
- `--timeout`: request timeout in seconds

## Batch Calibration (Claude / GPT / Gemini)

New script: `api-police-batch-calibrate`, for one-shot calibration of major model families.

### OpenRouter one-shot batch (recommended first)

```bash
api-police-batch-calibrate \
  --provider openrouter \
  --api-key sk-or-xxx \
  --skip-existing
```

### Official API batch by family

```bash
api-police-batch-calibrate \
  --provider official \
  --claude-api-key sk-ant-xxx \
  --gpt-api-key sk-openai-xxx \
  --gemini-api-key sk-gemini-xxx \
  --skip-existing
```

### Common parameters

- `--families claude,gpt,gemini`: run selected families only
- `--delay-seconds 1.5`: delay between models to reduce rate limiting
- `--fingerprint-dir fingerprints`: fingerprint output directory
- `--summary-output fingerprints/batch_calibration_summary.json`: batch summary file

## Verdicts

- `✅ GENUINE`: multi-signal profile is broadly consistent
- `⚠️ SUSPICIOUS`: notable anomalies, re-check with larger sample
- `❌ LIKELY FAKE`: multiple key signals conflict, model substitution likely

## Development & Testing

```bash
pip install -e ".[dev]"
pytest -q
```
