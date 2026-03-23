"""FastAPI 服务器。

实现 §4.5：API 端点 /api/generate, /api/score, /api/sweep, /api/defaults。
静态文件服务。
"""

from __future__ import annotations

import asyncio
import json
import queue
import threading
import time
from pathlib import Path

import numpy as np
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from engine.scoring import LayerScores, compute_scores
from engine.search import generate_targets, simulated_annealing
from engine.order_params import compute_order_params
from engine.phase_scan import run_sweep

app = FastAPI(title="Fibered CSP Image Generator")

STATIC_DIR = Path(__file__).parent / "static"

# ── 静态文件 ──────────────────────────────────────────────────────

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index():
    html_path = STATIC_DIR / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    return HTMLResponse("<h1>Fibered CSP Image Generator</h1><p>static/index.html not found</p>")


# ── 默认参数 ──────────────────────────────────────────────────────

DEFAULTS = {
    "width":     {"value": 16, "min": 4, "max": 64, "step": 1},
    "height":    {"value": 16, "min": 4, "max": 64, "step": 1},
    "levels":    {"value": 8,  "options": [4, 8, 16, 32]},
    "color_mode": {"value": "grayscale", "options": ["grayscale", "rgb"]},
    "seed":      {"value": 42, "min": 0, "max": 999999, "step": 1},
    "target_mode": {"value": "random_smooth",
                    "options": ["random_uniform", "random_smooth",
                                "gradient_h", "gradient_v",
                                "checkerboard", "center_blob"]},
    "max_iter":  {"value": 30000, "min": 1000, "max": 500000, "step": 100},
    "T_init":    {"value": 10.0, "min": 0.1, "max": 100.0},
    "T_min":     {"value": 0.01, "min": 0.001, "max": 1.0},
    "cooling":   {"value": 0.9995, "min": 0.990, "max": 0.9999, "step": 0.0001},
    "alpha":     {"value": 0.5, "min": 0.01, "max": 1.0, "step": 0.01},
    "K":         {"value": 255, "min": 10, "max": 1000, "step": 5},
    "sigma":     {"value": 0.3, "min": 0.05, "max": 2.0, "step": 0.01},
    "tau":       {"value": 0.3, "min": 0.05, "max": 0.95, "step": 0.01},
    "beta":      {"value": 5.0, "min": 0.1, "max": 20.0, "step": 0.1},
    "gamma":     {"value": 10.0, "min": 0.1, "max": 30.0, "step": 0.1},
    "mu":        {"value": 0.0, "min": 0.0, "max": 50.0, "step": 0.1},
    "dir_strength": {"value": 0.0, "min": -1.0, "max": 1.0, "step": 0.1},
    "dir_angle": {"value": 0, "min": 0, "max": 180, "step": 5},
    "symmetry":  {"value": ["none"],
                  "options": ["none", "lr", "ud", "quad", "c4", "trans_h"]},
    "epsilon":   {"value": 0, "min": 0, "max": 16, "step": 1},
    "translate_period": {"value": 4, "min": 2, "max": 64, "step": 1},
    "w_pixel":  {"value": 0.1, "min": 0.001, "max": 10.0, "step": 0.001},
}


def _fill_defaults(body: dict) -> dict:
    """补全缺失参数为默认值。"""
    params = {}
    for key, spec in DEFAULTS.items():
        params[key] = body.get(key, spec["value"])
    return params


