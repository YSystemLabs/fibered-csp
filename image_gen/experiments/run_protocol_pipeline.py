from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
DEFAULT_PROTOCOL = BASE_DIR / "protocols" / "alpha_sigma_size_smoke_v1.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full experiment pipeline: raw -> analysis -> report.")
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--output-dir", type=Path, default=None)
    return parser.parse_args()


def run_step(args: list[str]) -> None:
    subprocess.run([sys.executable, *args], check=True)


def main() -> None:
    args = parse_args()
    protocol = args.protocol.resolve()
    output_dir = args.output_dir.resolve() if args.output_dir is not None else None

    run_args = [str(BASE_DIR / "run_protocol.py"), "--protocol", str(protocol)]
    if output_dir is not None:
        run_args.extend(["--output-dir", str(output_dir)])
    run_step(run_args)

    if output_dir is None:
        raise ValueError("run_protocol_pipeline.py requires --output-dir for reproducible downstream steps")

    run_step([str(BASE_DIR / "analyze_protocol_run.py"), str(output_dir)])
    run_step([str(BASE_DIR / "render_protocol_report.py"), str(output_dir)])


if __name__ == "__main__":
    main()
