"""
编译模块：固定生成 Sudoku 9×9 的 units / Peers / CellsOf / UnitsOf。

对应 spec §3.0–§3.3, §2.1, §7.1 (编译退化说明), §8 (810 硬断言)。

v0.1 的"路线 A 编译"在 Sudoku 特化下退化为固定生成——
硬编码 27 个 unit、Peers[x]（每 cell 20 个 peer）、810 条 neq 断言。
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# §3.0  CellId: 行优先线性索引 idx = r * 9 + c, r,c ∈ {0..8}
# ---------------------------------------------------------------------------

def cell_name(idx: int) -> str:
    """将内部 0-based idx 转为用户可读的 1-based Cell[r,c] 表示。"""
    r, c = divmod(idx, 9)
    return f"Cell[{r + 1},{c + 1}]"


def unit_name(uid: int) -> str:
    """将内部 0-based UnitId 转为用户可读名称。
    UnitId 编号: Row 0..8 → Col 0..8 → Box 0..8 (共 27)。
    """
    if uid < 9:
        return f"Row {uid + 1}"
    elif uid < 18:
        return f"Col {uid - 9 + 1}"
    else:
        box_idx = uid - 18
        br, bc = divmod(box_idx, 3)
        return f"Box({br + 1},{bc + 1})"


# ---------------------------------------------------------------------------
# §3.3  辅助结构（预计算）
# ---------------------------------------------------------------------------

def compile_sudoku() -> dict:
    """固定生成 Sudoku 9×9 的全部编译产物。

    返回 dict 包含:
        units       : list[list[int]]  — 27 个 unit，每个包含 9 个 CellId
        cells_of    : list[list[int]]  — 同 units（别名，语义更清晰）
        units_of    : list[list[int]]  — units_of[x] = 包含 x 的 unit id 列表 (长度 3)
        peers       : list[set[int]]   — peers[x] = 与 x 同行/同列/同宫的 cell 集合 (大小 20)
        pair_count  : int              — 去重后 neq 对数 (应恰好 810)
    """

    # --- 生成 27 个 unit ---
    # §3.0 UnitId: Row 0..8 → Col 0..8 → Box 0..8
    units: list[list[int]] = []

    # Row units (uid 0..8)
    for r in range(9):
        units.append([r * 9 + c for c in range(9)])

    # Col units (uid 9..17)
    for c in range(9):
        units.append([r * 9 + c for r in range(9)])

    # Box units (uid 18..26)
    # §1.1: Box[br,bc], br/bc ∈ {0,1,2}
    # box_idx = br * 3 + bc, uid = 18 + box_idx
    for br in range(3):
        for bc in range(3):
            cells = []
            for i in range(3):
                for j in range(3):
                    r = 3 * br + i
                    c = 3 * bc + j
                    cells.append(r * 9 + c)
            units.append(cells)

    assert len(units) == 27, f"Expected 27 units, got {len(units)}"

    # --- units_of[x]: 包含 x 的 unit 列表 ---
    units_of: list[list[int]] = [[] for _ in range(81)]
    for uid, unit_cells in enumerate(units):
        for x in unit_cells:
            units_of[x].append(uid)
    # 每个 cell 恰好属于 3 个 unit (1 Row + 1 Col + 1 Box)
    for x in range(81):
        assert len(units_of[x]) == 3, (
            f"{cell_name(x)} belongs to {len(units_of[x])} units, expected 3"
        )

    # --- peers[x]: 与 x 同 unit 的所有其他 cell ---
    peers: list[set[int]] = [set() for _ in range(81)]
    for x in range(81):
        for uid in units_of[x]:
            for y in units[uid]:
                if y != x:
                    peers[x].add(y)
    # 每个 cell 恰好有 20 个 peer
    for x in range(81):
        assert len(peers[x]) == 20, (
            f"{cell_name(x)} has {len(peers[x])} peers, expected 20"
        )

    # --- §2.1 派生 PairConstraints 并验证 810 硬断言 ---
    # 去重使用规范化无序对 (min(x,y), max(x,y))
    pair_set: set[tuple[int, int]] = set()
    for uid, unit_cells in enumerate(units):
        n = len(unit_cells)
        for i in range(n):
            for j in range(i + 1, n):
                x, y = unit_cells[i], unit_cells[j]
                pair_set.add((min(x, y), max(x, y)))

    pair_count = len(pair_set)
    # §8 硬断言: 去重后 neq 数量必须恰好 810
    assert pair_count == 810, (
        f"Derived {pair_count} neq pairs, expected 810. Compiler bug!"
    )

    return {
        "units": units,
        "cells_of": units,        # 别名
        "units_of": units_of,
        "peers": peers,
        "pair_count": pair_count,
    }
