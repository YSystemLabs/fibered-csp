"""三层约束定义。

实现 §4.2：像素层一元偏好、区域层边缘感知 Potts、对称性层布尔约束。
"""

from __future__ import annotations

from enum import Enum

import numpy as np


# ── §4.2.1 像素层约束（一元） ────────────────────────────────────

def pixel_preferences(
    image: np.ndarray,
    targets: np.ndarray,
    sigma: float,
    levels: int,
) -> np.ndarray:
    """逐像素偏好值 ∈ [0, 1]。

    φ_{p}(v) = exp(-d_p² / (2σ²)),  d_p = ‖v - t_p‖ / (L-1)

    参数
    ----
    image   : (H, W) 或 (H, W, 3)，当前赋值（整数值 0..L-1）
    targets : 同 image 形状，目标色
    sigma   : 偏好强度
    levels  : 灰度级数 L（域大小）

    返回
    ----
    (H, W) float64 数组，每像素偏好值。
    """
    channels = image.shape[-1] if image.ndim == 3 else 1
    norm = (levels - 1) * np.sqrt(channels)
    diff = (image.astype(np.float64) - targets.astype(np.float64)) / norm
    if diff.ndim == 3:
        d_sq = np.sum(diff ** 2, axis=-1)
    else:
        d_sq = diff ** 2
    return np.exp(-d_sq / (2.0 * sigma ** 2))


# ── §4.2.2 区域层约束（边缘感知 Potts） ─────────────────────────

def _potts_cost(d: np.ndarray, tau: float, beta: float, gamma: float,
                mu: float = 0.0) -> np.ndarray:
    """对归一化差异 d ∈ [0,1] 应用边缘感知 Potts 代价。

    φ_R(d) = (γ - μ)·d  if d ≤ τ  (同区域)
             β·d        if d > τ  (跨边缘)

    当 μ > γ 时，同区域代价为负，奖励邻居差异 → 反铁磁/纹理效应。
    μ = 0 时退化为原始 Potts。
    """
    return np.where(d <= tau, (gamma - mu) * d, beta * d)


def region_costs(
    image: np.ndarray,
    tau: float,
    beta: float,
    gamma: float,
    levels: int,
    dir_strength: float = 0.0,
    dir_angle: float = 0.0,
    mu: float = 0.0,
) -> tuple[float, np.ndarray, float, float]:
    """区域层总代价 + 热力图 + C_H/C_V 分量。

    返回
    ----
    (total_cost, heatmap, C_H, C_V)
    - total_cost : 标量，所有对的代价之和
    - heatmap    : (H, W) 每像素邻域代价均值
    - C_H        : 水平对代价之和
    - C_V        : 垂直对代价之和
    """
    img = image.astype(np.float64)
    channels = img.shape[-1] if img.ndim == 3 else 1
    norm = (levels - 1) * np.sqrt(channels)
    H, W = img.shape[:2]

    # 水平相邻差异
    if img.ndim == 3:
        dh = np.sqrt(np.sum(((img[:, 1:] - img[:, :-1]) / norm) ** 2, axis=-1))
        dv = np.sqrt(np.sum(((img[1:, :] - img[:-1, :]) / norm) ** 2, axis=-1))
    else:
        dh = np.abs(img[:, 1:] - img[:, :-1]) / norm
        dv = np.abs(img[1:, :] - img[:-1, :]) / norm

    # Potts 代价
    cost_h = _potts_cost(dh, tau, beta, gamma, mu)
    cost_v = _potts_cost(dv, tau, beta, gamma, mu)

    # 方向权重 §2.5.2 可选扩展
    if dir_strength != 0.0:
        theta0 = np.radians(dir_angle)
        # 水平对 θ=0, 垂直对 θ=π/2
        w_h = 1.0 + dir_strength * np.cos(2.0 * (0.0 - theta0))
        w_v = 1.0 + dir_strength * np.cos(2.0 * (np.pi / 2.0 - theta0))
        cost_h = cost_h * w_h
        cost_v = cost_v * w_v

    C_H = float(np.sum(cost_h))
    C_V = float(np.sum(cost_v))
    total = C_H + C_V

    # 热力图：每像素 = 该像素参与的所有对的代价均值
    heatmap = np.zeros((H, W), dtype=np.float64)
    count = np.zeros((H, W), dtype=np.float64)

    # 水平对贡献
    heatmap[:, :-1] += cost_h
    heatmap[:, 1:]  += cost_h
    count[:, :-1]   += 1.0
    count[:, 1:]    += 1.0

    # 垂直对贡献
    heatmap[:-1, :] += cost_v
    heatmap[1:, :]  += cost_v
    count[:-1, :]   += 1.0
    count[1:, :]    += 1.0

    heatmap = np.divide(heatmap, count, where=count > 0, out=heatmap)

    return total, heatmap, C_H, C_V


# ── §4.2.3 对称性层约束 ─────────────────────────────────────────

class SymmetryType(str, Enum):
    NONE = "none"
    LEFT_RIGHT = "lr"
    UP_DOWN = "ud"
    QUAD = "quad"
    ROTATE_C4 = "c4"
    TRANSLATE_H = "trans_h"


def symmetry_check(
    image: np.ndarray,
    sym_types: list[SymmetryType],
    epsilon: float,
    translate_period: int = 0,
) -> bool:
    """检查图像是否满足所有启用的对称约束。

    参数
    ----
    image            : (H, W) 或 (H, W, 3)
    sym_types        : 启用的对称类型列表
    epsilon          : 容差（色值差异在 ε 以内视为相等）
    translate_period : 水平平移周期（仅 TRANSLATE_H 时使用）
    """
    img = image.astype(np.float64)
    H, W = img.shape[:2]

    for st in sym_types:
        if st == SymmetryType.NONE:
            continue

        if st == SymmetryType.LEFT_RIGHT:
            flipped = img[:, ::-1]
            if not _within_epsilon(img, flipped, epsilon):
                return False

        elif st == SymmetryType.UP_DOWN:
            flipped = img[::-1, :]
            if not _within_epsilon(img, flipped, epsilon):
                return False

        elif st == SymmetryType.QUAD:
            if not _within_epsilon(img, img[:, ::-1], epsilon):
                return False
            if not _within_epsilon(img, img[::-1, :], epsilon):
                return False

        elif st == SymmetryType.ROTATE_C4:
            assert H == W, "C4 rotation requires H == W"
            rotated = np.rot90(img, k=1)  # 90° counterclockwise
            if not _within_epsilon(img, rotated, epsilon):
                return False

        elif st == SymmetryType.TRANSLATE_H:
            assert translate_period > 0, "translate_period must be > 0"
            shifted = np.roll(img, -translate_period, axis=1)
            if not _within_epsilon(img, shifted, epsilon):
                return False

    return True


def _within_epsilon(a: np.ndarray, b: np.ndarray, epsilon: float) -> bool:
    """检查两个数组是否在 epsilon 容差内相等。"""
    if a.ndim == 3:
        diff = np.sqrt(np.sum((a - b) ** 2, axis=-1))
    else:
        diff = np.abs(a - b)
    return bool(np.all(diff <= epsilon + 1e-12))
