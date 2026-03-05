"""
输入解析模块：81 字符串 → givens 列表，含校验与 givens 静态冲突检测。

对应 spec §7.1 (输入格式/校验), §8 (givens 静态冲突检测)。
"""

from __future__ import annotations

import re
from typing import NamedTuple

from .compiler import compile_sudoku, cell_name, unit_name


# ---------------------------------------------------------------------------
# 异常类型
# ---------------------------------------------------------------------------

class ParseError(Exception):
    """输入格式错误（字符非法或长度不为 81）。"""
    pass


class GivenConflict(Exception):
    """编译期检测到 givens 之间的静态冲突。"""
    pass


# ---------------------------------------------------------------------------
# Given 结构
# ---------------------------------------------------------------------------

class Given(NamedTuple):
    idx: int    # CellId (0-based linear index)
    digit: int  # 1..9


# ---------------------------------------------------------------------------
# §7.1  合法字符集 [0-9.], 长度 81
# ---------------------------------------------------------------------------
_VALID_PATTERN = re.compile(r'^[0-9.]{81}$')


def parse_puzzle(puzzle: str) -> list[Given]:
    """解析 81 字符输入串，返回 givens 列表（按 idx 升序）。

    校验规则 (§7.1):
      - 合法字符集: [0-9.] (共 11 种字符)
      - 长度恰好 81

    Raises:
        ParseError: 输入不合法
    """
    # 长度检查
    if len(puzzle) != 81:
        raise ParseError(
            f"PARSE_ERROR: input length is {len(puzzle)}, expected 81"
        )
    # 字符集检查
    if not _VALID_PATTERN.match(puzzle):
        bad_chars = sorted(set(ch for ch in puzzle if ch not in '0123456789.'))
        raise ParseError(
            f"PARSE_ERROR: illegal characters: {bad_chars}"
        )

    givens: list[Given] = []
    for idx, ch in enumerate(puzzle):
        if ch not in ('0', '.'):
            givens.append(Given(idx=idx, digit=int(ch)))
    return givens


# ---------------------------------------------------------------------------
# §8  givens 静态冲突检测
# ---------------------------------------------------------------------------

def check_given_conflicts(
    givens: list[Given],
    units: list[list[int]],
) -> None:
    """编译期静态检测 givens 之间是否有同 unit 同 digit 冲突。

    若发现冲突，抛出 GivenConflict 异常（含 1-based 用户友好信息）。
    """
    # 为每个 unit 建立 digit → cell 映射
    # 先建 cell → digit 查找表
    cell_digit: dict[int, int] = {g.idx: g.digit for g in givens}

    for uid, unit_cells in enumerate(units):
        # 该 unit 中已有 given 的 (digit → cell_idx)
        seen: dict[int, int] = {}
        for x in unit_cells:
            if x in cell_digit:
                d = cell_digit[x]
                if d in seen:
                    x1 = seen[d]
                    raise GivenConflict(
                        f"GIVEN_CONFLICT: {cell_name(x1)}={d} == "
                        f"{cell_name(x)}={d} in {unit_name(uid)}"
                    )
                seen[d] = x