def _validate_params(params: dict) -> None:
    """基础参数校验，非法时抛出 ValueError。"""
    width = int(params["width"])
    height = int(params["height"])
    levels = int(params["levels"])
    color_mode = params["color_mode"]
    alpha = float(params["alpha"])
    K = float(params["K"])
    sigma = float(params["sigma"])
    tau = float(params["tau"])
    beta = float(params["beta"])
    gamma = float(params["gamma"])
    dir_strength = float(params["dir_strength"])
    dir_angle = float(params["dir_angle"])
    max_iter = int(params["max_iter"])
    translate_period = int(params["translate_period"])
    symmetry = params.get("symmetry", ["none"])

    if not (4 <= width <= 64):
        raise ValueError("width 必须在 [4, 64] 内")
    if not (4 <= height <= 64):
        raise ValueError("height 必须在 [4, 64] 内")
    if levels not in {4, 8, 16, 32}:
        raise ValueError("levels 必须为 4/8/16/32 之一")
    if color_mode not in {"grayscale", "rgb"}:
        raise ValueError("color_mode 必须为 grayscale 或 rgb")
    if not (0.0 < alpha <= 1.0):
        raise ValueError("alpha 必须在 (0, 1] 内")
    if K <= 0.0:
        raise ValueError("K 必须为正数")
    if sigma <= 0.0:
        raise ValueError("sigma 必须为正数")
    if not (0.0 < tau < 1.0):
        raise ValueError("tau 必须在 (0, 1) 内")
    if beta <= 0.0:
        raise ValueError("beta 必须为正数")
    if gamma <= 0.0:
        raise ValueError("gamma 必须为正数")
    if not (-1.0 <= dir_strength <= 1.0):
        raise ValueError("dir_strength 必须在 [-1, 1] 内")
    if not (0.0 <= dir_angle <= 180.0):
        raise ValueError("dir_angle 必须在 [0, 180] 内")
    if max_iter < 1:
        raise ValueError("max_iter 必须为正整数")
    if translate_period < 2 or translate_period > width:
        raise ValueError("translate_period 必须在 [2, width] 内")

    sym_set = set(symmetry)
    valid_sym = set(DEFAULTS["symmetry"]["options"])
    if not sym_set.issubset(valid_sym):
        raise ValueError("symmetry 含非法选项")
    if "c4" in sym_set and width != height:
        raise ValueError("选择 c4 对称时必须满足 width == height")


def _bad_request(message: str) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": message})


def _scores_to_dict(s: LayerScores) -> dict:
    """LayerScores → JSON 可序列化字典。"""
    return {
        "dir_pixel_log": s.dir_pixel,
        "dir_region": s.dir_region,
        "dir_sym": s.dir_sym,
        "em_region": s.em_region,
        "score_pixel_log": s.score_pixel,
        "score_region": s.score_region,
        "score_sym": s.score_sym,
        "cl_pixel_log": s.cl_pixel,
        "cl_region": s.cl_region,
        "cl_sym": s.cl_sym,
        "closure_correction_pixel": s.closure_correction_pixel,
        "closure_correction_region": s.closure_correction_region,
        "is_collapsed": s.is_collapsed,
    }


# ── §4.5.1 GET /api/defaults ─────────────────────────────────────

@app.get("/api/defaults")
async def get_defaults():
    return DEFAULTS


# ── §4.5.2 POST /api/generate ────────────────────────────────────

@app.post("/api/generate")
async def api_generate(request: Request):
    body = await request.json()
    params = _fill_defaults(body)
    try:
        _validate_params(params)
    except ValueError as exc:
        return _bad_request(str(exc))

    H = params["width"]    # 注意：spec 中 width=W
    W = params["height"]
    # 修正：width → W (列数), height → H (行数)
    H, W = params["height"], params["width"]
    levels = params["levels"]
    seed = params["seed"]
    target_mode = params["target_mode"]
    max_iter = params["max_iter"]

    rng = np.random.default_rng(seed)
    color_mode = params.get("color_mode", "grayscale")
    channels = 3 if color_mode == "rgb" else 1
    targets = generate_targets(H, W, levels, target_mode, rng, channels=channels)

    t0 = time.time()
    img, scores = await asyncio.to_thread(
        simulated_annealing,
        H, W, targets, params,
        levels=levels,
        max_iter=max_iter,
        T_init=params.get("T_init", 10.0),
        T_min=params.get("T_min", 0.01),
        cooling=params.get("cooling", 0.9995),
        seed=seed,
    )
    elapsed = time.time() - t0

    # 基本域信息
    from engine.search import compute_basic_domain
    from engine.constraints import SymmetryType
    sym_types = [SymmetryType(s) for s in params["symmetry"]]
    bd, _ = compute_basic_domain(H, W, sym_types, params["translate_period"])

    return {
        "image": img.tolist(),
        "targets": targets.tolist(),
        "scores": _scores_to_dict(scores),
        "region_heatmap": (
            scores.region_heatmap.tolist()
            if scores.region_heatmap is not None else None
        ),
        "closure_map": (
            scores.closure_map.tolist()
            if scores.closure_map is not None else None
        ),
        "metadata": {
            "iterations_used": max_iter,
            "time_seconds": round(elapsed, 3),
            "free_pixels": len(bd),
            "total_pixels": H * W,
        },
    }


