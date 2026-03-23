from __future__ import annotations

import argparse
import json
from pathlib import Path

from core import (
    aggregate_group,
    alpha_floor,
    alpha_grid,
    ascii_phase_map,
    average_or_none,
    existing_values,
    focus_alphas,
    group_raw_rows,
    load_json,
    monotone_non_decreasing,
    sigma_boundary,
    sigma_grid,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze raw experiment rows into derived statistics only.")
    parser.add_argument("result_dir", type=Path)
    return parser.parse_args()


def load_raw_rows(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def summarize_case(case_name: str, rows: list[dict], alphas: list[float], sigmas: list[float], focus: list[float]) -> dict:
    stable_cells = sum(1 for row in rows if row["state"] == "stable")
    mixed_cells = sum(1 for row in rows if row["state"] == "mixed")
    collapsed_cells = sum(1 for row in rows if row["state"] == "collapsed")
    total = len(rows)

    sigma_any = sigma_boundary(rows, lambda cr: cr < 1.0)
    sigma_full = sigma_boundary(rows, lambda cr: cr == 0.0)
    alpha_full = alpha_floor(rows, lambda cr: cr == 0.0)

    focus_summary = {}
    for alpha in focus:
        key = f"{alpha:.2f}"
        focus_summary[key] = {
            "sigma_any_survival": sigma_any.get(key),
            "sigma_full_survival": sigma_full.get(key),
        }

    full_thresholds = [focus_summary[f"{alpha:.2f}"]["sigma_full_survival"] for alpha in focus]
    any_thresholds = [focus_summary[f"{alpha:.2f}"]["sigma_any_survival"] for alpha in focus]

    return {
        "case_name": case_name,
        "stable_cells": stable_cells,
        "mixed_cells": mixed_cells,
        "collapsed_cells": collapsed_cells,
        "stable_fraction": stable_cells / total,
        "mixed_fraction": mixed_cells / total,
        "collapsed_fraction": collapsed_cells / total,
        "sigma_any_survival_by_alpha": sigma_any,
        "sigma_full_survival_by_alpha": sigma_full,
        "lowest_fully_stable_alpha_by_sigma": alpha_full,
        "focus_summary": focus_summary,
        "focus_any_thresholds": any_thresholds,
        "focus_full_thresholds": full_thresholds,
        "focus_any_threshold_mean": average_or_none(any_thresholds),
        "focus_full_threshold_mean": average_or_none(full_thresholds),
        "focus_any_threshold_monotone": monotone_non_decreasing(any_thresholds),
        "focus_full_threshold_monotone": monotone_non_decreasing(full_thresholds),
        "ascii_phase_map": ascii_phase_map(rows, alphas, sigmas),
    }


def main() -> None:
    args = parse_args()
    result_dir = args.result_dir.resolve()
    manifest = load_json(result_dir / "manifest.json")
    protocol = load_json(Path(manifest["protocol_path"]))
    raw_rows = load_raw_rows(result_dir / "raw_runs.jsonl")

    grouped = group_raw_rows(raw_rows)
    cell_rows = []
    for group_rows in grouped.values():
        sample = group_rows[0]
        agg = aggregate_group(group_rows)
        cell_rows.append({
            "case_name": sample["case_name"],
            "alpha": float(sample["alpha"]),
            "sigma": float(sample["sigma"]),
            **agg,
        })
    cell_rows.sort(key=lambda row: (row["case_name"], row["alpha"], row["sigma"]))

    alphas = alpha_grid(protocol)
    sigmas = sigma_grid(protocol)
    focus = focus_alphas(protocol)

    cases = {}
    for case in protocol["cases"]:
        case_name = case["name"]
        case_rows = [row for row in cell_rows if row["case_name"] == case_name]
        cases[case_name] = summarize_case(case_name, case_rows, alphas, sigmas, focus)

    case_names = [case["name"] for case in protocol["cases"]]
    global_summary = {
        "case_names": case_names,
        "all_cases_focus_full_threshold_monotone": all(cases[name]["focus_full_threshold_monotone"] for name in case_names),
        "all_cases_focus_any_threshold_monotone": all(cases[name]["focus_any_threshold_monotone"] for name in case_names),
        "stable_fraction_by_case": {name: cases[name]["stable_fraction"] for name in case_names},
        "focus_full_threshold_mean_by_case": {name: cases[name]["focus_full_threshold_mean"] for name in case_names},
    }

    analysis = {
        "manifest": manifest,
        "protocol_name": protocol["protocol_name"],
        "protocol_version": protocol["protocol_version"],
        "research_questions": protocol["research_questions"],
        "focus_alphas": focus,
        "alphas": alphas,
        "sigmas": sigmas,
        "cell_rows": cell_rows,
        "cases": cases,
        "global_summary": global_summary,
    }

    out_path = result_dir / "analysis.json"
    out_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
