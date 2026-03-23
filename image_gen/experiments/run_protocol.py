from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from core import (
    alpha_grid,
    dump_json,
    load_json,
    protocol_hash,
    run_single_case,
    sigma_grid,
    validate_protocol,
)

BASE_DIR = Path(__file__).parent
DEFAULT_PROTOCOL = BASE_DIR / "protocols" / "alpha_sigma_size_full_v1.json"
RESULTS_DIR = BASE_DIR / "results"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run experiment protocol and emit raw rows only.")
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--output-dir", type=Path, default=None)
    return parser.parse_args()


def build_result_dir(protocol_path: Path, output_dir: Path | None) -> Path:
    if output_dir is not None:
        return output_dir
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return RESULTS_DIR / f"{protocol_path.stem}__{stamp}"


def main() -> None:
    args = parse_args()
    protocol_path = args.protocol.resolve()
    protocol = load_json(protocol_path)
    validate_protocol(protocol)

    result_dir = build_result_dir(protocol_path, args.output_dir)
    result_dir.mkdir(parents=True, exist_ok=True)
    raw_path = result_dir / "raw_runs.jsonl"
    manifest_path = result_dir / "manifest.json"

    alphas = alpha_grid(protocol)
    sigmas = sigma_grid(protocol)
    seeds = protocol["seed_policy"]["seeds"]
    cases = protocol["cases"]
    proto_hash = protocol_hash(protocol_path)

    total_runs = len(cases) * len(alphas) * len(sigmas) * len(seeds)
    manifest = {
        "protocol_path": str(protocol_path),
        "protocol_name": protocol["protocol_name"],
        "protocol_version": protocol["protocol_version"],
        "protocol_sha256": proto_hash,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "result_dir": str(result_dir),
        "alphas": alphas,
        "sigmas": sigmas,
        "seeds": seeds,
        "case_names": [case["name"] for case in cases],
        "total_runs": total_runs,
        "raw_runs_path": str(raw_path),
        "analysis_path": str(result_dir / "analysis.json"),
        "report_path": str(result_dir / "report.md"),
        "summary_path": str(result_dir / "summary.md"),
    }
    dump_json(manifest_path, manifest)

    with raw_path.open("w", encoding="utf-8") as f:
        for case in cases:
            case_name = case["name"]
            base_params = dict(case["params"])
            for alpha in alphas:
                for sigma in sigmas:
                    params = dict(base_params)
                    params["alpha"] = alpha
                    params["sigma"] = sigma
                    for seed in seeds:
                        outputs = run_single_case(params, int(seed))
                        row = {
                            "protocol_name": protocol["protocol_name"],
                            "protocol_version": protocol["protocol_version"],
                            "protocol_sha256": proto_hash,
                            "case_name": case_name,
                            "alpha": alpha,
                            "sigma": sigma,
                            "seed": int(seed),
                            "params": params,
                            **outputs,
                        }
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Wrote {manifest_path}")
    print(f"Wrote {raw_path}")


if __name__ == "__main__":
    main()
