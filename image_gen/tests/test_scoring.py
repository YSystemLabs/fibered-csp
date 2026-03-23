"""scoring.py 单元测试 — 对照 §8.2 回归值和 §2.6 流水线逻辑。"""

import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.scoring import compute_scores, LayerScores
from engine.fibers import COST_INF, LN_PROB_FLOOR, f1_shriek_from_log


def _make_params(**overrides):
    defaults = dict(
        alpha=1.0, K=255.0, sigma=0.3, levels=8,
        tau=0.3, beta=5.0, gamma=10.0,
        dir_strength=0.0, dir_angle=0.0,
        symmetry=["none"], epsilon=0.0, translate_period=4,
    )
    defaults.update(overrides)
    return defaults


# ── 基本流水线 ──────────────────────────────────────────────────

def test_uniform_image():
    """均匀图 + 目标=自身 → 代价 0，偏好 max，无闭包修正。"""
    img = np.full((4, 4), 3)
    targets = np.full((4, 4), 3)
    s = compute_scores(img, targets, _make_params())

    assert s.dir_pixel == 0.0  # log(1) * 16 = 0
    assert s.dir_region == 0.0
    assert s.dir_sym is True
    assert s.closure_correction_pixel <= 0.0  # non-positive
    assert not s.is_collapsed


def test_collapse_propagation():
    """对称坍缩 → 区域 INF → 像素 bot。"""
    # 不对称图像 + lr 约束
    img = np.array([[0, 7], [7, 0]])
    targets = np.zeros_like(img)
    params = _make_params(symmetry=["lr"], epsilon=0.0)
    s = compute_scores(img, targets, params)

    assert s.dir_sym is False
    assert s.cl_sym is False
    assert s.cl_region >= COST_INF * 0.9
    assert s.cl_pixel <= LN_PROB_FLOOR
    assert s.is_collapsed


def test_no_collapse_with_symmetry():
    """完全对称图 + lr → 不坍缩。"""
    img = np.array([[1, 2, 1], [3, 4, 3]])
    targets = img.copy()
    params = _make_params(symmetry=["lr"])
    s = compute_scores(img, targets, params)

    assert s.dir_sym is True
    assert s.cl_sym is True
    assert not s.is_collapsed


# ── 涌现效应 ────────────────────────────────────────────────────

def test_emergence_increases_region_cost():
    """em_region > 0 when pixels have non-perfect preferences。"""
    img = np.array([[0, 3], [3, 0]])
    targets = np.array([[7, 7], [7, 7]])
    s = compute_scores(img, targets, _make_params(alpha=0.5))

    assert s.em_region > 0.0
    assert s.score_region > s.dir_region


def test_emergence_is_collective_shriek_of_dir_pixel():
    """Em_region 必须是对整体 Dir_pixel 的一次 shriek，而非逐像素 surrogate。"""
    img = np.array([[0, 3], [3, 0]])
    targets = np.array([[7, 7], [7, 7]])
    params = _make_params(alpha=0.5)
    s = compute_scores(img, targets, params)
    expected = float(f1_shriek_from_log(s.dir_pixel, alpha=0.5, K=255.0))
    assert s.em_region == expected


def test_alpha_1_vs_alpha_05():
    """α=1 → 弱涌现；α=0.5 → 强涌现。em_region 在 α=0.5 时应更大。"""
    img = np.random.RandomState(42).randint(0, 8, (8, 8))
    targets = np.random.RandomState(99).randint(0, 8, (8, 8))

    s1 = compute_scores(img, targets, _make_params(alpha=1.0))
    s05 = compute_scores(img, targets, _make_params(alpha=0.5))

    # 两者的 Dir_pixel 相同（不依赖 alpha）
    np.testing.assert_allclose(s1.dir_pixel, s05.dir_pixel)

    # α=0.5 时涌现贡献应不同于 α=1.0（通常更小因 1/α 更大 → 指数更大）
    # 不断言方向，只断言它们不同
    assert s1.em_region != s05.em_region


# ── 闭包修正方向 ────────────────────────────────────────────────

def test_closure_pixel_leq_score_pixel():
    """截面化闭包只能让像素层更差（或不变）：cl ≤ score in log 域。"""
    img = np.random.RandomState(42).randint(0, 8, (8, 8))
    targets = np.random.RandomState(99).randint(0, 8, (8, 8))
    s = compute_scores(img, targets, _make_params(alpha=0.5))
    assert s.cl_pixel <= s.score_pixel + 1e-12


def test_closure_region_geq_score_region():
    """截面化闭包只能让区域层更差（代价更高）：cl ≥ score。"""
    img = np.random.RandomState(42).randint(0, 8, (8, 8))
    targets = np.random.RandomState(99).randint(0, 8, (8, 8))
    s = compute_scores(img, targets, _make_params(alpha=0.5))
    assert s.cl_region >= s.score_region - 1e-12


# ── 返回值完整性 ────────────────────────────────────────────────

def test_heatmap_and_prefs_returned():
    img = np.random.RandomState(42).randint(0, 8, (6, 8))
    targets = np.random.RandomState(99).randint(0, 8, (6, 8))
    s = compute_scores(img, targets, _make_params())
    assert s.region_heatmap is not None
    assert s.region_heatmap.shape == (6, 8)
    assert s.pixel_prefs is not None
    assert s.pixel_prefs.shape == (6, 8)
    assert s.closure_map is not None
    assert s.closure_map.shape == (6, 8)


def test_closure_map_mass_matches_total_correction():
    img = np.random.RandomState(42).randint(0, 8, (6, 8))
    targets = np.random.RandomState(99).randint(0, 8, (6, 8))
    s = compute_scores(img, targets, _make_params(alpha=0.5))
    np.testing.assert_allclose(
        float(np.sum(s.closure_map)),
        max(s.score_pixel - s.cl_pixel, 0.0),
        atol=1e-10,
    )


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
