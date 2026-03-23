"""engine/order_params.py 单元测试。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest

from engine.order_params import (
    compute_order_params,
    spatial_correlation_length,
    _phi_mirror,
)
from engine.scoring import compute_scores


def _default_params(**overrides):
    p = {
        "alpha": 0.5, "K": 255.0,
        "sigma": 0.3, "tau": 0.3, "beta": 5.0, "gamma": 10.0,
        "dir_strength": 0.0, "dir_angle": 0.0,
        "symmetry": ["none"], "epsilon": 0.0, "translate_period": 4,
        "levels": 8,
    }
    p.update(overrides)
    return p


# ═══════════════════════════════════════════════════════════════════
# §4.6.1 phi_em
# ═══════════════════════════════════════════════════════════════════

class TestPhiEm:

    def test_uniform_match_zero(self):
        """targets = image → Dir_pixel = 0 → Em = 0 → φ_em = 0."""
        img = np.full((8, 8), 3, dtype=int)
        params = _default_params()
        scores = compute_scores(img, img, params)
        result = compute_order_params(img, scores, params, ["phi_em"])
        assert result["phi_em"] == pytest.approx(0.0, abs=1e-10)

    def test_positive_for_nonuniform(self):
        """非均匀图像 → φ_em > 0。"""
        rng = np.random.default_rng(42)
        img = rng.integers(0, 8, (8, 8))
        targets = rng.integers(0, 8, (8, 8))
        params = _default_params()
        scores = compute_scores(img, targets, params)
        result = compute_order_params(img, scores, params, ["phi_em"])
        assert result["phi_em"] > 0.0

    def test_increases_with_lower_alpha(self):
        """对固定图像，当总负对数足够大时，较小 α 给出更大的 φ_em。"""
        rng = np.random.default_rng(42)
        img = rng.integers(0, 8, (8, 8))
        targets = rng.integers(0, 8, (8, 8))

        params1 = _default_params(alpha=1.0)
        s1 = compute_scores(img, targets, params1)
        r1 = compute_order_params(img, s1, params1, ["phi_em"])

        params05 = _default_params(alpha=0.5)
        s05 = compute_scores(img, targets, params05)
        r05 = compute_order_params(img, s05, params05, ["phi_em"])

        params03 = _default_params(alpha=0.3)
        s03 = compute_scores(img, targets, params03)
        r03 = compute_order_params(img, s03, params03, ["phi_em"])

        assert r03["phi_em"] > r05["phi_em"] > r1["phi_em"]


# ═══════════════════════════════════════════════════════════════════
# §4.6.2 phi_cl
# ═══════════════════════════════════════════════════════════════════

class TestPhiCl:

    def test_clamped_to_100(self):
        """φ_cl ∈ [0, 100]。"""
        rng = np.random.default_rng(42)
        img = rng.integers(0, 8, (8, 8))
        targets = rng.integers(0, 8, (8, 8))
        params = _default_params()
        scores = compute_scores(img, targets, params)
        result = compute_order_params(img, scores, params, ["phi_cl"])
        assert 0.0 <= result["phi_cl"] <= 100.0

    def test_zero_when_no_closure_correction(self):
        """无闭包修正时 φ_cl ≈ 0。"""
        img = np.full((4, 4), 3, dtype=int)
        params = _default_params()
        scores = compute_scores(img, img, params)
        # 均匀匹配 → score 和 cl 应该很接近
        result = compute_order_params(img, scores, params, ["phi_cl"])
        assert result["phi_cl"] < 1.0


# ═══════════════════════════════════════════════════════════════════
# §4.6.3 ξ（空间相关长度）
# ═══════════════════════════════════════════════════════════════════

class TestXi:

    def test_uniform_max_correlation(self):
        """均匀图像 → ξ = min(H,W)/2（最大相关）。"""
        img = np.full((8, 8), 5, dtype=int)
        xi = spatial_correlation_length(img)
        assert xi == 4.0

    def test_noise_short_correlation(self):
        """随机噪声 → ξ 较小。"""
        rng = np.random.default_rng(42)
        img = rng.integers(0, 256, (16, 16))
        xi = spatial_correlation_length(img)
        assert xi < 4.0  # 远小于 min(16,16)/2 = 8

    def test_smooth_longer_correlation(self):
        """平滑图像 → ξ > 随机噪声的 ξ。"""
        rng = np.random.default_rng(42)
        noise = rng.integers(0, 256, (16, 16))
        xi_noise = spatial_correlation_length(noise)

        # 平滑色块
        smooth = np.zeros((16, 16), dtype=int)
        smooth[:8, :] = 200
        smooth[8:, :] = 50
        xi_smooth = spatial_correlation_length(smooth)

        assert xi_smooth > xi_noise

    def test_via_compute_order_params(self):
        """通过 compute_order_params 接口调用 xi。"""
        rng = np.random.default_rng(42)
        img = rng.integers(0, 8, (8, 8))
        targets = rng.integers(0, 8, (8, 8))
        params = _default_params()
        scores = compute_scores(img, targets, params)
        result = compute_order_params(img, scores, params, ["xi"])
        assert "xi" in result
        assert result["xi"] > 0


# ═══════════════════════════════════════════════════════════════════
# §4.6.4 phi_dir
# ═══════════════════════════════════════════════════════════════════

class TestPhiDir:

    def test_isotropic_near_zero(self):
        """各向同性图像（dir_strength=0，C_H ≈ C_V）→ φ_dir ≈ 0。"""
        rng = np.random.default_rng(42)
        img = rng.integers(0, 8, (16, 16))
        targets = rng.integers(0, 8, (16, 16))
        params = _default_params()
        scores = compute_scores(img, targets, params)
        result = compute_order_params(img, scores, params, ["phi_dir"])
        assert result["phi_dir"] < 0.2  # 大致各向同性

    def test_horizontal_stripes_high(self):
        """水平条纹 → C_V ≫ C_H → φ_dir 较大。"""
        img = np.zeros((8, 8), dtype=int)
        for i in range(8):
            img[i, :] = (i % 2) * 7
        targets = np.zeros_like(img)
        params = _default_params()
        scores = compute_scores(img, targets, params)
        result = compute_order_params(img, scores, params, ["phi_dir"])
        assert result["phi_dir"] > 0.5

    def test_rectangular_grid_unbiased_for_uniform(self):
        """非方形画布上，平均边代价定义不应引入虚假方向性。"""
        img = np.full((6, 10), 3, dtype=int)
        params = _default_params()
        scores = compute_scores(img, img, params)
        result = compute_order_params(img, scores, params, ["phi_dir"])
        assert result["phi_dir"] == pytest.approx(0.0, abs=1e-12)


# ═══════════════════════════════════════════════════════════════════
# §4.6.5 phi_mirror
# ═══════════════════════════════════════════════════════════════════

class TestPhiMirror:

    def test_perfect_lr_symmetric(self):
        """完美左右对称 → φ_mirror = 1.0。"""
        img = np.array([[1, 2, 3, 3, 2, 1],
                        [4, 5, 6, 6, 5, 4]], dtype=int)
        assert _phi_mirror(img) == pytest.approx(1.0)

    def test_uniform_perfect(self):
        """均匀图像 → 完美镜像。"""
        img = np.full((4, 4), 5, dtype=int)
        assert _phi_mirror(img) == 1.0

    def test_asymmetric_low(self):
        """强烈不对称 → φ_mirror < 1。"""
        img = np.zeros((4, 8), dtype=int)
        img[:, :4] = 0
        img[:, 4:] = 7
        val = _phi_mirror(img)
        assert val < 0.5


# ═══════════════════════════════════════════════════════════════════
# 错误处理
# ═══════════════════════════════════════════════════════════════════

def test_unknown_param_raises():
    img = np.zeros((4, 4), dtype=int)
    params = _default_params()
    scores = compute_scores(img, img, params)
    with pytest.raises(ValueError, match="Unknown order parameter"):
        compute_order_params(img, scores, params, ["nonexistent"])


def test_multiple_params_at_once():
    """一次请求多个序参量。"""
    rng = np.random.default_rng(42)
    img = rng.integers(0, 8, (8, 8))
    targets = rng.integers(0, 8, (8, 8))
    params = _default_params()
    scores = compute_scores(img, targets, params)
    result = compute_order_params(
        img, scores, params,
        ["phi_em", "phi_cl", "xi", "phi_dir", "phi_mirror"],
    )
    assert len(result) == 5
    for k, v in result.items():
        assert isinstance(v, float)
