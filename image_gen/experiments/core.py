from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from statistics import fmean
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.order_params import compute_order_params
from engine.search import generate_targets, simulated_annealing


REQUIRED_CASE_PARAMS = {
    "width",
    "height",
    "levels",
    "target_mode",
    "symmetry",
    "tau",
    "beta",
    "gamma",
    "mu",
    "dir_strength",
    "dir_angle",
    "translate_period",
    "T_init",
    "T_min",
    "cooling",
    "max_iter",
    "color_mode",
    "K",
    "w_pixel",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def protocol_hash(path: Path) -> str:
    return sha256_text(path.read_text())


def arange_closed(start: float, stop: float, step: float) -> list[float]:
    count = int(round((stop - start) / step)) + 1
    return [round(start + idx * step, 10) for idx in range(count)]


def validate_protocol(protocol: dict[str, Any]) -> None:
    required_top = {
        "protocol_name",
        "protocol_version",
        "description",
        "research_questions",
        "grid",
        "seed_policy",
        "focus_alphas",
        "cases",
    }
    missing = sorted(required_top - set(protocol))
    if missing:
        raise ValueError(f"Protocol missing keys: {missing}")

    grid = protocol["grid"]
    for axis in ("alpha", "sigma"):
        if axis not in grid:
            raise ValueError(f"Protocol grid missing axis: {axis}")
        axis_cfg = grid[axis]
        for key in ("start", "stop", "step"):
            if key not in axis_cfg:
                raise ValueError(f"Protocol grid axis {axis!r} missing {key!r}")

    seeds = protocol["seed_policy"].get("seeds")
    if not isinstance(seeds, list) or not seeds:
        raise ValueError("Protocol seed_policy.seeds must be a non-empty list")

    cases = protocol["cases"]
    if not isinstance(cases, list) or not cases:
        raise ValueError("Protocol cases must be a non-empty list")
    for case in cases:
        if "name" not in case or "params" not in case:
            raise ValueError("Each case must contain name and params")
        missing_case = sorted(REQUIRED_CASE_PARAMS - set(case["params"]))
        if missing_case:
            raise ValueError(f"Case {case.get('name', '<unknown>')} missing params: {missing_case}")


def alpha_grid(protocol: dict[str, Any]) -> list[float]:
    cfg = protocol["grid"]["alpha"]
    return arange_closed(float(cfg["start"]), float(cfg["stop"]), float(cfg["step"]))


def sigma_grid(protocol: dict[str, Any]) -> list[float]:
    cfg = protocol["grid"]["sigma"]
    return arange_closed(float(cfg["start"]), float(cfg["stop"]), float(cfg["step"]))


def focus_alphas(protocol: dict[str, Any]) -> list[float]:
    return [float(v) for v in protocol["focus_alphas"]]


def run_single_case(params: dict[str, Any], seed: int) -> dict[str, Any]:
    run_params = dict(params)
    H, W, L = run_params["height"], run_params["width"], run_params["levels"]
    channels = 3 if run_params.get("color_mode", "grayscale") == "rgb" else 1
    rng = np.random.default_rng(seed)
    targets = generate_targets(H, W, L, run_params["target_mode"], rng, channels=channels)
    image, scores = simulated_annealing(
        H,
        W,
        targets,
        run_params,
        levels=L,
        max_iter=run_params["max_iter"],
        T_init=run_params["T_init"],
        T_min=run_params["T_min"],
        cooling=run_params["cooling"],
        seed=seed,
    )
    ops = compute_order_params(
        image,
        scores,
        run_params,
        ["phi_em", "phi_cl", "xi", "phi_mirror"],
    )
    return {
        "seed": seed,
        "collapsed": bool(scores.is_collapsed),
        "phi_em": float(ops["phi_em"]),
        "phi_cl": float(ops["phi_cl"]),
        "xi": float(ops["xi"]),
        "phi_mirror": float(ops["phi_mirror"]),
        "dir_region": float(scores.dir_region),
        "em_region": float(scores.em_region),
        "cl_region": float(scores.cl_region),
    }


def group_raw_rows(raw_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in raw_rows:
        key = f"{row['case_name']}|{row['alpha']:.10f}|{row['sigma']:.10f}"
        grouped[key].append(row)
    return grouped


def collapse_state(collapse_rate: float) -> str:
    if collapse_rate == 0.0:
        return "stable"
    if collapse_rate == 1.0:
        return "collapsed"
    return "mixed"


def aggregate_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    collapse_rate = sum(1 for row in rows if row["collapsed"]) / len(rows)
    survivors = [row for row in rows if not row["collapsed"]]
    return {
        "collapse_rate": collapse_rate,
        "noncollapsed": len(survivors),
        "total": len(rows),
        "mean_phi_em": None if not survivors else float(fmean(row["phi_em"] for row in survivors)),
        "mean_phi_cl": None if not survivors else float(fmean(row["phi_cl"] for row in survivors)),
        "mean_xi": None if not survivors else float(fmean(row["xi"] for row in survivors)),
        "mean_phi_mirror": None if not survivors else float(fmean(row["phi_mirror"] for row in survivors)),
        "state": collapse_state(collapse_rate),
    }


def sigma_boundary(rows: list[dict[str, Any]], predicate) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    alpha_values = sorted({float(row["alpha"]) for row in rows})
    for alpha in alpha_values:
        matches = [row for row in rows if float(row["alpha"]) == alpha and predicate(float(row["collapse_rate"]))]
        out[f"{alpha:.2f}"] = None if not matches else min(float(row["sigma"]) for row in matches)
    return out


def alpha_floor(rows: list[dict[str, Any]], predicate) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    sigma_values = sorted({float(row["sigma"]) for row in rows})
    for sigma in sigma_values:
        matches = [row for row in rows if float(row["sigma"]) == sigma and predicate(float(row["collapse_rate"]))]
        out[f"{sigma:.2f}"] = None if not matches else min(float(row["alpha"]) for row in matches)
    return out


def existing_values(values: list[float | None]) -> list[float]:
    return [float(v) for v in values if v is not None]


def monotone_non_decreasing(values: list[float | None]) -> bool:
    nums = existing_values(values)
    return all(a <= b for a, b in zip(nums, nums[1:]))


def average_or_none(values: list[float | None]) -> float | None:
    nums = existing_values(values)
    return None if not nums else float(fmean(nums))


def ascii_phase_map(rows: list[dict[str, Any]], alphas: list[float], sigmas: list[float]) -> str:
    table = {(float(row["alpha"]), float(row["sigma"])): row for row in rows}
    lines = []
    lines.append("α\\σ  " + " ".join(f"{sigma:>4.1f}" for sigma in sigmas))
    for alpha in sorted(alphas, reverse=True):
        symbols = []
        for sigma in sigmas:
            row = table[(float(alpha), float(sigma))]
            symbols.append({"stable": "S", "mixed": "M", "collapsed": "X"}[row["state"]])
        lines.append(f"{alpha:>4.2f} " + "    ".join(symbols))
    return "\n".join(lines)


def format_num(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "N/A"
    if value == 0:
        return "0"
    abs_value = abs(value)
    if abs_value >= 1000 or abs_value < 0.01:
        return f"{value:.3e}"
    return f"{value:.{digits}f}"
