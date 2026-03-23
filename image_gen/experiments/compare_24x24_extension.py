from __future__ import annotations

import argparse
import json
from pathlib import Path

from core import format_num, load_json

FOCUS_ALPHAS = [0.10, 0.08, 0.06, 0.04]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare V2 24x24 results with V3 extended-sigma 24x24 results.")
    parser.add_argument("v2_dir", type=Path)
    parser.add_argument("v3_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=None)
    return parser.parse_args()


def case_rows(analysis: dict, case_name: str) -> list[dict]:
    return [row for row in analysis["cell_rows"] if row["case_name"] == case_name]


def keyed(rows: list[dict], max_sigma: float | None = None) -> dict[tuple[float, float], dict]:
    table = {}
    for row in rows:
        alpha = float(row["alpha"])
        sigma = float(row["sigma"])
        if max_sigma is not None and sigma > max_sigma + 1e-9:
            continue
        table[(alpha, sigma)] = row
    return table


def first_sigma(rows: list[dict], alpha: float, predicate) -> float | None:
    matches = [float(row["sigma"]) for row in rows if float(row["alpha"]) == alpha and predicate(float(row["collapse_rate"]))]
    return None if not matches else min(matches)


def build_comparison(v2: dict, v3: dict) -> dict:
    rows_v2 = case_rows(v2, "relaxed_24x24")
    rows_v3 = case_rows(v3, "relaxed_24x24")

    overlap_v2 = keyed(rows_v2, max_sigma=2.0)
    overlap_v3 = keyed(rows_v3, max_sigma=2.0)
    common_keys = sorted(set(overlap_v2) & set(overlap_v3))

    overlap_equal = all(overlap_v2[key] == overlap_v3[key] for key in common_keys)
    differing_keys = [key for key in common_keys if overlap_v2[key] != overlap_v3[key]]

    focus = {}
    for alpha in FOCUS_ALPHAS:
        v2_any = first_sigma(rows_v2, alpha, lambda cr: cr < 1.0)
        v2_full = first_sigma(rows_v2, alpha, lambda cr: cr == 0.0)
        v3_any = first_sigma(rows_v3, alpha, lambda cr: cr < 1.0)
        v3_full = first_sigma(rows_v3, alpha, lambda cr: cr == 0.0)
        focus[f"{alpha:.2f}"] = {
            "v2_any_survival_sigma": v2_any,
            "v2_full_survival_sigma": v2_full,
            "v3_any_survival_sigma": v3_any,
            "v3_full_survival_sigma": v3_full,
        }

    extended_only = [row for row in rows_v3 if float(row["sigma"]) > 2.0]
    extended_summary = {
        "stable_cells": sum(1 for row in extended_only if row["state"] == "stable"),
        "mixed_cells": sum(1 for row in extended_only if row["state"] == "mixed"),
        "collapsed_cells": sum(1 for row in extended_only if row["state"] == "collapsed"),
        "total_cells": len(extended_only),
    }

    return {
        "v2_manifest": v2["manifest"],
        "v3_manifest": v3["manifest"],
        "overlap_sigma_max": 2.0,
        "overlap_equal": overlap_equal,
        "overlap_cell_count": len(common_keys),
        "overlap_differing_keys": differing_keys,
        "focus_comparison": focus,
        "extended_only_summary": extended_summary,
    }


def build_report(comp: dict) -> str:
    lines: list[str] = []
    lines.append("# 24x24 sigma 扩展 V2/V3 对比报告")
    lines.append("")
    lines.append("## 基本信息")
    lines.append("")
    lines.append(f"- V2 结果目录：{comp['v2_manifest']['result_dir']}")
    lines.append(f"- V3 结果目录：{comp['v3_manifest']['result_dir']}")
    lines.append(f"- 重叠窗口：sigma <= {comp['overlap_sigma_max']}")
    lines.append(f"- 重叠窗口内 cell 数：{comp['overlap_cell_count']}")
    lines.append(f"- 重叠窗口结果是否完全一致：{comp['overlap_equal']}")
    lines.append("")
    lines.append("## 低 alpha 对比")
    lines.append("")
    for alpha_key, row in comp["focus_comparison"].items():
        lines.append(f"### alpha={alpha_key}")
        lines.append(f"- V2 任意幸存阈值：{format_num(row['v2_any_survival_sigma'])}")
        lines.append(f"- V2 全稳定阈值：{format_num(row['v2_full_survival_sigma'])}")
        lines.append(f"- V3 任意幸存阈值：{format_num(row['v3_any_survival_sigma'])}")
        lines.append(f"- V3 全稳定阈值：{format_num(row['v3_full_survival_sigma'])}")
        lines.append("")
    ext = comp["extended_only_summary"]
    lines.append("## 扩展窗口 (sigma > 2.0) 摘要")
    lines.append("")
    lines.append(f"- stable_cells={ext['stable_cells']}")
    lines.append(f"- mixed_cells={ext['mixed_cells']}")
    lines.append(f"- collapsed_cells={ext['collapsed_cells']}")
    lines.append(f"- total_cells={ext['total_cells']}")
    lines.append("")
    return "\n".join(lines)


def build_summary(comp: dict) -> str:
    lines: list[str] = []
    lines.append("# 24x24 sigma 扩展 V2/V3 对比摘要")
    lines.append("")
    lines.append(f"- 重叠窗口结果是否完全一致：{comp['overlap_equal']}")
    for alpha_key, row in comp["focus_comparison"].items():
        lines.append(
            f"- alpha={alpha_key}: V2(any/full)=({format_num(row['v2_any_survival_sigma'])}/{format_num(row['v2_full_survival_sigma'])}), V3(any/full)=({format_num(row['v3_any_survival_sigma'])}/{format_num(row['v3_full_survival_sigma'])})"
        )
    ext = comp["extended_only_summary"]
    lines.append(
        f"- 扩展窗口统计: stable={ext['stable_cells']}, mixed={ext['mixed_cells']}, collapsed={ext['collapsed_cells']}, total={ext['total_cells']}"
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    v2 = load_json(args.v2_dir.resolve() / "analysis.json")
    v3 = load_json(args.v3_dir.resolve() / "analysis.json")
    output_dir = args.output_dir.resolve() if args.output_dir is not None else args.v3_dir.resolve() / "comparison_to_v2"
    output_dir.mkdir(parents=True, exist_ok=True)

    comp = build_comparison(v2, v3)
    (output_dir / "comparison.json").write_text(json.dumps(comp, ensure_ascii=False, indent=2))
    (output_dir / "comparison.md").write_text(build_report(comp))
    (output_dir / "comparison_summary.md").write_text(build_summary(comp))
    print(f"Wrote {output_dir / 'comparison.json'}")
    print(f"Wrote {output_dir / 'comparison.md'}")
    print(f"Wrote {output_dir / 'comparison_summary.md'}")


if __name__ == "__main__":
    main()
