#!/usr/bin/env python3
"""
Fibered-CSP Sudoku Solver v0.1 — CLI 入口。

对应 spec §7 (输入输出格式), §0.2 (sys.setrecursionlimit)。

用法:
    python -m code.main <81-char-puzzle>
    python -m code.main --log <81-char-puzzle>
    python -m code.main --count <81-char-puzzle>
    echo "<puzzle>" | python -m code.main -
"""

from __future__ import annotations

import json
import sys
import argparse

# §0.2 递归限制（在任何求解逻辑之前设置）
sys.setrecursionlimit(2000)

from .compiler import compile_sudoku, cell_name
from .parser import parse_puzzle, check_given_conflicts, ParseError, GivenConflict
from .solver import Solver, Contradiction


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Fibered-CSP Sudoku Solver v0.1'
    )
    parser.add_argument(
        'puzzle',
        help='81-char puzzle string (digits 1-9 for givens, 0 or . for empty). '
             'Use "-" to read from stdin.'
    )
    parser.add_argument(
        '--log', action='store_true',
        help='Output full LogEntry sequence (JSON lines)'
    )
    parser.add_argument(
        '--count', action='store_true',
        help='Count all solutions (verify uniqueness)'
    )
    args = parser.parse_args()

    # 读取输入
    puzzle_str = args.puzzle
    if puzzle_str == '-':
        puzzle_str = sys.stdin.read().strip()

    # §8 编译
    compiled = compile_sudoku()

    # §7.1 解析
    try:
        givens = parse_puzzle(puzzle_str)
    except ParseError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # §8 givens 静态冲突检测
    try:
        check_given_conflicts(givens, compiled['units'])
    except GivenConflict as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # 求解
    solver = Solver(compiled)
    try:
        solver.initialize(givens)

        if args.count:
            # 枚举所有解
            solutions = _count_solutions(solver)
            print(f"Solutions found: {len(solutions)}")
            if solutions:
                print(f"First solution: {solutions[0]}")
        else:
            found = solver.solve()
            if found:
                print(solver.solution_string())
                print()
                print(solver.solution_grid())
            else:
                print("FAIL: no solution found", file=sys.stderr)
                sys.exit(1)

    except Contradiction as e:
        print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)

    # 统计
    print()
    stats = solver.stats.as_dict()
    print("Stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # 日志
    if args.log:
        print()
        print("Log:")
        for entry in solver.log:
            print(json.dumps({
                'step_id': entry.step_id,
                'depth': entry.depth,
                'reason': entry.reason,
                'cell': cell_name(entry.cell),
                'digit': entry.digit,
                'evidence': entry.evidence,
            }))


def _count_solutions(solver: Solver) -> list[str]:
    """枚举所有解（--count 模式）。"""
    solutions: list[str] = []
    _count_recurse(solver, solutions)
    return solutions


def _count_recurse(solver: Solver, solutions: list[str]) -> None:
    from .solver import domain_size, iter_digits, Contradiction

    # 找未定变量 (MRV, 行优先 tiebreak)
    best_idx = -1
    best_size = 10
    for x in range(81):
        s = domain_size(solver.D[x])
        if s > 1 and s < best_size:
            best_size = s
            best_idx = x

    if best_idx == -1:
        solutions.append(solver.solution_string())
        return

    x = best_idx
    for v in iter_digits(solver.D[x]):
        mark = len(solver.trail)
        old_depth = solver._depth
        solver._depth += 1
        if solver._depth > solver.stats.max_depth:
            solver.stats.max_depth = solver._depth
        solver.stats.guesses += 1

        try:
            solver.assign(x, v, _reason='GUESS',
                          _evidence={'domain_size_before': best_size})
            _count_recurse(solver, solutions)
        except Contradiction:
            pass

        # 回溯
        solver.stats.backtracks += 1
        solver._log('BACKTRACK', x, v,
                     {'failed_value': v, 'depth': solver._depth})
        solver._depth = old_depth
        solver._restore_trail(mark)


if __name__ == '__main__':
    main()
