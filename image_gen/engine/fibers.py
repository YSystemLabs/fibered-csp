"""纤维定义与层间函子。

实现 §4.1：三层纤维的数值常数、f*/f_! 函子。
所有函子支持标量和 NumPy 数组输入。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# ── §4.1.3 数值约定 ──────────────────────────────────────────────────

COST_INF: float = 1e12
"""代价域的 ∞ 替代值。"""

PROB_EPS: float = 1e-15
"""概率域的最小正值（防止 log(0)）。"""

LN_PROB_FLOOR: float = -35.0
"""对数概率域的下界（≈ ln(PROB_EPS)）。"""


# ── §4.1.1 纤维配置 ──────────────────────────────────────────────────

@dataclass(frozen=True)
class FiberConfig:
    """一根纤维的完整配置。"""
    name: str   # "pixel" | "region" | "sym"
    bot: float  # 底元素值
    top: float  # 顶元素值


FIBER_PIXEL = FiberConfig(name="pixel", bot=0.0, top=1.0)
FIBER_REGION = FiberConfig(name="region", bot=COST_INF, top=0.0)
FIBER_SYM = FiberConfig(name="sym", bot=0.0, top=1.0)


# ── §4.1.2 层间函子 ──────────────────────────────────────────────────

def f1_star(c: float | np.ndarray, alpha: float, K: float = 255.0) -> float | np.ndarray:
    """区域层代价 → 像素层偏好。

    f_1^*(c) = exp(-(c/K)^alpha)

    参数
    ----
    c : 区域层代价值 (≥0)
    alpha : 涌现控制参数 (0, 1]
    K : 归一化常数 (>0)
    """
    return np.exp(-np.power(np.asarray(c, dtype=np.float64) / K, alpha))


def f1_star_log(c: float | np.ndarray, alpha: float, K: float = 255.0) -> float | np.ndarray:
    """f1_star 的对数版本：ln f_1^*(c) = -(c/K)^alpha

    直接返回对数值，避免 exp 后再 log 的精度损失。
    """
    return -np.power(np.asarray(c, dtype=np.float64) / K, alpha)


def f1_shriek(p: float | np.ndarray, alpha: float, K: float = 255.0) -> float | np.ndarray:
    """像素层偏好 → 区域层代价。

    (f_1)_!(p) = K * (ln(1/p))^(1/alpha)
    (f_1)_!(0) = COST_INF

    参数
    ----
    p : 像素层偏好值 ∈ (0, 1]
    alpha : 涌现控制参数 (0, 1]
    K : 归一化常数 (>0)
    """
    p_arr = np.maximum(np.asarray(p, dtype=np.float64), PROB_EPS)
    return K * np.power(np.log(1.0 / p_arr), 1.0 / alpha)


def f1_shriek_from_log(log_p: float | np.ndarray, alpha: float, K: float = 255.0) -> float | np.ndarray:
    """(f_1)_! 的对数域输入版本。

    给定 log_p = ln(Dir_pixel) < 0，直接计算：
        (f_1)_!(exp(log_p)) = K * (-log_p)^(1/alpha)

    避免 exp 下溢（§4.3 BUG4 修复）。
    """
    neg_log_p = np.maximum(-np.asarray(log_p, dtype=np.float64), 0.0)
    return K * np.power(neg_log_p, 1.0 / alpha)


def f2_star(b: int | np.ndarray) -> float | np.ndarray:
    """对称层布尔 → 区域层代价。

    f_2^*(1) = 0,  f_2^*(0) = COST_INF
    """
    b_arr = np.asarray(b)
    return np.where(b_arr, 0.0, COST_INF)


def f2_shriek(c: float | np.ndarray) -> int | np.ndarray:
    """区域层代价 → 对称层布尔。

    (f_2)_!(c) = 1 if c < COST_INF else 0
    """
    c_arr = np.asarray(c, dtype=np.float64)
    return np.where(c_arr < COST_INF, 1, 0)
