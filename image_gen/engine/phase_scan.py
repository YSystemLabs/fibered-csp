"""相图扫描引擎。

实现 §4.7：参数网格生成、批量退火、序参量收集、α_c 估计。
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from .order_params import compute_order_params
from .scoring import compute_scores
from .search import generate_targets, simulated_annealing


@dataclass
class SweepResult:
    """扫描结果。"""
    axis_x_values: list[float]
    axis_y_values: list[float]                      # 1D 扫描时为 [0.0]
    order_params: dict[str, list[list[float]]]       # {id: [[y0_x0, ...], ...]}
    thumbnails: list[list[dict | None]]              # 采样的 {image, params}
    estimated_alpha_c: float | None
    total_time: float


def run_sweep(
    base_params: dict,
    axis_x: dict,
    axis_y: dict | None,
    order_param_ids: list[str],
    thumbnail_stride: int = 4,
    callback: Callable | None = None,
    cancel_event: threading.Event | None = None,
) -> SweepResult:
    """执行相图扫描。

    Parameters
    ----------
    base_params : 基线参数（与 /api/generate 相同键）
    axis_x      : {"param": str, "min": float, "max": float, "steps": int}
    axis_y      : 同上（None → 1D 扫描）
    order_param_ids : 需要计算的序参量标识符
    thumbnail_stride : 缩略图采样步长
    callback    : 进度回调 (completed, total, last_order_params)
    """
    t0 = time.time()

    # §4.7.1 参数网格
    x_vals = np.linspace(
        axis_x["min"], axis_x["max"], axis_x["steps"],
    ).tolist()
    if axis_y is not None:
        y_vals = np.linspace(
            axis_y["min"], axis_y["max"], axis_y["steps"],
        ).tolist()
    else:
        y_vals = [0.0]

    steps_x = len(x_vals)
    steps_y = len(y_vals)
    total = steps_x * steps_y

    # 初始化结果容器
    op_results: dict[str, list[list[float]]] = {
        k: [[0.0] * steps_x for _ in range(steps_y)]
        for k in order_param_ids
    }
    thumbnails: list[list[dict | None]] = [
        [None] * steps_x for _ in range(steps_y)
    ]

    # §4.7.6 种子策略：每个网格点共用相同 seed
    seed = base_params.get("seed", 42)
    H = base_params.get("height", 16)
    W = base_params.get("width", 16)
    levels = base_params.get("levels", 8)
    target_mode = base_params.get("target_mode", "random_smooth")
    max_iter = base_params.get("max_iter", 30000)
    color_mode = base_params.get("color_mode", "grayscale")
    channels = 3 if color_mode == "rgb" else 1

    # 目标色只生成一次（种子固定）
    rng_targets = np.random.default_rng(seed)
    targets = generate_targets(H, W, levels, target_mode, rng_targets, channels=channels)

    completed = 0

    for yi, yv in enumerate(y_vals):
        for xi, xv in enumerate(x_vals):
            if cancel_event is not None and cancel_event.is_set():
                return SweepResult(
                    axis_x_values=x_vals,
                    axis_y_values=y_vals,
                    order_params=op_results,
                    thumbnails=thumbnails,
                    estimated_alpha_c=None,
                    total_time=time.time() - t0,
                )
            # 合并参数
            run_params = dict(base_params)
            run_params[axis_x["param"]] = xv
            if axis_y is not None:
                run_params[axis_y["param"]] = yv

            # §4.7.2 生成
            img, scores = simulated_annealing(
                H, W, targets, run_params,
                levels=levels,
                max_iter=max_iter,
                seed=seed,
            )

            # §4.7.3 序参量计算
            ops = compute_order_params(
                img, scores, run_params, order_param_ids,
            )
            for k in order_param_ids:
                op_results[k][yi][xi] = ops[k]

            # §4.7.4 缩略图采样
            flat_idx = yi * steps_x + xi
            if flat_idx % thumbnail_stride == 0:
                thumb_params = {axis_x["param"]: xv}
                if axis_y is not None:
                    thumb_params[axis_y["param"]] = yv
                thumbnails[yi][xi] = {
                    "image": img.tolist(),
                    **thumb_params,
                }

            completed += 1
            if callback is not None:
                callback(completed, total, ops)

    # §4.7.5 α_c 估计
    estimated_alpha_c = _estimate_alpha_c(
        axis_x, x_vals, op_results, order_param_ids,
    )

    return SweepResult(
        axis_x_values=x_vals,
        axis_y_values=y_vals,
        order_params=op_results,
        thumbnails=thumbnails,
        estimated_alpha_c=estimated_alpha_c,
        total_time=time.time() - t0,
    )


def _estimate_alpha_c(
    axis_x: dict,
    x_vals: list[float],
    op_results: dict[str, list[list[float]]],
    order_param_ids: list[str],
) -> float | None:
    """若 X 轴为 alpha 且有 phi_em，返回 |dφ_em/dα| 最大处的 α。"""
    if axis_x["param"] != "alpha":
        return None
    if "phi_em" not in order_param_ids:
        return None

    # 取第一行（1D）或 y 中间行
    phi_em_row = op_results["phi_em"][len(op_results["phi_em"]) // 2]
    if len(phi_em_row) < 3:
        return None

    # 数值梯度
    arr = np.array(phi_em_row)
    grad = np.gradient(arr, x_vals)
    abs_grad = np.abs(grad)
    idx = int(np.argmax(abs_grad))
    return x_vals[idx]
