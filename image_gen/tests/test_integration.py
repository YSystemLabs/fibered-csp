"""端到端集成测试：模拟完整的 generate → score → sweep 工作流。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest

from engine.search import generate_targets, simulated_annealing
from engine.scoring import compute_scores
from engine.order_params import compute_order_params
from engine.phase_scan import run_sweep


class TestEndToEnd:
    """完整流水线：目标生成 → SA → 评分 → 序参量。"""

    def test_full_pipeline_no_symmetry(self):
        """§7.1 推荐参数组（无对称，短迭代）。"""
        params = {
            "alpha": 0.5, "K": 255.0,
            "sigma": 0.3, "tau": 0.3, "beta": 5.0, "gamma": 10.0,
            "dir_strength": 0.0, "dir_angle": 0.0,
            "symmetry": ["none"], "epsilon": 0.0, "translate_period": 4,
            "levels": 8,
        }
        H, W, L, seed = 8, 8, 8, 42

        rng = np.random.default_rng(seed)
        targets = generate_targets(H, W, L, "random_smooth", rng)
        img, scores = simulated_annealing(
            H, W, targets, params, levels=L, max_iter=3000, seed=seed,
        )

        # 基本断言
        assert img.shape == (H, W)
        assert img.min() >= 0 and img.max() <= L - 1
        assert scores.dir_region >= 0
        assert scores.dir_pixel <= 0  # log 域，负值

        # 序参量
        ops = compute_order_params(
            img, scores, params,
            ["phi_em", "phi_cl", "xi", "phi_dir", "phi_mirror"],
        )
        assert ops["phi_em"] >= 0
        assert 0 <= ops["phi_cl"] <= 100
        assert ops["xi"] > 0
        assert 0 <= ops["phi_dir"] <= 1
        assert 0 <= ops["phi_mirror"] <= 1

    def test_full_pipeline_lr_symmetry(self):
        """LR 对称 + 涌现 → 产生对称图案。"""
        params = {
            "alpha": 0.3, "K": 255.0,
            "sigma": 0.3, "tau": 0.3, "beta": 5.0, "gamma": 10.0,
            "dir_strength": 0.0, "dir_angle": 0.0,
            "symmetry": ["lr"], "epsilon": 0.0, "translate_period": 4,
            "levels": 8,
        }
        H, W, L, seed = 8, 8, 8, 42

        rng = np.random.default_rng(seed)
        targets = generate_targets(H, W, L, "random_smooth", rng)
        img, scores = simulated_annealing(
            H, W, targets, params, levels=L, max_iter=5000, seed=seed,
        )

        # 严格左右对称
        np.testing.assert_array_equal(img, img[:, ::-1])
        # 镜像序参量应为 1.0
        ops = compute_order_params(img, scores, params, ["phi_mirror"])
        assert ops["phi_mirror"] == pytest.approx(1.0)

    def test_alpha_sweep_phi_em_trend(self):
        """α 扫描可产生有效的 φ_em 曲线与 α_c 估计。"""
        result = run_sweep(
            base_params={
                "width": 6, "height": 6, "levels": 4,
                "target_mode": "random_smooth", "seed": 42,
                "max_iter": 500,
                "sigma": 0.3, "tau": 0.3, "beta": 5.0, "gamma": 10.0,
                "K": 255.0,
                "symmetry": ["none"], "epsilon": 0.0, "translate_period": 4,
            },
            axis_x={"param": "alpha", "min": 0.2, "max": 1.0, "steps": 5},
            axis_y=None,
            order_param_ids=["phi_em"],
        )

        vals = result.order_params["phi_em"][0]
        assert len(vals) == 5
        assert all(v >= 0 for v in vals)
        assert result.estimated_alpha_c is not None

    def test_score_recompute_matches_sa_output(self):
        """SA 返回的 scores 与重新全量评分一致。"""
        params = {
            "alpha": 0.5, "K": 255.0,
            "sigma": 0.3, "tau": 0.3, "beta": 5.0, "gamma": 10.0,
            "dir_strength": 0.0, "dir_angle": 0.0,
            "symmetry": ["none"], "epsilon": 0.0, "translate_period": 4,
            "levels": 8,
        }
        H, W, L, seed = 6, 6, 8, 99

        rng = np.random.default_rng(seed)
        targets = generate_targets(H, W, L, "random_smooth", rng)
        img, sa_scores = simulated_annealing(
            H, W, targets, params, levels=L, max_iter=2000, seed=seed,
        )

        # 独立重算
        fresh_scores = compute_scores(img, targets, params)

        assert sa_scores.dir_pixel == pytest.approx(fresh_scores.dir_pixel, abs=1e-8)
        assert sa_scores.dir_region == pytest.approx(fresh_scores.dir_region, abs=1e-8)
        assert sa_scores.em_region == pytest.approx(fresh_scores.em_region, abs=1e-8)
        assert sa_scores.score_region == pytest.approx(fresh_scores.score_region, abs=1e-8)

    def test_determinism(self):
        """§6.4 完全确定性：相同种子 → 相同结果。"""
        params = {
            "alpha": 0.5, "K": 255.0,
            "sigma": 0.3, "tau": 0.3, "beta": 5.0, "gamma": 10.0,
            "dir_strength": 0.0, "dir_angle": 0.0,
            "symmetry": ["lr"], "epsilon": 0.0, "translate_period": 4,
            "levels": 8,
        }
        H, W, L, seed = 8, 8, 8, 77

        rng1 = np.random.default_rng(seed)
        targets1 = generate_targets(H, W, L, "random_smooth", rng1)
        img1, s1 = simulated_annealing(
            H, W, targets1, params, levels=L, max_iter=2000, seed=seed,
        )

        rng2 = np.random.default_rng(seed)
        targets2 = generate_targets(H, W, L, "random_smooth", rng2)
        img2, s2 = simulated_annealing(
            H, W, targets2, params, levels=L, max_iter=2000, seed=seed,
        )

        np.testing.assert_array_equal(img1, img2)
        np.testing.assert_array_equal(targets1, targets2)
        assert s1.dir_region == s2.dir_region
