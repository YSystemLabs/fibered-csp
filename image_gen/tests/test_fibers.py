"""fibers.py 单元测试 — 对照 §8.2 数值验收表。"""

import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.fibers import (
    COST_INF, PROB_EPS, LN_PROB_FLOOR,
    f1_star, f1_star_log, f1_shriek, f1_shriek_from_log,
    f2_star, f2_shriek,
    FIBER_PIXEL, FIBER_REGION, FIBER_SYM,
)


def test_constants():
    assert COST_INF == 1e12
    assert PROB_EPS == 1e-15
    assert LN_PROB_FLOOR == -35.0


def test_fiber_configs():
    assert FIBER_PIXEL.bot == 0.0 and FIBER_PIXEL.top == 1.0
    assert FIBER_REGION.bot == COST_INF and FIBER_REGION.top == 0.0
    assert FIBER_SYM.bot == 0.0 and FIBER_SYM.top == 1.0


# ── f1_star ──────────────────────────────────────────────────────────

def test_f1_star_basic():
    # f1*(0) = exp(0) = 1 = top_pixel
    assert f1_star(0.0, alpha=0.5) == 1.0
    # f1*(INF) → 0 = bot_pixel
    assert f1_star(COST_INF, alpha=1.0) < PROB_EPS


def test_f1_star_vectorized():
    c = np.array([0.0, 100.0, 255.0])
    result = f1_star(c, alpha=1.0, K=255.0)
    assert result.shape == (3,)
    np.testing.assert_allclose(result[0], 1.0)
    np.testing.assert_allclose(result[2], np.exp(-1.0))


# ── f1_shriek —— §8.2 回归测试 ──────────────────────────────────

def test_f1_shriek_regression_alpha1():
    """f_!(0.394), alpha=1.0, K=255 ≈ 237.6（容差 ±0.5）"""
    result = f1_shriek(0.394, alpha=1.0, K=255.0)
    assert abs(result - 237.6) < 0.5, f"f1_shriek(0.394, a=1.0) = {result}"


def test_f1_shriek_regression_alpha05():
    """f_!(0.394), alpha=0.5, K=255 ≈ 221.5（容差 ±0.5）"""
    result = f1_shriek(0.394, alpha=0.5, K=255.0)
    assert abs(result - 221.5) < 0.5, f"f1_shriek(0.394, a=0.5) = {result}"


def test_f1_shriek_emergence_deviation():
    """涌现偏差 δ(p1=0.8, p2=0.6), alpha=0.5
    δ = f_!(p1*p2) - (f_!(p1) + f_!(p2)) ≈ 58.2（容差 ±0.5）
    注：α<1 时 f_! 是次可加的，δ < 0 是涌现的标志；
    但规范写的是 |δ|≈58.2。让我们验证。
    """
    p1, p2 = 0.8, 0.6
    alpha, K = 0.5, 255.0
    lhs = f1_shriek(p1 * p2, alpha, K)
    rhs = f1_shriek(p1, alpha, K) + f1_shriek(p2, alpha, K)
    delta = abs(lhs - rhs)  # |f_!(p1p2) - (f_!(p1)+f_!(p2))|
    assert abs(delta - 58.2) < 0.5, f"emergence deviation = {delta}"


# ── f1_shriek_from_log（§4.3 BUG4 修复的对数域版本）────────────

def test_f1_shriek_from_log_consistency():
    """log 域版本与原版一致。"""
    p = 0.394
    log_p = np.log(p)
    a1 = f1_shriek(p, alpha=1.0, K=255.0)
    a2 = f1_shriek_from_log(log_p, alpha=1.0, K=255.0)
    np.testing.assert_allclose(a1, a2, rtol=1e-10)

    a3 = f1_shriek(p, alpha=0.5, K=255.0)
    a4 = f1_shriek_from_log(log_p, alpha=0.5, K=255.0)
    np.testing.assert_allclose(a3, a4, rtol=1e-10)


def test_f1_shriek_from_log_large_negative():
    """log_p = -1000 时不应 overflow（BUG4 场景）。"""
    result = f1_shriek_from_log(-1000.0, alpha=0.5, K=255.0)
    assert np.isfinite(result)
    assert result > 0


def test_f1_star_log_consistency():
    """f1_star_log 与 log(f1_star) 一致。"""
    c = np.array([0.0, 50.0, 200.0, 500.0])
    direct = f1_star_log(c, alpha=0.7, K=255.0)
    via_exp = np.log(np.maximum(f1_star(c, alpha=0.7, K=255.0), PROB_EPS))
    np.testing.assert_allclose(direct, via_exp, atol=1e-10)


# ── f2_star / f2_shriek ─────────────────────────────────────────

def test_f2_star():
    assert f2_star(1) == 0.0
    assert f2_star(0) == COST_INF


def test_f2_shriek():
    assert f2_shriek(0.0) == 1
    assert f2_shriek(100.0) == 1
    assert f2_shriek(COST_INF) == 0


def test_f2_vectorized():
    b = np.array([1, 0, 1, 0])
    np.testing.assert_array_equal(f2_star(b), [0.0, COST_INF, 0.0, COST_INF])
    c = np.array([0.0, 1.0, COST_INF, 500.0])
    np.testing.assert_array_equal(f2_shriek(c), [1, 1, 0, 1])


# ── 伴随性验证 ───────────────────────────────────────────────────

def test_adjunction_f1():
    """验证 f1_! ⊣ f1*：
    区域层为 [0,∞]^op（反序），所以伴随条件为：
    f1_!(p) ≥_nat c  ⟺  p ≤ f1*(c)
    """
    alpha, K = 0.5, 255.0
    for p in [0.1, 0.3, 0.5, 0.8, 0.99]:
        for c in [10.0, 100.0, 255.0, 500.0]:
            lhs = float(f1_shriek(p, alpha, K)) >= c - 1e-9  # ≥_nat on region
            rhs = p <= float(f1_star(c, alpha, K)) + 1e-9
            assert lhs == rhs, f"Adjunction failed at p={p}, c={c}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
