"""Command-line interface for API Police."""

from __future__ import annotations

import argparse
import sys

from api_police.report import print_report, write_report_json
from api_police.runner import run_audit, run_calibration


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="api-police",
        description="API Police - 模型真伪验证工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  api-police --base-url https://api.provider.com/v1 --api-key sk-xxx --claimed-model gpt-4o --mode quick\n"
            "  api-police --base-url https://api.provider.com/v1 --api-key sk-xxx --claimed-model claude-3-5-sonnet-20241022 --mode full --output report.json\n"
            "  api-police --calibrate --base-url https://api.openai.com/v1 --api-key sk-xxx --model-family gpt --model-name gpt-4o"
        ),
    )

    parser.add_argument("--base-url", required=True, help="API base URL")
    parser.add_argument("--api-key", required=True, help="API key")
    parser.add_argument("--claimed-model", help="声称的模型名称")
    parser.add_argument("--model", help="兼容旧参数，等价于 --claimed-model")
    parser.add_argument("--mode", choices=["quick", "full"], default="quick", help="检测模式")
    parser.add_argument("--calibrate", action="store_true", help="校准模式")
    parser.add_argument("--model-family", help="校准模式下模型家族")
    parser.add_argument("--model-name", help="校准模式下模型名称")
    parser.add_argument("--fingerprint-dir", default="fingerprints", help="指纹数据库目录")
    parser.add_argument("--output", help="输出 JSON 报告路径")
    parser.add_argument("--timeout", type=float, default=60.0, help="请求超时（秒）")
    parser.add_argument("--verbose", action="store_true", help="保留兼容参数（当前版本忽略）")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    claimed_model = args.claimed_model or args.model

    if args.calibrate:
        if not args.model_family or not args.model_name:
            parser.error("校准模式需要 --model-family 和 --model-name")

        run_calibration(
            base_url=args.base_url,
            api_key=args.api_key,
            model_name=args.model_name,
            model_family=args.model_family,
            timeout=args.timeout,
            fingerprint_dir=args.fingerprint_dir,
        )
        print("✅ 校准完成")
        return

    if not claimed_model:
        parser.error("检测模式需要 --claimed-model（或 --model）")

    report = run_audit(
        base_url=args.base_url,
        api_key=args.api_key,
        claimed_model=claimed_model,
        mode=args.mode,
        timeout=args.timeout,
        fingerprint_dir=args.fingerprint_dir,
    )
    print_report(report)

    if args.output:
        write_report_json(report, args.output)
        print(f"💾 报告已保存: {args.output}")

    verdict = report.analysis.get("verdict", "")
    if "GENUINE" not in verdict:
        sys.exit(1)


if __name__ == "__main__":
    main()
