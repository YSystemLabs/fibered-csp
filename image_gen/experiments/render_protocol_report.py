from __future__ import annotations

import argparse
from pathlib import Path

from core import format_num, load_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render markdown report strictly from analysis.json.")
    parser.add_argument("result_dir", type=Path)
    return parser.parse_args()


def build_report(analysis: dict) -> str:
    manifest = analysis["manifest"]
    cases = analysis["cases"]
    focus_alphas = analysis["focus_alphas"]
    global_summary = analysis["global_summary"]

    lines: list[str] = []
    lines.append("# 实验报告")
    lines.append("")
    lines.append("## 协议信息")
    lines.append("")
    lines.append(f"- 协议名称：{analysis['protocol_name']}")
    lines.append(f"- 协议版本：{analysis['protocol_version']}")
    lines.append(f"- 协议哈希：{manifest['protocol_sha256']}")
    lines.append(f"- 结果目录：{manifest['result_dir']}")
    lines.append(f"- 原始数据：{Path(manifest['raw_runs_path']).name}")
    lines.append(f"- 分析数据：{Path(manifest['analysis_path']).name}")
    lines.append("")
    lines.append("## 研究问题")
    lines.append("")
    for idx, question in enumerate(analysis["research_questions"], start=1):
        lines.append(f"{idx}. {question}")
    lines.append("")
    lines.append("## 结果总览")
    lines.append("")
    lines.append(
        f"- 所有 case 的低 alpha 全稳定阈值是否单调：{global_summary['all_cases_focus_full_threshold_monotone']}"
    )
    lines.append(
        f"- 所有 case 的低 alpha 任意幸存阈值是否单调：{global_summary['all_cases_focus_any_threshold_monotone']}"
    )
    lines.append("")
    lines.append("各 case 的稳定格点占比：")
    for case_name, value in global_summary["stable_fraction_by_case"].items():
        lines.append(f"- {case_name}: {value:.3f}")
    lines.append("")
    lines.append("各 case 的低 alpha 全稳定阈值均值：")
    for case_name, value in global_summary["focus_full_threshold_mean_by_case"].items():
        lines.append(f"- {case_name}: {format_num(value)}")
    lines.append("")

    for case_name, case in cases.items():
        lines.append(f"## {case_name}")
        lines.append("")
        lines.append("### 聚合统计")
        lines.append("")
        lines.append(f"- 稳定格点占比：{case['stable_fraction']:.3f}")
        lines.append(f"- 混合格点占比：{case['mixed_fraction']:.3f}")
        lines.append(f"- 坍缩格点占比：{case['collapsed_fraction']:.3f}")
        lines.append(f"- 低 alpha 全稳定阈值均值：{format_num(case['focus_full_threshold_mean'])}")
        lines.append(f"- 低 alpha 任意幸存阈值均值：{format_num(case['focus_any_threshold_mean'])}")
        lines.append(f"- 低 alpha 全稳定阈值是否单调：{case['focus_full_threshold_monotone']}")
        lines.append(f"- 低 alpha 任意幸存阈值是否单调：{case['focus_any_threshold_monotone']}")
        lines.append("")
        lines.append("### 低 alpha 截面")
        lines.append("")
        for alpha in focus_alphas:
            key = f"{alpha:.2f}"
            vals = case['focus_summary'][key]
            lines.append(
                f"- alpha={key}: 任意幸存阈值 sigma={format_num(vals['sigma_any_survival'])}，全稳定阈值 sigma={format_num(vals['sigma_full_survival'])}"
            )
        lines.append("")
        lines.append("### 文本相图")
        lines.append("")
        lines.append("```text")
        lines.append(case["ascii_phase_map"])
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def build_summary(analysis: dict) -> str:
    global_summary = analysis["global_summary"]
    lines: list[str] = []
    lines.append("# 实验结论摘要")
    lines.append("")
    lines.append("## 结果驱动摘要")
    lines.append("")
    lines.append(
        f"- 低 alpha 全稳定阈值在全部 case 上是否单调：{global_summary['all_cases_focus_full_threshold_monotone']}"
    )
    lines.append(
        f"- 低 alpha 任意幸存阈值在全部 case 上是否单调：{global_summary['all_cases_focus_any_threshold_monotone']}"
    )
    lines.append("- 各 case 稳定格点占比：")
    for case_name, value in global_summary["stable_fraction_by_case"].items():
        lines.append(f"  - {case_name}: {value:.3f}")
    lines.append("- 各 case 低 alpha 全稳定阈值均值：")
    for case_name, value in global_summary["focus_full_threshold_mean_by_case"].items():
        lines.append(f"  - {case_name}: {format_num(value)}")
    lines.append("")
    lines.append("## 说明")
    lines.append("")
    lines.append("- 本摘要只复述 analysis.json 中已有统计量，不引入额外推断。")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    result_dir = args.result_dir.resolve()
    analysis = load_json(result_dir / "analysis.json")
    report_path = result_dir / "report.md"
    summary_path = result_dir / "summary.md"
    report_path.write_text(build_report(analysis))
    summary_path.write_text(build_summary(analysis))
    print(f"Wrote {report_path}")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
