"""
传播引擎：ASSIGN / ELIMINATE 互递归 + trail 回溯。

对应 spec §3.0 (bitmask), §3.1 (域), §3.3 (Count), §3.4 (初始化),
§4.0 (原子操作), §4.1–4.3 (传播语义), §5 (回溯 trail 恢复)。
"""

from __future__ import annotations

import sys
from typing import NamedTuple

from .compiler import cell_name, unit_name

# §0.2 递归限制
sys.setrecursionlimit(2000)


# ---------------------------------------------------------------------------
# §3.0  位掩码域操作
# ---------------------------------------------------------------------------

FULL_DOMAIN = 0x1FF  # 9 bit 全 1, 即 {1..9}


def has_digit(domain: int, d: int) -> bool:
    """检查 digit d (1..9) 是否在域中。"""
    return bool(domain & (1 << (d - 1)))


def remove_digit(domain: int, d: int) -> int:
    """从域中移除 digit d。"""
    return domain & ~(1 << (d - 1))


def domain_size(domain: int) -> int:
    """域中元素个数 = popcount。"""
    return bin(domain).count('1')


def single_digit(domain: int) -> int:
    """域恰好为单点时，返回该 digit (1..9)。"""
    # bit_length 给出最高位位置 (1-indexed)
    return domain.bit_length()


def iter_digits(domain: int):
    """迭代域中所有 digit (1..9)，按升序。"""
    for d in range(1, 10):
        if domain & (1 << (d - 1)):
            yield d


# ---------------------------------------------------------------------------
# 异常
# ---------------------------------------------------------------------------

class Contradiction(Exception):
    """传播过程中检测到矛盾（域空或 unit 中 digit 无候选位置）。

    属性:
        cell: 可选，引发矛盾的 CellId
        unit: 可选，引发矛盾的 UnitId
        digit: 可选，涉及的 digit
    """
    def __init__(self, *, cell: int | None = None,
                 unit: int | None = None, digit: int | None = None):
        self.cell = cell
        self.unit = unit
        self.digit = digit
        parts = []
        if cell is not None:
            parts.append(f"cell={cell_name(cell)}")
        if unit is not None:
            parts.append(f"unit={unit_name(unit)}")
        if digit is not None:
            parts.append(f"digit={digit}")
        super().__init__(f"Contradiction({', '.join(parts)})")


# ---------------------------------------------------------------------------
# Trail
# ---------------------------------------------------------------------------

class TrailEntry(NamedTuple):
    var: int    # CellId
    digit: int  # 被移除的 digit


# ---------------------------------------------------------------------------
# §6  LogEntry + ReasonType + Stats
# ---------------------------------------------------------------------------

class LogEntry(NamedTuple):
    step_id: int
    depth: int
    reason: str         # ReasonType 字符串
    cell: int           # CellId
    digit: int
    evidence: dict


class Stats:
    __slots__ = ('eliminations', 'assignments', 'guesses', 'backtracks', 'max_depth')

    def __init__(self):
        self.eliminations = 0
        self.assignments = 0
        self.guesses = 0
        self.backtracks = 0
        self.max_depth = 0

    def as_dict(self) -> dict:
        return {
            'eliminations': self.eliminations,
            'assignments': self.assignments,
            'guesses': self.guesses,
            'backtracks': self.backtracks,
            'max_depth': self.max_depth,
        }


# ---------------------------------------------------------------------------
# 求解器状态
# ---------------------------------------------------------------------------

