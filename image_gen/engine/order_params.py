"""序参量计算。

实现 §4.6：φ_em, φ_cl, ξ, φ_dir, φ_mirror 五个序参量。
"""

from __future__ import annotations

import numpy as np

from .scoring import LayerScores

# 防除零小量
_EPS0: float = 1e-10


# ═══════════════════════════════════════════════════════════════════
# §4.6 主入口
# ═══════════════════════════════════════════════════════════════════

def compute_order_params(
    image: np.ndarray,
    scores: LayerScores,
    params: dict,
    requested: list[str],
) -> dict[str, float]:
    """计算请求的序参量，返回 {标识符: 值} 字典。

    可用标识符: phi_em, phi_cl, xi, phi_dir, phi_mirror
    """
    H, W = image.shape[:2]
    result: dict[str, float] = {}

    for key in requested:
        if key == "phi_em":
            result[key] = _phi_em(scores, H, W)
        elif key == "phi_cl":
            result[key] = _phi_cl(scores)
        elif key == "xi":
            result[key] = _xi(image)
        elif key == "phi_dir":
            result[key] = _phi_dir(scores)
        elif key == "phi_mirror":
            result[key] = _phi_mirror(image)
        else:
            raise ValueError(f"Unknown order parameter: {key!r}")

    return result


# ═══════════════════════════════════════════════════════════════════
# §4.6.1 φ_em（归一化涌现强度）
# ═══════════════════════════════════════════════════════════════════

def _phi_em(scores: LayerScores, H: int, W: int) -> float:
    """φ_em = Em_region / (H × W)"""
    return scores.em_region / (H * W)


# ═══════════════════════════════════════════════════════════════════
# §4.6.2 φ_cl（闭包修正比率 %）
# ═══════════════════════════════════════════════════════════════════

def _phi_cl(scores: LayerScores) -> float:
    """φ_cl = |cl_pixel - score_pixel| / max(|score_pixel|, EPS) × 100

    Clamped 到 [0, 100]。
    """
    val = (
        abs(scores.cl_pixel - scores.score_pixel)
        / max(abs(scores.score_pixel), _EPS0)
        * 100.0
    )
    return min(val, 100.0)


# ═══════════════════════════════════════════════════════════════════
# §4.6.3 ξ（空间相关长度）
# ═══════════════════════════════════════════════════════════════════

def spatial_correlation_length(image: np.ndarray) -> float:
    """通过径向自相关函数估计空间相关长度。

    1. 归一化到 [0,1]
    2. FFT 加速 2D 自相关
    3. 径向平均为 1D C(r)
    4. 找 C(r) < C(0)/e 的最小 r
    """
    img = image.astype(np.float64)
    if img.ndim == 3:
        img = np.mean(img, axis=-1)

    H, W = img.shape
    rng = img.max() - img.min()
    if rng < _EPS0:
        # 完全均匀图像 → 无限相关
        return min(H, W) / 2.0

    img = (img - img.min()) / rng
    img = img - img.mean()

    # 2D 自相关（FFT 加速）
    # 用零填充避免循环卷积
    fft = np.fft.fft2(img, s=(2 * H, 2 * W))
    acf_full = np.real(np.fft.ifft2(fft * np.conj(fft)))
    # 取左上 H×W 块（正 lag）
    acf = acf_full[:H, :W]
    acf /= max(acf[0, 0], _EPS0)  # 归一化使 C(0) = 1

    # 径向平均
    max_r = min(H, W) // 2
    radial_sum = np.zeros(max_r + 1)
    radial_cnt = np.zeros(max_r + 1)
    for di in range(H):
        for dj in range(W):
            r = int(np.sqrt(di * di + dj * dj) + 0.5)
            if r <= max_r:
                radial_sum[r] += acf[di, dj]
                radial_cnt[r] += 1

    # C(r)
    radial_cnt = np.maximum(radial_cnt, 1)
    c_r = radial_sum / radial_cnt

    # 找 C(r) < 1/e 的最小 r
    threshold = np.exp(-1.0)
    for r in range(1, max_r + 1):
        if c_r[r] < threshold:
            return float(r)

    return float(max_r)


_xi = spatial_correlation_length  # 内部别名


# ═══════════════════════════════════════════════════════════════════
# §4.6.4 φ_dir（方向序参量）
# ═══════════════════════════════════════════════════════════════════

def _phi_dir(scores: LayerScores) -> float:
    """φ_dir：基于平均水平/垂直边代价，消除边数偏置。"""
    heatmap = scores.region_heatmap
    if heatmap is None:
        return 0.0
    H, W = heatmap.shape[:2]
    avg_h = scores.C_H / max(H * (W - 1), 1)
    avg_v = scores.C_V / max((H - 1) * W, 1)
    return abs(avg_h - avg_v) / (avg_h + avg_v + _EPS0)


# ═══════════════════════════════════════════════════════════════════
# §4.6.5 φ_mirror（镜像序参量）
# ═══════════════════════════════════════════════════════════════════

def _phi_mirror(image: np.ndarray) -> float:
    """φ_mirror = 1 - mean(|left - right_flipped| / norm)"""
    img = image.astype(np.float64)
    if img.ndim == 3:
        img = np.mean(img, axis=-1)

    H, W = img.shape
    norm = img.max() - img.min()
    if norm < _EPS0:
        return 1.0  # 完全均匀 → 完美镜像

    left = img[:, : W // 2]
    right = img[:, -1 : W - W // 2 - 1 : -1]  # 镜像翻转右半
    return float(1.0 - np.mean(np.abs(left - right) / norm))
