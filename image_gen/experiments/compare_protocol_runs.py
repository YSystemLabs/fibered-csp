from __future__ import annotations

import argparse
import json
from pathlib import Path

from core import format_num, load_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two analyzed protocol runs and render a strict comparison report.")
    parser.add_argument("v1_dir", type=Path)
    parser.add_argument("v2_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=None)
    return parser.parse_args()


def compare_case(case1: dict, case2: dict) -> dict:
    return {
        "stable_fraction_v1": case1["stable_fraction"],
        "stable_fraction_v2": case2["stable_fraction"],
        "stable_fraction_delta": case2["stable_fraction"] - case1["stable_fraction"],
        "full_threshold_mean_v1": case1["focus_full_threshold_mean"],
        "full_threshold_mean_v2": case2["focus_full_threshold_mean"],
        "full_threshold_mean_delta": (
            None
            if case1["focus_full_threshold_mean"] is None or case2["focus_full_threshold_mean"] is None
            else case2["focus_full_threshold_mean"] - case1["focus_full_threshold_mean"]
        ),
        "focus_summary_equal": case1["focus_summary"] == case2["focus_summary"],
        "stable_fraction_equal": case1["stable_fraction"] == case2["stable_fraction"],
        "ascii_phase_map_equal": case1["ascii_phase_map"] == case2["ascii_phase_map"],
    }


def build_comparison(v1: dict, v2: dict) -> dict:
    cases1 = v1["cases"]
    cases2 = v2["cases"]
    names1 = set(cases1)
    names2 = set(cases2)
    common = sorted(names1 & names2)
    added = sorted(names2 - names1)
    removed = sorted(names1 - names2)

    common_cases = {name: compare_case(cases1[name], cases2[name]) for name in common}

    size_cases = [name for name in sorted(cases2) if name.startswith("relaxed_") and "x" in name]
    size_trend = []
    for name in size_cases:
        case = cases2[name]
        size_trend.append(
            {
                "case_name": name,
                "stable_fraction": case["stable_fraction"],
                "full_threshold_mean": case["focus_full_threshold_mean"],
                "focus_summary": case["focus_summary"],
            }
        )

    return {
        "v1_manifest": v1["manifest"],
        "v2_manifest": v2["manifest"],
        "common_case_names": common,
        "added_case_names": added,
        "removed_case_names": removed,
        "common_cases": common_cases,
        "size_trend_v2": size_trend,
    }


def build_report(comp: dict) -> str:
    lines: list[str] = []
    lines.append("# V1 / V2 协议对比报告")
    lines.append("")
    lines.append("## 协议信息")
    lines.append("")
    lines.append(f"- V1 结果目录：{comp['v1_manifest']['result_dir']}")
    lines.append(f"- V2 结果目录：{comp['v2_manifest']['result_dir']}")
    lines.append(f"- V1 协议哈希：{comp['v1_manifest']['protocol_sha256']}")
    lines.append(f"- V2 协议哈希：{comp['v2_manifest']['protocol_sha256']}")
    lines.append("")
    lines.append("## 共有 case 一致性")
    lines.append("")
    for case_name in comp["common_case_names"]:
        row = comp["common_cases"][case_name]
        lines.append(f"### {case_name}")
        lines.append(f"- stable_fraction: V1={row['stable_fraction_v1']:.3f}, V2={row['stable_fraction_v2']:.3f}, delta={row['stable_fraction_delta']:.3f}")
        lines.append(f"- full_threshold_mean: V1={format_num(row['full_threshold_mean_v1'])}, V2={format_num(row['full_threshold_mean_v2'])}, delta={format_num(row['full_threshold_mean_delta'])}")
        lines.append(f"- focus_summary 是否完全一致：{row['focus_summary_equal']}")
        lines.append(f"- stable_fraction 是否完全一致：{row['stable_fraction_equal']}")
        lines.append(f"- ascii_phase_map 是否完全一致：{row['ascii_phase_map_equal']}")
        lines.append("")
    lines.append("## V2 新增 case")
    lines.append("")
    lines.append(f"- 新增：{', '.join(comp['added_case_names']) if comp['added_case_names'] else '无'}")
    lines.append(f"- 删除：{', '.join(comp['removed_case_names']) if comp['removed_case_names'] else '无'}")
    lines.append("")
    lines.append("## V2 尺度趋势")
    lines.append("")
    for row in comp["size_trend_v2"]:
        lines.append(f"### {row['case_name']}")
        lines.append(f"- stable_fraction={row['stable_fraction']:.3f}")
        lines.append(f"- focus_full_threshold_mean={format_num(row['full_threshold_mean'])}")
        for alpha_key, vals in row["focus_summary"].items():
            lines.append(
                f"- alpha={alpha_key}: any_survival_sigma={format_num(vals['sigma_any_survival'])}, full_survival_sigma={format_num(vals['sigma_full_survival'])}"
            )
        lines.append("")
    return "\n".join(lines)


def build_summary(comp: dict) -> str:
    lines: list[str] = []
    lines.append("# V1 / V2 对比摘要")
    lines.append("")
    lines.append("## 共有 case 复现性")
    lines.append("")
    for case_name in comp["common_case_names"]:
        row = comp["common_cases"][case_name]
        lines.append(
            f"- {case_name}: focus_summary_equal={row['focus_summary_equal']}, stable_fraction_equal={row['stable_fraction_equal']}, ascii_phase_map_equal={row['ascii_phase_map_equal']}"
        )
    lines.append("")
    lines.append("## V2 新增 case")
    lines.append("")
    lines.append(f"- {', '.join(comp['added_case_names']) if comp['added_case_names'] else '无'}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    v1_dir = args.v1_dir.resolve()
    v2_dir = args.v2_dir.resolve()
    output_dir = args.output_dir.resolve() if args.output_dir is not None else v2_dir / "comparison_to_v1"
    output_dir.mkdir(parents=True, exist_ok=True)

    v1 = load_json(v1_dir / "analysis.json")
    v2 = load_json(v2_dir / "analysis.json")
    comp = build_comparison(v1, v2)

    (output_dir / "comparison.json").write_text(json.dumps(comp, ensure_ascii=False, indent=2))
    (output_dir / "comparison.md").write_text(build_report(comp))
    (output_dir / "comparison_summary.md").write_text(build_summary(comp))
    print(f"Wrote {output_dir / 'comparison.json'}")
    print(f"Wrote {output_dir / 'comparison.md'}")
    print(f"Wrote {output_dir / 'comparison_summary.md'}")


if __name__ == "__main__":
    main()
