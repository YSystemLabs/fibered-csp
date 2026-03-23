"""RGB 模式专项测试。

验证 generate_targets、constraints、scoring、search 在 channels=3 时的正确性。
"""

import numpy as np
import pytest

from engine.search import (
    generate_targets,
    compute_basic_domain,
    fill_from_basic_domain,
    simulated_annealing,
    _pair_cost,
    _incremental_delta,
    _t_to_rgb,
)
from engine.constraints import (
    pixel_preferences,
    region_costs,
    symmetry_check,
    SymmetryType,
)
from engine.scoring import compute_scores


# ═══ generate_targets RGB ═══════════════════════════════════

class TestGenerateTargetsRGB:
    """测试 6 种模式的 RGB 目标生成。"""

    @pytest.fixture
    def rng(self):
        return np.random.default_rng(42)

    @pytest.mark.parametrize("mode", [
        "random_uniform", "random_smooth", "gradient_h",
        "gradient_v", "checkerboard", "center_blob",
    ])
    def test_shape_and_range(self, rng, mode):
        H, W, L = 8, 8, 8
        result = generate_targets(H, W, L, mode, rng, channels=3)
        assert result.shape == (H, W, 3)
        assert result.dtype == int
        assert np.all(result >= 0)
        assert np.all(result < L)

    def test_gradient_h_rgb_varies_across_cols(self, rng):
        result = generate_targets(8, 16, 8, "gradient_h", rng, channels=3)
        # 列间应有变化
        diffs = np.sum(np.abs(np.diff(result, axis=1)), axis=-1)
        assert np.sum(diffs) > 0

    def test_checkerboard_rgb_two_colors(self, rng):
        result = generate_targets(8, 8, 8, "checkerboard", rng, channels=3)
        c00 = tuple(result[0, 0])
        c01 = tuple(result[0, 1])
        # 棋盘格应只有两种颜色
        unique = set()
        for i in range(8):
            for j in range(8):
                unique.add(tuple(result[i, j]))
        assert len(unique) == 2
        assert c00 != c01

    def test_channels_default_is_grayscale(self, rng):
        result = generate_targets(8, 8, 8, "random_uniform", rng)
        assert result.ndim == 2
        assert result.shape == (8, 8)


# ═══ _t_to_rgb 帮助函数 ═══════════════════════════════════

class TestTToRGB:
    def test_endpoints(self):
        L = 8
        # t=0: cos(0)=1 → R=(L-1), cos(-2π/3)=cos(2π/3)=-0.5 → G=0, B=0
        r0 = _t_to_rgb(np.array([0.0]), L)
        assert r0.shape == (1, 3)
        assert r0[0, 0] == L - 1  # R = max at t=0

    def test_output_range(self):
        t = np.linspace(0, 1, 100)
        rgb = _t_to_rgb(t, 16)
        assert np.all(rgb >= 0)
        assert np.all(rgb < 16)


# ═══ Constraints RGB 兼容 ═══════════════════════════════════

class TestConstraintsRGB:
    def test_pixel_preferences_rgb(self):
        img = np.array([[[3, 5, 2], [1, 1, 1]]], dtype=int)
        tgt = np.array([[[3, 5, 2], [7, 7, 7]]], dtype=int)
        prefs = pixel_preferences(img, tgt, 0.3, 8)
        assert prefs.shape == (1, 2)
        # 完全匹配的像素偏好应接近 1.0
        assert prefs[0, 0] == pytest.approx(1.0, abs=1e-6)
        # 不匹配的较低
        assert prefs[0, 1] < prefs[0, 0]

    def test_region_costs_rgb(self):
        img = np.zeros((4, 4, 3), dtype=int)
        img[:, 2:] = 7  # 右半设为 [7,7,7]
        total, hmap, C_H, C_V = region_costs(img, 0.3, 5.0, 10.0, 8)
        assert total > 0
        assert hmap.shape == (4, 4)
        assert C_H > 0  # 水平方向有跳变

    def test_symmetry_check_rgb(self):
        img = np.zeros((4, 6, 3), dtype=int)
        img[0, 0] = [1, 2, 3]
        img[0, 5] = [1, 2, 3]
        img[1, 1] = [4, 5, 6]
        img[1, 4] = [4, 5, 6]
        img[2, 1] = [4, 5, 6]
        img[2, 4] = [4, 5, 6]
        img[3, 0] = [1, 2, 3]
        img[3, 5] = [1, 2, 3]
        assert symmetry_check(img, [SymmetryType.LEFT_RIGHT], 0.0)


# ═══ _pair_cost 向量支持 ═══════════════════════════════════

class TestPairCost:
    def test_scalar_backward_compat(self):
        # 标量：与旧 _pair_cost_scalar 行为一致
        cost = _pair_cost(2, 5, 0.3, 5.0, 10.0, 7.0, 1.0)
        d = abs(2 - 5) / 7.0  # ≈ 0.4286 > tau=0.3
        expected = 5.0 * d * 1.0
        assert cost == pytest.approx(expected, rel=1e-10)

    def test_vector_euclidean(self):
        v1 = np.array([3, 0, 0])
        v2 = np.array([0, 4, 0])
        norm = 7.0
        d = np.sqrt(9 + 16) / 7.0  # 5/7 ≈ 0.714 > tau
        cost = _pair_cost(v1, v2, 0.3, 5.0, 10.0, norm, 1.0)
        expected = 5.0 * d * 1.0
        assert cost == pytest.approx(expected, rel=1e-10)

    def test_identical_vectors_zero_cost(self):
        v = np.array([3, 5, 2])
        cost = _pair_cost(v, v, 0.3, 5.0, 10.0, 7.0, 1.0)
        assert cost == pytest.approx(0.0)