# ── POST /api/score ──────────────────────────────────────────────

@app.post("/api/score")
async def api_score(request: Request):
    body = await request.json()
    image = np.array(body["image"], dtype=int)
    targets = np.array(body["targets"], dtype=int)
    params = _fill_defaults(body.get("params", {}))
    try:
        _validate_params(params)
    except ValueError as exc:
        return _bad_request(str(exc))
    scores = compute_scores(image, targets, params)
    return {"scores": _scores_to_dict(scores)}


# ── §4.5.3 POST /api/sweep ──────────────────────────────────────
# SSE 流式推送进度（§5.6.4）

@app.post("/api/sweep")
async def api_sweep(request: Request):
    body = await request.json()
    base_params = _fill_defaults(body.get("base_params", {}))
    try:
        _validate_params(base_params)
    except ValueError as exc:
        return _bad_request(str(exc))
    sweep = body["sweep"]
    axis_x = sweep["axis_x"]
    axis_y = sweep.get("axis_y")
    order_param_ids = body.get("order_params", ["phi_em", "phi_cl"])
    stream = bool(body.get("stream", False))

    if not stream:
        result = await asyncio.to_thread(
            run_sweep,
            base_params=base_params,
            axis_x=axis_x,
            axis_y=axis_y,
            order_param_ids=order_param_ids,
        )

        return {
            "axis_x": {"param": axis_x["param"], "values": result.axis_x_values},
            "axis_y": {
                "param": axis_y["param"] if axis_y else None,
                "values": result.axis_y_values,
            },
            "results": result.order_params,
            "thumbnails": result.thumbnails,
            "metadata": {
                "total_runs": len(result.axis_x_values) * len(result.axis_y_values),
                "time_seconds": round(result.total_time, 3),
                "estimated_alpha_c": result.estimated_alpha_c,
            },
        }

    async def event_stream():
        q: queue.Queue = queue.Queue()
        cancel_event = threading.Event()

        def _worker() -> None:
            try:
                result = run_sweep(
                    base_params=base_params,
                    axis_x=axis_x,
                    axis_y=axis_y,
                    order_param_ids=order_param_ids,
                    callback=lambda completed, total, ops: q.put(("progress", {
                        "completed": completed,
                        "total": total,
                        "last_order_params": ops,
                    })),
                    cancel_event=cancel_event,
                )
                q.put(("done", {
                    "axis_x": {"param": axis_x["param"], "values": result.axis_x_values},
                    "axis_y": {
                        "param": axis_y["param"] if axis_y else None,
                        "values": result.axis_y_values,
                    },
                    "results": result.order_params,
                    "thumbnails": result.thumbnails,
                    "metadata": {
                        "total_runs": len(result.axis_x_values) * len(result.axis_y_values),
                        "time_seconds": round(result.total_time, 3),
                        "estimated_alpha_c": result.estimated_alpha_c,
                    },
                }))
            except Exception as exc:  # pragma: no cover
                q.put(("error", {"message": str(exc)}))

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

        while True:
            if await request.is_disconnected():
                cancel_event.set()
                break
            try:
                event, payload = q.get(timeout=0.2)
            except queue.Empty:
                continue
            yield f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
            if event in {"done", "error"}:
                break

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── 启动入口 ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