class Solver:
    """Fibered-CSP Sudoku 求解器 v0.1。"""

    def __init__(self, compiled: dict):
        """
        Args:
            compiled: compile_sudoku() 的返回值
        """
        self.units: list[list[int]] = compiled['units']
        self.cells_of: list[list[int]] = compiled['cells_of']
        self.units_of: list[list[int]] = compiled['units_of']
        self.peers: list[set[int]] = compiled['peers']

        # §3.1 域: D[x] = bitmask
        self.D: list[int] = [FULL_DOMAIN] * 81

        # §3.3 Count[U][d]: digit d 在 unit U 中的候选位置计数
        # Count[uid][d-1] (0-indexed digit offset)
        self.count: list[list[int]] = [[9] * 9 for _ in range(27)]

        # Trail
        self.trail: list[TrailEntry] = []

        # 日志
        self.log: list[LogEntry] = []
        self._step_counter: int = 0
        self._depth: int = 0

        # 统计
        self.stats = Stats()

    # -----------------------------------------------------------------------
    # 日志辅助
    # -----------------------------------------------------------------------
    def _log(self, reason: str, cell: int, digit: int, evidence: dict) -> None:
        self._step_counter += 1
        self.log.append(LogEntry(
            step_id=self._step_counter,
            depth=self._depth,
            reason=reason,
            cell=cell,
            digit=digit,
            evidence=evidence,
        ))

    # -----------------------------------------------------------------------
    # §4.0  ELIMINATE
    # -----------------------------------------------------------------------
    def eliminate(self, x: int, d: int, *, _reason: str = 'PAIR_ELIMINATE',
                  _evidence: dict | None = None) -> None:
        """从 D[x] 中移除 digit d。级联触发 Count 更新、Hidden Single、Naked Single。"""
        self.stats.eliminations += 1

        # 幂等: 已删则跳过
        if not has_digit(self.D[x], d):
            return

        # 移除
        self.D[x] = remove_digit(self.D[x], d)
        self.trail.append(TrailEntry(var=x, digit=d))

        # 日志: 记录本次删值
        self._log(_reason, x, d, _evidence or {})

        # 域空 → 矛盾
        if self.D[x] == 0:
            raise Contradiction(cell=x)

        # --- Unit 层: 增量 Hidden Single 检测 ---
        # Phase 1: 先递减所有 unit 的 Count（保证 Count 与域同步）
        for uid in self.units_of[x]:
            self.count[uid][d - 1] -= 1

        # Phase 2: 检查矛盾与 Hidden Single（此时 Count 已准确反映 d 从 D[x] 移除）
        for uid in self.units_of[x]:
            c = self.count[uid][d - 1]

            if c == 0:
                raise Contradiction(unit=uid, digit=d)

            if c == 1:
                # 线性扫描找唯一候选
                candidates = [y for y in self.cells_of[uid]
                              if has_digit(self.D[y], d)]
                assert len(candidates) == 1, (
                    f"Count desync: Count[{unit_name(uid)}][{d}]==1 "
                    f"but found {len(candidates)} candidates"
                )
                y = candidates[0]
                # Hidden Single: y 必须取 d
                self.assign(y, d, _reason='HIDDEN_SINGLE',
                            _evidence={'unit': uid, 'digit': d})

        # --- Naked Single 检测 ---
        if domain_size(self.D[x]) == 1:
            d_last = single_digit(self.D[x])
            self.assign(x, d_last, _reason='NAKED_SINGLE',
                        _evidence={'remaining_digit': d_last})

    # -----------------------------------------------------------------------
    # §4.0  ASSIGN
    # -----------------------------------------------------------------------
    def assign(self, x: int, d: int, *, _reason: str = 'GIVEN',
               _evidence: dict | None = None) -> None:
        """确定 x 的值为 d。"""
        self.stats.assignments += 1

        # 入口 guard
        if not has_digit(self.D[x], d):
            raise Contradiction(cell=x, digit=d)

        # 注意：此处曾有 `if D[x] == {d}: return` 优化，但已移除。
        # 原因：当 Naked Single 从 **peer 的传播链** 首次触发 ASSIGN(x, d) 时，
        # D[x] 已是 {d}（ELIMINATE 刚缩到单点），但 peers 从未被告知删除 d。
        # 早返回会跳过 peer 传播，违反 ASSIGN 后置条件 "所有 peer 域中不含 d"。
        # 仅当存在 **外层** ASSIGN(x, d)（如 ASSIGN 自身内循环触发的 Naked Single）
        # 时早返回才安全——但运行时无法廉价区分这两种情况。

        # 日志: 记录赋值事件 (仅 GIVEN/HIDDEN_SINGLE/NAKED_SINGLE/GUESS 会带有原因)
        if _reason in ('GIVEN', 'HIDDEN_SINGLE', 'NAKED_SINGLE', 'GUESS'):
            self._log(_reason, x, d, _evidence or {})

        # --- 缩域到单点 (委托给 ELIMINATE) ---
        for dp in range(1, 10):
            if dp != d and has_digit(self.D[x], dp):
                self.eliminate(x, dp,
                               _reason='PAIR_ELIMINATE',
                               _evidence={'trigger': x, 'trigger_digit': d})

        # --- Pair 层: neq 传播 ---
        for y in self.peers[x]:
            self.eliminate(y, d,
                           _reason='PAIR_ELIMINATE',
                           _evidence={'trigger': x, 'trigger_digit': d})

    # -----------------------------------------------------------------------
    # §3.4 初始化
    # -----------------------------------------------------------------------
    def initialize(self, givens: list) -> None:
        """按行优先顺序处理 givens，调用 ASSIGN 完成初始传播。

        Args:
            givens: parser.Given 列表（已按 idx 升序排列）
        """
        for g in givens:
            self.assign(g.idx, g.digit, _reason='GIVEN', _evidence={})

    # -----------------------------------------------------------------------
    # §5 搜索: MRV + trail 回溯
    # -----------------------------------------------------------------------
    def solve(self) -> bool:
        """在当前传播不动点上执行搜索。返回 True 若找到解。"""

        # 找未定变量 (|D[x]| > 1)，MRV 选择
        best_idx = -1
        best_size = 10  # > 9
        for x in range(81):
            s = domain_size(self.D[x])
            if s > 1 and s < best_size:
                best_size = s
                best_idx = x
            # s == 0 不应出现（会在传播中抛 Contradiction）

        if best_idx == -1:
            # 所有变量已定 → 解
            return True

        # 升序遍历域中的 digit
        x = best_idx
        for v in iter_digits(self.D[x]):
            # 记录 trail 分界点
            mark = len(self.trail)
            old_depth = self._depth
            self._depth += 1
            if self._depth > self.stats.max_depth:
                self.stats.max_depth = self._depth
            self.stats.guesses += 1

            try:
                self.assign(x, v, _reason='GUESS', _evidence={'domain_size_before': best_size})
                if self.solve():
                    return True
            except Contradiction:
                pass

            # 回溯: 恢复 trail 到 mark
            self.stats.backtracks += 1
            self._log('BACKTRACK', x, v, {'failed_value': v, 'depth': self._depth})
            self._depth = old_depth
            self._restore_trail(mark)

        # 所有值都失败
        raise Contradiction(cell=x)

    def _restore_trail(self, mark: int) -> None:
        """按 trail 从当前位置逆序恢复到 mark。"""
        while len(self.trail) > mark:
            entry = self.trail.pop()
            y, dp = entry.var, entry.digit
            # 恢复域
            self.D[y] |= (1 << (dp - 1))
            # 恢复 Count
            for uid in self.units_of[y]:
                self.count[uid][dp - 1] += 1

    # -----------------------------------------------------------------------
    # §7.2 输出
    # -----------------------------------------------------------------------
    def solution_string(self) -> str:
        """返回 81 字符解字符串。"""
        chars = []
        for x in range(81):
            if domain_size(self.D[x]) == 1:
                chars.append(str(single_digit(self.D[x])))
            else:
                chars.append('0')
        return ''.join(chars)

    def solution_grid(self) -> str:
        """返回 9×9 网格字符串。"""
        sol = self.solution_string()
        lines = []
        for r in range(9):
            row = ' '.join(sol[r * 9 + c] for c in range(9))
            lines.append(row)
        return '\n'.join(lines)
