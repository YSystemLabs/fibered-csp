"""评分流水线 S1–S4。

实现 §4.3：直接评分 → 涌现 → 总评分 → 截面化闭包。
所有像素层运算在对数域进行（§6.2）。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .fibers import (
    COST_INF, PROB_EPS, LN_PROB_FLOOR,
    f1_star_log, f1_shriek_from_log,
    f2_star, f2_shriek,
)
from .constraints import (
    pixel_preferences, region_costs, symmetry_check, SymmetryType,
)


@dataclass
class LayerScores:
    """一次评分的完整结果。"""

    # S1: 直接评分
    dir_pixel: float       # log 域
    dir_region: float      # 代价域（自然值）
    dir_sym: bool

    # S2: 涌现贡献
    em_region: float       # (f_1)_!(Dir_pixel)

    # S3: 总评分
    score_pixel: float     # log 域
    score_region: float
    score_sym: bool

    # S4: 截面化闭包后
    cl_pixel: float        # log 域
    cl_region: float
    cl_sym: bool

    # 诊断
    closure_correction_pixel: float   # cl_pixel - score_pixel
    closure_correction_region: float  # cl_region - score_region
    is_collapsed: bool

    # 附加数据（前端可视化用）
    region_heatmap: np.ndarray | None = None  # (H, W)
    pixel_prefs: np.ndarray | None = None     # (H, W) — log 域逐像素偏好
    closure_map: np.ndarray | None = None     # (H, W) — 闭包修正热力图
    C_H: float = 0.0
    C_V: float = 0.0


def compute_scores(
    image: np.ndarray,
    targets: np.ndarray,
    params: dict,
) -> LayerScores:
    """执行完整的 S1–S4 评分流水线。

    参数
    ----
    image   : (H, W) 或 (H, W, 3)，当前赋值
    targets : 同 image 形状，目标色
    params  : 参数字典，需包含：
        alpha, K, sigma, levels,
        tau, beta, gamma, dir_strength, dir_angle,
        symmetry (list[str]), epsilon, translate_period
    """
    alpha = params.get("alpha", 0.5)
    K = params.get("K", 255.0)
    sigma = params.get("sigma", 0.3)
    levels = params.get("levels", 8)
    tau = params.get("tau", 0.3)
    beta = params.get("beta", 5.0)
    gamma = params.get("gamma", 10.0)
    dir_strength = params.get("dir_strength", 0.0)
    dir_angle = params.get("dir_angle", 0.0)
    mu = params.get("mu", 0.0)
    sym_strs = params.get("symmetry", ["none"])
    epsilon = params.get("epsilon", 0.0)
    translate_period = params.get("translate_period", 4)

    sym_types = [SymmetryType(s) for s in sym_strs]

    # ── S1：逐层直接评分 ──────────────────────────────────────

    # 像素层（log 域）
    prefs = pixel_preferences(image, targets, sigma, levels)
    prefs_log = np.log(np.maximum(prefs, PROB_EPS))
    dir_pixel_log = float(np.sum(prefs_log))

    # 区域层
    dir_region, heatmap, C_H, C_V = region_costs(
        image, tau, beta, gamma, levels, dir_strength, dir_angle, mu,
    )

    # 对称层
    dir_sym = symmetry_check(image, sym_types, epsilon, translate_period)

    # ── S2：涌现贡献 ──────────────────────────────────────────

    # Em_pixel = top = 1 （无更精细层），log 域 = 0
    # Em_region = (f1)_!(Dir_pixel)
    # 对数域中：Dir_pixel = exp(dir_pixel_log)
    em_region = float(f1_shriek_from_log(dir_pixel_log, alpha, K))

    # Em_sym 通常为 top（简化，见 §2.6 S2 说明）
    # (f2)_!(dir_region) 和 (f2)_!(em_region) 只要有限就为 1

    # ── S3：总评分 ────────────────────────────────────────────

    score_pixel_log = dir_pixel_log  # ×1 = 不变（log 域 +0）
    score_region = dir_region + em_region
    score_sym = dir_sym  # ∧ top = 不变

    # ── S4：截面化闭包（逆拓扑序：sym → region → pixel）─────

    cl_sym = score_sym

    if not cl_sym:
        # 对称坍缩 → f2*(0) = INF → 区域坍缩
        cl_region = COST_INF
    else:
        # f2*(1) = 0, max(score_region, 0) = score_region
        cl_region = max(score_region, f2_star(int(cl_sym)))

    # cl_pixel_log = min(score_pixel_log, ln(f1*(cl_region)))
    cl_pixel_log_from_region = float(f1_star_log(cl_region, alpha, K))
    cl_pixel_log = min(score_pixel_log, cl_pixel_log_from_region)

    # ── 诊断 ──────────────────────────────────────────────────

    closure_correction_pixel = cl_pixel_log - score_pixel_log
    closure_correction_region = cl_region - score_region

    total_pixel_correction = max(score_pixel_log - cl_pixel_log, 0.0)
    neg_prefs = np.maximum(-prefs_log, 0.0)
    neg_sum = float(np.sum(neg_prefs))
    if total_pixel_correction > 0.0 and neg_sum > 0.0:
        closure_map = total_pixel_correction * (neg_prefs / neg_sum)
    else:
        closure_map = np.zeros_like(prefs_log, dtype=np.float64)

    # 坍缩判定
    # 1) 像素层：逐像素平均 log 偏好低于阈值
    # 2) 区域层：检查闭包后的区域评分
    # 3) 对称层：对称破缺即坍缩
    n_pixels = max(image.shape[0] * image.shape[1], 1)
    avg_cl_pixel_log = cl_pixel_log / n_pixels
    is_collapsed = (
        (avg_cl_pixel_log <= LN_PROB_FLOOR)
        or (cl_region >= COST_INF * 0.9)
        or (not cl_sym)
    )

    return LayerScores(
        dir_pixel=dir_pixel_log,
        dir_region=dir_region,
        dir_sym=dir_sym,
        em_region=em_region,
        score_pixel=score_pixel_log,
        score_region=score_region,
        score_sym=score_sym,
        cl_pixel=cl_pixel_log,
        cl_region=cl_region,
        cl_sym=cl_sym,
        closure_correction_pixel=closure_correction_pixel,
        closure_correction_region=closure_correction_region,
        is_collapsed=is_collapsed,
        region_heatmap=heatmap,
        pixel_prefs=prefs_log,
        closure_map=closure_map,
        C_H=C_H,
        C_V=C_V,
    )
