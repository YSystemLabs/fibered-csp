"""engine/search.py 单元测试。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest

from engine.search import (
    generate_targets,
    compute_basic_domain,
    fill_from_basic_domain,
    _incremental_delta,
    _direction_weights,
    simulated_annealing,
)
from engine.constraints import SymmetryType, region_costs, pixel_preferences
from engine.fibers import PROB_EPS, f1_shriek_from_log, f1_star_log


# ═══════════════════════════════════════════════════════════════════
# §4.4.4 目标色生成
# ═══════════════════════════════════════════════════════════════════

class TestGenerateTargets:
    """目标色生成策略正确性。"""

    @pytest.mark.parametrize("mode", [
        "random_uniform", "random_smooth", "gradient_h",
        "gradient_v", "checkerboard", "center_blob",
    ])
    def test_shape_and_range(self, mode):
        """每种模式生成正确形状和值域。"""
        H, W, L = 16, 16, 8
        rng = np.random.default_rng(42)
        t = generate_targets(H, W, L, mode, rng)
        assert t.shape == (H, W)
        assert t.min() >= 0
        assert t.max() <= L - 1

    def test_gradient_h_monotonic(self):
        """水平渐变在同一行单调不减。"""
        t = generate_targets(8, 16, 8, "gradient_h", np.random.default_rng(0))
        for row in t:
            assert all(row[i] <= row[i + 1] for i in range(len(row) - 1))

    def test_gradient_v_monotonic(self):
        """垂直渐变在同一列单调不减。"""
        t = generate_targets(16, 8, 8, "gradient_v", np.random.default_rng(0))
        for j in range(8):
            col = t[:, j]
            assert all(col[i] <= col[i + 1] for i in range(len(col) - 1))

    def test_checkerboard_alternates(self):
        """棋盘格在相邻位置交替 0 / (L-1)。"""
        t = generate_targets(8, 8, 8, "checkerboard", np.random.default_rng(0))
        for i in range(8):
            for j in range(8):
                expected = ((i + j) % 2) * 7
                assert t[i, j] == expected

    def test_center_blob_peak(self):
        """中心斑最大值在图像中央附近。"""
        t = generate_targets(16, 16, 8, "center_blob", np.random.default_rng(0))
        # 中心 2x2 区域应包含最大值
        center = t[7:9, 7:9]
        assert center.max() == t.max()

    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError, match="Unknown target mode"):
            generate_targets(8, 8, 8, "nonexistent", np.random.default_rng(0))


# ═══════════════════════════════════════════════════════════════════
# §4.4.2 基本域和轨道
# ═══════════════════════════════════════════════════════════════════

class TestBasicDomain:
    """对称约束消元——基本域计算。"""

    def test_none_full_image(self):
        """无对称：基本域 = 全图。"""
        bd, om = compute_basic_domain(4, 4, [SymmetryType.NONE])
        assert len(bd) == 16
        # 每个轨道只有 1 个元素
        for orbit in om.values():
            assert len(orbit) == 1

    def test_lr_half(self):
        """左右对称：基本域 ≈ H × ⌈W/2⌉。"""
        H, W = 4, 8
        bd, om = compute_basic_domain(H, W, [SymmetryType.LEFT_RIGHT])
        assert len(bd) == H * (W // 2)  # 4 * 4 = 16
        # 每个轨道大小为 2（中轴无重合时）
        for orbit in om.values():
            assert len(orbit) == 2

    def test_lr_odd_width(self):
        """左右对称 + 奇数宽：中轴像素轨道大小为 1。"""
        H, W = 4, 5
        bd, om = compute_basic_domain(H, W, [SymmetryType.LEFT_RIGHT])
        # 中轴列 j=2 的像素自身是不动点
        sizes = [len(o) for o in om.values()]
        assert 1 in sizes  # 存在大小为 1 的轨道

    def test_ud_half(self):
        """上下对称：基本域 ≈ ⌈H/2⌉ × W。"""
        H, W = 8, 4
        bd, om = compute_basic_domain(H, W, [SymmetryType.UP_DOWN])
        assert len(bd) == (H // 2) * W  # 4 * 4 = 16

    def test_quad_quarter(self):
        """四重对称：基本域 ≈ ⌈H/2⌉ × ⌈W/2⌉。"""
        H, W = 8, 8
        bd, om = compute_basic_domain(H, W, [SymmetryType.QUAD])
        assert len(bd) == (H // 2) * (W // 2)  # 4 * 4 = 16

    def test_c4_approx_quarter(self):
        """C4 旋转：基本域 ≈ N²/4。"""
        N = 8
        bd, om = compute_basic_domain(N, N, [SymmetryType.ROTATE_C4])
        expected = N * N // 4  # 16
        assert abs(len(bd) - expected) <= 2  # 允许中心不动点偏差

    def test_c4_orbit_sizes(self):
        """C4 旋转：轨道大小为 1 或 4。"""
        N = 7  # 奇数 → 存在中心不动点
        bd, om = compute_basic_domain(N, N, [SymmetryType.ROTATE_C4])
        for orbit in om.values():
            assert len(orbit) in (1, 2, 4)

    def test_translate_h(self):
        """水平平移：基本域 = H × T。"""
        H, W, T = 4, 12, 3
        bd, om = compute_basic_domain(H, W, [SymmetryType.TRANSLATE_H], T)
        assert len(bd) == H * T  # 4 * 3 = 12

    def test_coverage(self):
        """所有轨道覆盖全图无遗漏。"""
        H, W = 6, 6
        for st in [SymmetryType.LEFT_RIGHT, SymmetryType.ROTATE_C4,
                    SymmetryType.QUAD]:
            bd, om = compute_basic_domain(H, W, [st])
            all_pixels = set()
            for orbit in om.values():
                all_pixels.update(orbit)
            assert len(all_pixels) == H * W


# ═══════════════════════════════════════════════════════════════════
# 对称填充
# ═══════════════════════════════════════════════════════════════════

class TestFillFromBasicDomain:
    """fill_from_basic_domain 正确性。"""

    def test_lr_fill(self):
        """LR 填充产生左右对称图像。"""
        H, W = 4, 8
        _, om = compute_basic_domain(H, W, [SymmetryType.LEFT_RIGHT])
        rng = np.random.default_rng(7)
        img = np.zeros((H, W), dtype=int)
        for rep in om:
            img[rep] = int(rng.integers(0, 8))
        fill_from_basic_domain(img, om)
        np.testing.assert_array_equal(img, img[:, ::-1])

    def test_c4_fill(self):
        """C4 填充产生 90° 旋转不变图像。"""
        N = 8
        _, om = compute_basic_domain(N, N, [SymmetryType.ROTATE_C4])
        rng = np.random.default_rng(7)
        img = np.zeros((N, N), dtype=int)
        for rep in om:
            img[rep] = int(rng.integers(0, 8))
        fill_from_basic_domain(img, om)
        np.testing.assert_array_equal(img, np.rot90(img, k=1))

    def test_translate_fill(self):
        """平移填充产生周期性图像。"""
        H, W, T = 4, 12, 3
        _, om = compute_basic_domain(H, W, [SymmetryType.TRANSLATE_H], T)
        rng = np.random.default_rng(7)
        img = np.zeros((H, W), dtype=int)
        for rep in om:
            img[rep] = int(rng.integers(0, 8))
        fill_from_basic_domain(img, om)
        # 检查每个周期相同
        for k in range(1, W // T):
            np.testing.assert_array_equal(
                img[:, :T], img[:, k * T: (k + 1) * T],
            )


# ═══════════════════════════════════════════════════════════════════
# §6.1 增量评分
# ═══════════════════════════════════════════════════════════════════

class TestIncrementalDelta:
    """增量评分与全量重算一致性。"""

    def test_single_pixel_change(self):
        """单像素变更：增量 ≈ 全量差。"""
        rng = np.random.default_rng(99)
        H, W, L = 8, 8, 8
        sigma, tau, beta, gamma = 0.3, 0.3, 5.0, 10.0
        image = rng.integers(0, L, size=(H, W))
        targets = rng.integers(0, L, size=(H, W))

        # 全量评分（旧）
        prefs_old = pixel_preferences(image, targets, sigma, L)
        log_old = float(np.sum(np.log(np.maximum(prefs_old, PROB_EPS))))
        region_old = region_costs(image, tau, beta, gamma, L)[0]

        # 变更 (3, 4) 从 image[3,4] → new_val
        ci, cj = 3, 4
        old_v = int(image[ci, cj])
        new_v = (old_v + 2) % L
        changes = [(ci, cj, new_v)]

        d_pix, d_reg = _incremental_delta(
            image, changes, targets, sigma,
            tau, beta, gamma, L, 0.0, 0.0,
        )

        # 应用变更后全量评分
        image2 = image.copy()
        image2[ci, cj] = new_v
        prefs_new = pixel_preferences(image2, targets, sigma, L)
        log_new = float(np.sum(np.log(np.maximum(prefs_new, PROB_EPS))))
        region_new = region_costs(image2, tau, beta, gamma, L)[0]

        assert abs(d_pix - (log_new - log_old)) < 1e-10
        assert abs(d_reg - (region_new - region_old)) < 1e-10

    def test_symmetric_orbit_change(self):
        """对称轨道多像素同时变更：增量 ≈ 全量差。"""
        rng = np.random.default_rng(42)
        H, W, L = 4, 8, 8
        sigma, tau, beta, gamma = 0.3, 0.3, 5.0, 10.0
        image = rng.integers(0, L, size=(H, W))
        targets = rng.integers(0, L, size=(H, W))

        # LR 对称轨道: (1, 2) ↔ (1, 5)
        new_v = (int(image[1, 2]) + 3) % L
        changes = [(1, 2, new_v), (1, 5, new_v)]

        prefs_old = pixel_preferences(image, targets, sigma, L)
        log_old = float(np.sum(np.log(np.maximum(prefs_old, PROB_EPS))))
        region_old = region_costs(image, tau, beta, gamma, L)[0]

        d_pix, d_reg = _incremental_delta(
            image, changes, targets, sigma,
            tau, beta, gamma, L, 0.0, 0.0,
        )

        image2 = image.copy()
        for ci, cj, nv in changes:
            image2[ci, cj] = nv
        prefs_new = pixel_preferences(image2, targets, sigma, L)
        log_new = float(np.sum(np.log(np.maximum(prefs_new, PROB_EPS))))
        region_new = region_costs(image2, tau, beta, gamma, L)[0]

        assert abs(d_pix - (log_new - log_old)) < 1e-10
        assert abs(d_reg - (region_new - region_old)) < 1e-10

    def test_mirror_neighbor_double_end(self):
        """§4.4.3 边界情形：LR 对称中轴两侧互为邻居。"""
        H, W, L = 2, 4, 8  # 中轴在 j=1.5, (i,1) ↔ (i,2) 互为邻居
        sigma, tau, beta, gamma = 0.3, 0.3, 5.0, 10.0
        image = np.array([[1, 3, 5, 7],
                          [2, 4, 6, 0]], dtype=int)
        targets = np.zeros_like(image)

        # 修改 (0, 1) → 6，镜像 (0, 2) → 6
        changes = [(0, 1, 6), (0, 2, 6)]

        d_pix, d_reg = _incremental_delta(
            image, changes, targets, sigma,
            tau, beta, gamma, L, 0.0, 0.0,
        )

        image2 = image.copy()
        image2[0, 1] = 6
        image2[0, 2] = 6
        region_old = region_costs(image, tau, beta, gamma, L)[0]
        region_new = region_costs(image2, tau, beta, gamma, L)[0]

        assert abs(d_reg - (region_new - region_old)) < 1e-10


# ═══════════════════════════════════════════════════════════════════
# 方向权重
# ═══════════════════════════════════════════════════════════════════

class TestDirectionWeights:

    def test_no_direction(self):
        """无方向偏性：w_h = w_v = 1.0。"""
        w_h, w_v = _direction_weights(0.0, 0.0)
        assert w_h == 1.0 and w_v == 1.0

    def test_horizontal_bias(self):
        """strength=1, angle=0 → 水平权重 > 垂直权重。"""
        w_h, w_v = _direction_weights(1.0, 0.0)
        assert w_h > w_v


# ═══════════════════════════════════════════════════════════════════
# §4.4.1 模拟退火集成
# ═══════════════════════════════════════════════════════════════════

class TestSimulatedAnnealing:
    """SA 基本功能测试（短迭代以保持测试速度）。"""

    @pytest.fixture
    def base_params(self):
        return {
            "alpha": 0.5, "K": 255.0,
            "sigma": 0.3, "tau": 0.3, "beta": 5.0, "gamma": 10.0,
            "dir_strength": 0.0, "dir_angle": 0.0,
            "symmetry": ["none"], "epsilon": 0.0,
            "translate_period": 4,
        }

    def test_deterministic_seed(self, base_params):
        """§6.4 相同种子 → 相同结果。"""
        H, W, L = 6, 6, 8
        rng = np.random.default_rng(42)
        targets = generate_targets(H, W, L, "random_smooth", rng)

        img1, s1 = simulated_annealing(
            H, W, targets, base_params, L,
            max_iter=2000, seed=123,
        )
        img2, s2 = simulated_annealing(
            H, W, targets, base_params, L,
            max_iter=2000, seed=123,
        )
        np.testing.assert_array_equal(img1, img2)
        assert s1.dir_region == s2.dir_region

    def test_reduces_objective(self, base_params):
        """SA 降低 closure-aware 目标函数（相对随机初始化）。"""
        H, W, L = 8, 8, 8
        rng = np.random.default_rng(42)
        targets = generate_targets(H, W, L, "random_smooth", rng)

        def closure_obj(scores):
            return 1.0 * scores.cl_region - 0.01 * scores.cl_pixel

        # 随机图像的目标函数
        rand_img = np.random.default_rng(0).integers(0, L, (H, W))
        from engine.scoring import compute_scores
        rand_scores = compute_scores(rand_img, targets, base_params)
        rand_obj = closure_obj(rand_scores)

        # SA 搜索后
        img, scores = simulated_annealing(
            H, W, targets, base_params, L,
            max_iter=5000, seed=42,
        )
        sa_obj = closure_obj(scores)

        assert sa_obj < rand_obj

    def test_collective_em_used_in_final_scores(self, base_params):
        """SA 最终评分应与 collective Em 的全量重算一致。"""
        H, W, L = 4, 4, 8
        rng = np.random.default_rng(42)
        targets = generate_targets(H, W, L, "random_uniform", rng)
        img, scores = simulated_annealing(H, W, targets, base_params, L, max_iter=500, seed=1)
        expected_em = float(f1_shriek_from_log(scores.dir_pixel, base_params["alpha"], base_params["K"]))
        assert scores.em_region == expected_em

    def test_lr_symmetry_preserved(self, base_params):
        """LR 对称约束消元：结果严格左右对称。"""
        base_params["symmetry"] = ["lr"]
        H, W, L = 6, 8, 8
        rng = np.random.default_rng(42)
        targets = generate_targets(H, W, L, "random_smooth", rng)

        img, _ = simulated_annealing(
            H, W, targets, base_params, L,
            max_iter=3000, seed=42,
        )
        np.testing.assert_array_equal(img, img[:, ::-1])

    def test_c4_symmetry_preserved(self, base_params):
        """C4 旋转约束消元：结果 90° 旋转不变。"""
        base_params["symmetry"] = ["c4"]
        N, L = 8, 8
        rng = np.random.default_rng(42)
        targets = generate_targets(N, N, L, "random_smooth", rng)

        img, _ = simulated_annealing(
            N, N, targets, base_params, L,
            max_iter=3000, seed=42,
        )
        np.testing.assert_array_equal(img, np.rot90(img, k=1))

    def test_callback_invoked(self, base_params):
        """回调函数被正确调用。"""
        H, W, L = 4, 4, 4
        rng = np.random.default_rng(0)
        targets = generate_targets(H, W, L, "random_uniform", rng)

        calls = []
        def cb(it, total, obj, T):
            calls.append((it, total))

        simulated_annealing(
            H, W, targets, base_params, L,
            max_iter=3000, seed=0, callback=cb,
        )
        # 3000 / 1000 = 3 次回调（在 1000, 2000, 3000 步）
        assert len(calls) == 3
        assert calls[-1][0] == 3000

    def test_output_in_valid_range(self, base_params):
        """输出图像值域在 [0, levels-1]。"""
        H, W, L = 8, 8, 8
        rng = np.random.default_rng(42)
        targets = generate_targets(H, W, L, "gradient_h", rng)

        img, _ = simulated_annealing(
            H, W, targets, base_params, L,
            max_iter=1000, seed=0,
        )
        assert img.min() >= 0
        assert img.max() <= L - 1
