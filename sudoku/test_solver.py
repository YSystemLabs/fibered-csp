"""
Fibered-CSP Sudoku Solver v0.1 — pytest 测试套件。

对应 spec §8.1 参考测试用例 T1–T4。
"""

import pytest

from sudoku.compiler import compile_sudoku
from sudoku.parser import parse_puzzle, check_given_conflicts, ParseError, GivenConflict
from sudoku.solver import Solver, Contradiction


# ---------------------------------------------------------------------------
# 编译产物（所有测试共用，只生成一次）
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def compiled():
    return compile_sudoku()


# ---------------------------------------------------------------------------
# 编译模块测试
# ---------------------------------------------------------------------------

class TestCompiler:

    def test_unit_count(self, compiled):
        """应生成 27 个 unit。"""
        assert len(compiled['units']) == 27

    def test_pair_count(self, compiled):
        """去重后 neq 数量应恰好 810。"""
        assert compiled['pair_count'] == 810

    def test_peers_size(self, compiled):
        """每个 cell 应有 20 个 peer。"""
        for x in range(81):
            assert len(compiled['peers'][x]) == 20

    def test_units_of_size(self, compiled):
        """每个 cell 应属于 3 个 unit。"""
        for x in range(81):
            assert len(compiled['units_of'][x]) == 3


# ---------------------------------------------------------------------------
# 输入解析测试
# ---------------------------------------------------------------------------

class TestParser:

    def test_valid_input(self):
        givens = parse_puzzle(
            '53..7....6..195....98....6.8...6...34..8.3..17...2...6'
            '.6....28....419..5....8..79'
        )
        assert len(givens) == 30

    def test_zeros_and_dots(self):
        """0 和 . 都应被视为空格。"""
        g1 = parse_puzzle('5300700006001950000980000608000600034008030017000200060600002800004190050000800' + '79')
        g2 = parse_puzzle('53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79')
        # 两者的 given 数量相同（0 和 . 都是空格）
        assert len(g1) == len(g2)

    def test_bad_length(self):
        with pytest.raises(ParseError, match='PARSE_ERROR.*length'):
            parse_puzzle('123')

    def test_bad_chars(self):
        with pytest.raises(ParseError, match='PARSE_ERROR.*illegal'):
            parse_puzzle('X' * 81)

    def test_given_conflict(self, compiled):
        """T4: Cell[1,1]=1 与 Cell[1,2]=1 同 Row 冲突。"""
        givens = parse_puzzle('11' + '.' * 79)
        with pytest.raises(GivenConflict, match='GIVEN_CONFLICT.*Cell\\[1,1\\].*Cell\\[1,2\\].*Row 1'):
            check_given_conflicts(givens, compiled['units'])


# ---------------------------------------------------------------------------
# §8.1 参考测试用例
# ---------------------------------------------------------------------------

class TestSolve:

    def _solve(self, compiled, puzzle: str) -> Solver:
        givens = parse_puzzle(puzzle)
        check_given_conflicts(givens, compiled['units'])
        solver = Solver(compiled)
        solver.initialize(givens)
        solver.solve()
        return solver

    def test_t1_easy(self, compiled):
        """T1: Easy — 纯传播可解，guesses == 0。"""
        solver = self._solve(
            compiled,
            '53..7....6..195....98....6.8...6...34..8.3..17...2...6'
            '.6....28....419..5....8..79'
        )
        sol = solver.solution_string()
        assert len(sol) == 81
        assert '0' not in sol
        assert solver.stats.guesses == 0

    def test_t1_known_solution(self, compiled):
        """T1: 验证解的正确性。"""
        solver = self._solve(
            compiled,
            '53..7....6..195....98....6.8...6...34..8.3..17...2...6'
            '.6....28....419..5....8..79'
        )
        expected = (
            '534678912672195348198342567859761423'
            '426853791713924856961537284287419635345286179'
        )
        assert solver.solution_string() == expected

    def test_t2_medium(self, compiled):
        """T2: Medium — 需搜索，guesses > 0。"""
        solver = self._solve(
            compiled,
            '..9748...7.........2.1.9.....7...24..64.1.59..98...3.'
            '....8.3.2.........6...2759..'
        )
        sol = solver.solution_string()
        assert len(sol) == 81
        assert '0' not in sol
        assert solver.stats.guesses > 0

    def test_t3_contradiction(self, compiled):
        """T3: 矛盾 — 最后一位改为 1，与同列已有 1 冲突。
        静态冲突检测会在编译期捕获（Cell[5,9]=1 与 Cell[9,9]=1 同属 Col 9）。
        """
        givens = parse_puzzle(
            '53..7....6..195....98....6.8...6...34..8.3..17...2...6'
            '.6....28....419..5....8..71'
        )
        with pytest.raises(GivenConflict, match='Col 9'):
            check_given_conflicts(givens, compiled['units'])

    def test_t4_given_conflict(self, compiled):
        """T4: Givens 冲突 — Cell[1,1]=1 与 Cell[1,2]=1。"""
        givens = parse_puzzle('11' + '.' * 79)
        with pytest.raises(GivenConflict):
            check_given_conflicts(givens, compiled['units'])


# ---------------------------------------------------------------------------
# 传播引擎属性测试
# ---------------------------------------------------------------------------

class TestPropagationProperties:

    def test_solution_validity(self, compiled):
        """解满足所有 unit 约束 (all-different)。"""
        solver = Solver(compiled)
        solver.initialize(parse_puzzle(
            '53..7....6..195....98....6.8...6...34..8.3..17...2...6'
            '.6....28....419..5....8..79'
        ))
        solver.solve()
        sol = solver.solution_string()

        # 每个 unit 中 9 个 digit 各出现恰好一次
        for unit_cells in compiled['units']:
            digits = [int(sol[x]) for x in unit_cells]
            assert sorted(digits) == list(range(1, 10))

    def test_trail_restore(self, compiled):
        """回溯恢复后域应与初始传播后一致。"""
        from sudoku.solver import domain_size

        solver = Solver(compiled)
        puzzle = '..9748...7.........2.1.9.....7...24..64.1.59..98...3.....8.3.2.........6...2759..'
        solver.initialize(parse_puzzle(puzzle))

        # 记录初始传播后的域快照
        snapshot_d = solver.D[:]
        snapshot_count = [row[:] for row in solver.count]
        mark = len(solver.trail)

        # 找第一个未定变量，做一次 guess
        for x in range(81):
            if domain_size(solver.D[x]) > 1:
                from sudoku.solver import iter_digits
                d = next(iter_digits(solver.D[x]))
                try:
                    solver.assign(x, d, _reason='GUESS', _evidence={})
                except Contradiction:
                    pass
                break

        # 回溯
        solver._restore_trail(mark)

        # 验证域恢复
        assert solver.D == snapshot_d
        # 验证 Count 恢复
        assert solver.count == snapshot_count
