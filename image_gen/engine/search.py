"""搜索引擎：模拟退火 + 对称约束消元。

实现 §4.4 + §6.1 + §6.3：
- 目标色生成（6 种策略）
- 对称基本域计算与轨道枚举
- 增量评分（O(1) per step）
- 模拟退火主循环（Metropolis 判据）
"""

from __future__ import annotations

from typing import Callable

import numpy as np

from .constraints import SymmetryType
from .fibers import COST_INF, f1_shriek_from_log, f1_star_log
from .scoring import LayerScores, compute_scores


# ═══════════════════════════════════════════════════════════════════
# §4.4.4 目标色生成策略
# ═══════════════════════════════════════════════════════════════════

def generate_targets(
    H: int, W: int, levels: int, mode: str,
    rng: np.random.Generator,
    channels: int = 1,
) -> np.ndarray:
    """生成目标色图案。

    channels=1 → (H, W) int，channels=3 → (H, W, 3) int。值域 [0, levels-1]。
    """
    L = levels

    if channels == 3:
        return _generate_targets_rgb(H, W, L, mode, rng)

    if mode == "random_uniform":
        return rng.integers(0, L, size=(H, W))

    if mode == "random_smooth":
        small_h, small_w = max(2, H // 4), max(2, W // 4)
        small = rng.integers(0, L, size=(small_h, small_w)).astype(np.float64)
        return _bilinear_upsample(small, H, W, L)

    if mode == "gradient_h":
        row = np.linspace(0, L - 1, W)
        return np.round(np.broadcast_to(row, (H, W))).astype(int)

    if mode == "gradient_v":
        col = np.linspace(0, L - 1, H).reshape(-1, 1)
        return np.round(np.broadcast_to(col, (H, W))).astype(int)

    if mode == "checkerboard":
        ii, jj = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
        return ((ii + jj) % 2 * (L - 1)).astype(int)

    if mode == "center_blob":
        cy, cx = (H - 1) / 2.0, (W - 1) / 2.0
        yy, xx = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
        sig = min(H, W) / 4.0
        gauss = np.exp(-((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * sig ** 2))
        return np.round(gauss * (L - 1)).astype(int)

    raise ValueError(f"Unknown target mode: {mode!r}")


def _bilinear_upsample(
    small: np.ndarray, H: int, W: int, L: int,
) -> np.ndarray:
    """双线性插值放大小图到 (H, W)。"""
    sh, sw = small.shape
    y = np.linspace(0, sh - 1, H)
    x = np.linspace(0, sw - 1, W)
    yi = np.clip(np.floor(y).astype(int), 0, sh - 2)
    yf = (y - yi).reshape(-1, 1)
    xi = np.clip(np.floor(x).astype(int), 0, sw - 2)
    xf = (x - xi).reshape(1, -1)
    f00 = small[np.ix_(yi, xi)]
    f01 = small[np.ix_(yi, xi + 1)]
    f10 = small[np.ix_(yi + 1, xi)]
    f11 = small[np.ix_(yi + 1, xi + 1)]
    result = (
        f00 * (1 - yf) * (1 - xf)
        + f01 * (1 - yf) * xf
        + f10 * yf * (1 - xf)
        + f11 * yf * xf
    )
    return np.clip(np.round(result), 0, L - 1).astype(int)


def _t_to_rgb(t: np.ndarray, L: int) -> np.ndarray:
    """将 [0,1] 标量场映射为 RGB 数组 (*, 3)，值域 [0, L-1]。

    使用余弦色环：R/G/B 相位间隔 120°。
    """
    r = 0.5 + 0.5 * np.cos(2.0 * np.pi * t)
    g = 0.5 + 0.5 * np.cos(2.0 * np.pi * (t - 1.0 / 3.0))
    b = 0.5 + 0.5 * np.cos(2.0 * np.pi * (t - 2.0 / 3.0))
    rgb = np.stack([r, g, b], axis=-1)
    return np.clip(np.round(rgb * (L - 1)), 0, L - 1).astype(int)


def _generate_targets_rgb(
    H: int, W: int, L: int, mode: str, rng: np.random.Generator,
) -> np.ndarray:
    """生成 RGB 目标色图案，返回 (H, W, 3) int。"""

    if mode == "random_uniform":
        return rng.integers(0, L, size=(H, W, 3))

    if mode == "random_smooth":
        small_h, small_w = max(2, H // 4), max(2, W // 4)
        chs = []
        for _ in range(3):
            small = rng.integers(0, L, size=(small_h, small_w)).astype(np.float64)
            chs.append(_bilinear_upsample(small, H, W, L))
        return np.stack(chs, axis=-1)

    if mode == "gradient_h":
        t = np.broadcast_to(np.linspace(0.0, 1.0, W), (H, W))
        return _t_to_rgb(t, L)

    if mode == "gradient_v":
        t = np.broadcast_to(np.linspace(0.0, 1.0, H).reshape(-1, 1), (H, W))
        return _t_to_rgb(t, L)

    if mode == "checkerboard":
        c0, c1 = rng.integers(0, L, size=3), rng.integers(0, L, size=3)
        ii, jj = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
        mask = ((ii + jj) % 2).astype(bool)
        result = np.zeros((H, W, 3), dtype=int)
        result[~mask] = c0
        result[mask] = c1
        return result

    if mode == "center_blob":
        cy, cx = (H - 1) / 2.0, (W - 1) / 2.0
        yy, xx = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
        sig = max(min(H, W) / 4.0, 1.0)
        gauss = np.exp(-((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * sig ** 2))
        fg = rng.integers(0, L, size=3).astype(float)
        bg = rng.integers(0, L, size=3).astype(float)
        result = np.zeros((H, W, 3), dtype=float)
        for c in range(3):
            result[:, :, c] = bg[c] + gauss * (fg[c] - bg[c])
        return np.clip(np.round(result), 0, L - 1).astype(int)

    raise ValueError(f"Unknown target mode: {mode!r}")


# ═══════════════════════════════════════════════════════════════════
# §4.4.2 对称约束消元
# ═══════════════════════════════════════════════════════════════════

def _compute_orbit(
    i: int, j: int, H: int, W: int,
    sym_types: list[SymmetryType],
    translate_period: int,
) -> list[tuple[int, int]]:
    """计算 (i,j) 在所有启用对称下的完整轨道（传递闭包）。"""
    orbit: set[tuple[int, int]] = {(i, j)}
    changed = True
    while changed:
        changed = False
        new_pts: set[tuple[int, int]] = set()
        for pi, pj in orbit:
            for st in sym_types:
                if st == SymmetryType.NONE:
                    continue
                elif st == SymmetryType.LEFT_RIGHT:
                    new_pts.add((pi, W - 1 - pj))
                elif st == SymmetryType.UP_DOWN:
                    new_pts.add((H - 1 - pi, pj))
                elif st == SymmetryType.QUAD:
                    new_pts.add((pi, W - 1 - pj))
                    new_pts.add((H - 1 - pi, pj))
                    new_pts.add((H - 1 - pi, W - 1 - pj))
                elif st == SymmetryType.ROTATE_C4:
                    N = H  # 需 H == W
                    new_pts.add((pj, N - 1 - pi))
                    new_pts.add((N - 1 - pi, N - 1 - pj))
                    new_pts.add((N - 1 - pj, pi))
                elif st == SymmetryType.TRANSLATE_H:
                    T = translate_period
                    base_j = pj % T
                    for kk in range(0, W, T):
                        nj = base_j + kk
                        if nj < W:
                            new_pts.add((pi, nj))
        added = new_pts - orbit
        if added:
            orbit |= added
            changed = True
    return sorted(orbit)


def compute_basic_domain(
    H: int, W: int,
    sym_types: list[SymmetryType],
    translate_period: int = 4,
) -> tuple[list[tuple[int, int]], dict[tuple[int, int], list[tuple[int, int]]]]:
    """计算基本域和轨道映射。

    返回
    ----
    (basic_domain, orbit_map)
    basic_domain : 代表元列表（字典序排列）
    orbit_map    : {代表元: 完整轨道列表}
    """
    seen: set[tuple[int, int]] = set()
    orbit_map: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for i in range(H):
        for j in range(W):
            if (i, j) in seen:
                continue
            orbit = _compute_orbit(i, j, H, W, sym_types, translate_period)
            rep = orbit[0]  # 字典序最小
            orbit_map[rep] = orbit
            seen.update(orbit)

    basic_domain = sorted(orbit_map.keys())
    return basic_domain, orbit_map


def fill_from_basic_domain(
    image: np.ndarray,
    orbit_map: dict[tuple[int, int], list[tuple[int, int]]],
    epsilon: float = 0.0,
    levels: int = 8,
    rng: np.random.Generator | None = None,
) -> None:
    """根据代表元的值填充完整图像（in-place）。"""
    is_rgb = image.ndim == 3
    for rep, orbit in orbit_map.items():
        val = image[rep].copy() if is_rgb else int(image[rep])
        for pi, pj in orbit:
            if (pi, pj) == rep:
                continue
            if epsilon > 0.0 and rng is not None:
                if is_rgb:
                    noise = rng.integers(
                        -int(epsilon / 2), int(epsilon / 2) + 1, size=3,
                    )
                    image[pi, pj] = np.clip(val + noise, 0, levels - 1)
                else:
                    noise = int(rng.integers(
                        -int(epsilon / 2), int(epsilon / 2) + 1,
                    ))
                    image[pi, pj] = int(np.clip(val + noise, 0, levels - 1))
            else:
                image[pi, pj] = val


# ═══════════════════════════════════════════════════════════════════
# §6.1 增量评分辅助函数
# ═══════════════════════════════════════════════════════════════════

def _direction_weights(
    dir_strength: float, dir_angle: float,
) -> tuple[float, float]:
    """返回 (w_h, w_v) 方向权重，与 constraints.region_costs 一致。"""
    if dir_strength == 0.0:
        return 1.0, 1.0
    theta0 = np.radians(dir_angle)
    w_h = 1.0 + dir_strength * np.cos(2.0 * (0.0 - theta0))
    w_v = 1.0 + dir_strength * np.cos(2.0 * (np.pi / 2.0 - theta0))
    return float(w_h), float(w_v)


def _pair_cost(
    v1, v2,
    tau: float, beta: float, gamma: float,
    norm: float, weight: float,
    mu: float = 0.0,
) -> float:
    """单对边缘感知 Potts 代价（支持标量和向量像素值）。"""
    diff = (np.asarray(v1, dtype=float) - np.asarray(v2, dtype=float)) / norm
    d = float(np.sqrt(np.sum(diff ** 2)))
    return ((gamma - mu) * d if d <= tau else beta * d) * weight


def _incremental_delta(
    image: np.ndarray,
    changes: list[tuple],
    targets: np.ndarray,
    sigma: float,
    tau: float, beta: float, gamma: float,
    levels: int,
    dir_strength: float, dir_angle: float,
    mu: float = 0.0,
) -> tuple[float, float]:
    """计算增量 (Δpixel_log, Δregion)。

    image   : 更新前状态 (H,W) 或 (H,W,3)
    changes : [(i, j, new_val), ...] 所有同时变更的像素
              new_val 为 int（灰度）或 ndarray（RGB）

    §6.1 增量公式 + §4.4.3 双端更新边界处理。
    """
    H, W = image.shape[:2]
    channels = image.shape[-1] if image.ndim == 3 else 1
    norm = float((levels - 1) * np.sqrt(channels))
    w_h, w_v = _direction_weights(dir_strength, dir_angle)

    # 构建变更查找表
    change_map = {(ci, cj): nv for ci, cj, nv in changes}

    # ── 像素层增量（Δ ln φ_p） ────────────────────
    d_pixel = 0.0
    for ci, cj, nv in changes:
        ov = image[ci, cj]
        t = targets[ci, cj]
        diff_old = (np.asarray(ov, dtype=float) - np.asarray(t, dtype=float)) / norm
        diff_new = (np.asarray(nv, dtype=float) - np.asarray(t, dtype=float)) / norm
        d_old_sq = float(np.sum(diff_old ** 2))
        d_new_sq = float(np.sum(diff_new ** 2))
        d_pixel += -(d_new_sq - d_old_sq) / (2.0 * sigma ** 2)

    # ── 区域层增量（Δ Σ φ_R） ──────────────────────
    # §4.4.3 注：镜像像素互为邻居时走双端更新路径
    d_region = 0.0
    processed: set[tuple[tuple[int, int], tuple[int, int]]] = set()

    for ci, cj, _ in changes:
        # 4-邻域：(di, dj, is_horizontal)
        for di, dj, is_h in ((-1, 0, False), (1, 0, False),
                             (0, -1, True), (0, 1, True)):
            ni, nj = ci + di, cj + dj
            if not (0 <= ni < H and 0 <= nj < W):
                continue
            pair = (min((ci, cj), (ni, nj)), max((ci, cj), (ni, nj)))
            if pair in processed:
                continue
            processed.add(pair)

            w = w_h if is_h else w_v
            ov_c = image[ci, cj]
            ov_n = image[ni, nj]
            old_cost = _pair_cost(ov_c, ov_n, tau, beta, gamma, norm, w, mu)

            # 新值（可能一端或两端变化）
            nv_c = change_map.get((ci, cj), ov_c)
            nv_n = change_map.get((ni, nj), ov_n)
            new_cost = _pair_cost(nv_c, nv_n, tau, beta, gamma, norm, w, mu)

            d_region += new_cost - old_cost

    return d_pixel, d_region


# ═══════════════════════════════════════════════════════════════════
# §4.4.1 + §6.3 模拟退火
# ═══════════════════════════════════════════════════════════════════

def simulated_annealing(
    H: int, W: int,
    targets: np.ndarray,
    params: dict,
    levels: int = 8,
    max_iter: int = 50000,
    T_init: float = 10.0,
    T_min: float = 0.01,
    cooling: float = 0.9995,
    seed: int | None = None,
    callback: Callable | None = None,
) -> tuple[np.ndarray, LayerScores]:
    """模拟退火搜索，返回 (最优图像, 最终评分)。"""
    rng = np.random.default_rng(seed)

    # ── 参数解包 ──────────────────────────────────────────
    alpha = params.get("alpha", 0.5)
    K = params.get("K", 255.0)
    sigma = params.get("sigma", 0.3)
    tau = params.get("tau", 0.3)
    beta = params.get("beta", 5.0)
    gamma = params.get("gamma", 10.0)
    mu = params.get("mu", 0.0)
    dir_strength = params.get("dir_strength", 0.0)
    dir_angle = params.get("dir_angle", 0.0)
    sym_strs = params.get("symmetry", ["none"])
    epsilon = params.get("epsilon", 0.0)
    translate_period = params.get("translate_period", 4)

    sym_types = [SymmetryType(s) for s in sym_strs]

    # §6.3 目标函数权重
    W_REGION = 1.0
    W_PIXEL = params.get("w_pixel", 0.1)

    def _closure_objective(dir_pixel_log_val: float, dir_region_val: float) -> float:
        em_region_val = float(f1_shriek_from_log(dir_pixel_log_val, alpha, K))
        score_region_val = dir_region_val + em_region_val
        cl_region_val = score_region_val
        cl_pixel_log_val = min(dir_pixel_log_val, float(f1_star_log(cl_region_val, alpha, K)))
        if cl_region_val >= COST_INF * 0.9:
            return COST_INF
        return W_REGION * cl_region_val - W_PIXEL * cl_pixel_log_val

    # ── 基本域预计算（§4.4.2） ────────────────────────────
    basic_domain, orbit_map = compute_basic_domain(
        H, W, sym_types, translate_period,
    )
    n_free = len(basic_domain)

    # ── 初始赋值：随机 + 对称填充 ────────────────────────
    is_rgb = targets.ndim == 3
    if is_rgb:
        image = np.zeros((H, W, 3), dtype=int)
        for bi, bj in basic_domain:
            image[bi, bj] = rng.integers(0, levels, size=3)
    else:
        image = np.zeros((H, W), dtype=int)
        for bi, bj in basic_domain:
            image[bi, bj] = int(rng.integers(0, levels))
    fill_from_basic_domain(
        image, orbit_map, epsilon, levels,
        rng if epsilon > 0 else None,
    )

    # ── 初始全量评分 ──────────────────────────────────────
    scores = compute_scores(image, targets, params)
    dir_pixel_log = scores.dir_pixel      # log 域
    dir_region = scores.dir_region        # 代价域

    # §6.3 closure-aware Obj = w_r * cl_region - w_p * cl_pixel_log
    obj = _closure_objective(dir_pixel_log, dir_region)

    best_image = image.copy()
    best_obj = obj

    T = T_init

    for it in range(max_iter):
        if T < T_min:
            T = T_min

        # §4.4.3 自适应步长
        k = max(1, min(int(T), levels - 1))

        # 选取基本域像素
        idx = int(rng.integers(0, n_free))
        ri, rj = basic_domain[idx]

        # 提议偏移
        if is_rgb:
            old_pixel = image[ri, rj].copy()
            ch = int(rng.integers(0, 3))
            delta_v = int(rng.integers(-k, k + 1))
            if delta_v == 0:
                delta_v = 1 if rng.random() < 0.5 else -1
            new_pixel = old_pixel.copy()
            new_pixel[ch] = int(np.clip(old_pixel[ch] + delta_v, 0, levels - 1))
            proposal_changed = not np.array_equal(new_pixel, old_pixel)
        else:
            old_val = int(image[ri, rj])
            delta_v = int(rng.integers(-k, k + 1))
            if delta_v == 0:
                delta_v = 1 if rng.random() < 0.5 else -1
            new_val = int(np.clip(old_val + delta_v, 0, levels - 1))
            proposal_changed = new_val != old_val

        if proposal_changed:
            # 构造变更列表（含对称镜像，§4.4.3）
            orbit = orbit_map[(ri, rj)]
            changes: list[tuple] = []
            if is_rgb:
                for pi, pj in orbit:
                    if epsilon > 0.0 and (pi, pj) != (ri, rj):
                        noise = rng.integers(
                            -int(epsilon / 2), int(epsilon / 2) + 1, size=3,
                        )
                        nv = np.clip(new_pixel + noise, 0, levels - 1).astype(int)
                        changes.append((pi, pj, nv))
                    else:
                        changes.append((pi, pj, new_pixel.copy()))
            else:
                for pi, pj in orbit:
                    if epsilon > 0.0 and (pi, pj) != (ri, rj):
                        noise = int(rng.integers(
                            -int(epsilon / 2), int(epsilon / 2) + 1,
                        ))
                        nv = int(np.clip(new_val + noise, 0, levels - 1))
                        changes.append((pi, pj, nv))
                    else:
                        changes.append((pi, pj, new_val))

            # §6.1 增量评分
            d_pix, d_reg = _incremental_delta(
                image, changes, targets, sigma,
                tau, beta, gamma, levels, dir_strength, dir_angle, mu,
            )

            new_dir_pixel_log = dir_pixel_log + d_pix
            new_dir_region = dir_region + d_reg
            new_obj = _closure_objective(new_dir_pixel_log, new_dir_region)
            delta_obj = new_obj - obj

            # §6.3 Metropolis 判据
            if delta_obj <= 0.0:
                accept = True
            else:
                accept = rng.random() < np.exp(-delta_obj / max(T, 1e-15))

            if accept:
                for ci, cj, nv in changes:
                    image[ci, cj] = nv
                dir_pixel_log = new_dir_pixel_log
                dir_region = new_dir_region
                obj = new_obj

                if obj < best_obj:
                    best_image = image.copy()
                    best_obj = obj

        T *= cooling

        if callback is not None and (it + 1) % 1000 == 0:
            callback(it + 1, max_iter, obj, T)

    # ── 最终全量评分（best image） ─────────────────────
    final_scores = compute_scores(best_image, targets, params)
    return best_image, final_scores