# ═══ Scoring RGB ═══════════════════════════════════════════

class TestScoringRGB:
    def test_compute_scores_rgb(self):
        img = np.random.default_rng(0).integers(0, 8, size=(4, 4, 3))
        tgt = np.random.default_rng(1).integers(0, 8, size=(4, 4, 3))
        params = {
            "alpha": 0.5, "K": 255.0, "sigma": 0.3, "levels": 8,
            "tau": 0.3, "beta": 5.0, "gamma": 10.0,
            "dir_strength": 0.0, "dir_angle": 0.0,
            "symmetry": ["none"], "epsilon": 0.0, "translate_period": 4,
        }
        scores = compute_scores(img, tgt, params)
        assert scores.dir_pixel < 0  # log 域，负值
        assert scores.dir_region >= 0
        assert scores.region_heatmap.shape == (4, 4)


# ═══ Incremental Delta RGB ═══════════════════════════════════

class TestIncrementalDeltaRGB:
    def test_matches_full_recompute(self):
        rng = np.random.default_rng(42)
        img = rng.integers(0, 8, size=(4, 4, 3))
        tgt = rng.integers(0, 8, size=(4, 4, 3))
        params = {
            "alpha": 0.5, "K": 255.0, "sigma": 0.3, "levels": 8,
            "tau": 0.3, "beta": 5.0, "gamma": 10.0,
            "dir_strength": 0.0, "dir_angle": 0.0,
            "symmetry": ["none"], "epsilon": 0.0, "translate_period": 4,
        }

        # 全量评分 before
        sc_before = compute_scores(img, tgt, params)

        # 变更一个像素
        new_val = np.array([1, 6, 3])
        changes = [(1, 2, new_val)]
        d_pix, d_reg = _incremental_delta(
            img, changes, tgt, 0.3, 0.3, 5.0, 10.0, 8, 0.0, 0.0,
        )

        # 应用变更
        img2 = img.copy()
        img2[1, 2] = new_val
        sc_after = compute_scores(img2, tgt, params)

        assert d_pix == pytest.approx(sc_after.dir_pixel - sc_before.dir_pixel, abs=1e-8)
        assert d_reg == pytest.approx(sc_after.dir_region - sc_before.dir_region, abs=1e-8)


# ═══ fill_from_basic_domain RGB ═══════════════════════════════

class TestFillRGB:
    def test_lr_symmetry_fill(self):
        H, W = 4, 6
        bd, om = compute_basic_domain(H, W, [SymmetryType.LEFT_RIGHT], 4)
        img = np.zeros((H, W, 3), dtype=int)
        rng = np.random.default_rng(7)
        for bi, bj in bd:
            img[bi, bj] = rng.integers(0, 8, size=3)
        fill_from_basic_domain(img, om, 0.0, 8)
        # 验证左右对称
        for i in range(H):
            for j in range(W):
                np.testing.assert_array_equal(img[i, j], img[i, W - 1 - j])


# ═══ SA 端到端 RGB ═══════════════════════════════════════════

class TestSARGB:
    def test_sa_rgb_runs(self):
        """RGB 模式下 SA 能正常运行并返回 3D 图像。"""
        rng = np.random.default_rng(42)
        H, W, L = 4, 4, 8
        targets = generate_targets(H, W, L, "random_smooth", rng, channels=3)
        params = {
            "alpha": 0.5, "K": 255, "sigma": 0.3,
            "tau": 0.3, "beta": 5.0, "gamma": 10.0,
            "dir_strength": 0.0, "dir_angle": 0.0,
            "symmetry": ["none"], "epsilon": 0.0, "translate_period": 4,
        }
        img, scores = simulated_annealing(
            H, W, targets, params,
            levels=L, max_iter=500, seed=42,
        )
        assert img.shape == (H, W, 3)
        assert img.dtype == int
        assert np.all(img >= 0)
        assert np.all(img < L)
        assert scores.dir_pixel < 0

    def test_sa_rgb_with_symmetry(self):
        """RGB + LR 对称。"""
        rng = np.random.default_rng(99)
        H, W, L = 4, 6, 8
        targets = generate_targets(H, W, L, "gradient_h", rng, channels=3)
        params = {
            "alpha": 0.5, "K": 255, "sigma": 0.3,
            "tau": 0.3, "beta": 5.0, "gamma": 10.0,
            "dir_strength": 0.0, "dir_angle": 0.0,
            "symmetry": ["lr"], "epsilon": 0.0, "translate_period": 4,
        }
        img, _ = simulated_annealing(
            H, W, targets, params,
            levels=L, max_iter=500, seed=99,
        )
        assert img.shape == (H, W, 3)
        # 检查左右对称
        for i in range(H):
            for j in range(W):
                np.testing.assert_array_equal(img[i, j], img[i, W - 1 - j])

    def test_sa_rgb_deterministic(self):
        """同 seed 两次运行应产生相同结果。"""
        rng1 = np.random.default_rng(77)
        rng2 = np.random.default_rng(77)
        H, W, L = 4, 4, 8
        t1 = generate_targets(H, W, L, "random_uniform", rng1, channels=3)
        t2 = generate_targets(H, W, L, "random_uniform", rng2, channels=3)
        params = {
            "alpha": 0.5, "K": 255, "sigma": 0.3,
            "tau": 0.3, "beta": 5.0, "gamma": 10.0,
            "dir_strength": 0.0, "dir_angle": 0.0,
            "symmetry": ["none"], "epsilon": 0.0, "translate_period": 4,
        }
        img1, _ = simulated_annealing(H, W, t1, params, levels=L, max_iter=300, seed=77)
        img2, _ = simulated_annealing(H, W, t2, params, levels=L, max_iter=300, seed=77)
        np.testing.assert_array_equal(img1, img2)
