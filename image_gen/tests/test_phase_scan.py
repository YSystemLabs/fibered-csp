"""engine/phase_scan.py 单元测试。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest
import threading

from engine.phase_scan import run_sweep, SweepResult


def _base_params(**overrides):
    p = {
        "width": 6, "height": 6, "levels": 4,
        "color_mode": "grayscale",
        "target_mode": "random_smooth", "seed": 42,
        "max_iter": 500,  # 极短迭代以加速测试
        "alpha": 0.5, "K": 255.0,
        "sigma": 0.3, "tau": 0.3, "beta": 5.0, "gamma": 10.0,
        "dir_strength": 0.0, "dir_angle": 0.0,
        "symmetry": ["none"], "epsilon": 0.0, "translate_period": 4,
    }
    p.update(overrides)
    return p


class TestSweep1D:
    """1D 扫描（仅 X 轴）。"""

    def test_basic_1d(self):
        """1D alpha 扫描返回正确形状。"""
        result = run_sweep(
            base_params=_base_params(),
            axis_x={"param": "alpha", "min": 0.3, "max": 1.0, "steps": 3},
            axis_y=None,
            order_param_ids=["phi_em"],
        )
        assert isinstance(result, SweepResult)
        assert len(result.axis_x_values) == 3
        assert result.axis_y_values == [0.0]
        assert "phi_em" in result.order_params
        assert len(result.order_params["phi_em"]) == 1  # 1 row (1D)
        assert len(result.order_params["phi_em"][0]) == 3

    def test_alpha_c_estimated(self):
        """X 轴为 alpha + phi_em → 产生 α_c 估计。"""
        result = run_sweep(
            base_params=_base_params(),
            axis_x={"param": "alpha", "min": 0.1, "max": 1.0, "steps": 5},
            axis_y=None,
            order_param_ids=["phi_em"],
        )
        assert result.estimated_alpha_c is not None
        assert 0.1 <= result.estimated_alpha_c <= 1.0

    def test_no_alpha_c_when_not_alpha_axis(self):
        """X 轴非 alpha → 不估计 α_c。"""
        result = run_sweep(
            base_params=_base_params(),
            axis_x={"param": "tau", "min": 0.1, "max": 0.5, "steps": 3},
            axis_y=None,
            order_param_ids=["phi_em"],
        )
        assert result.estimated_alpha_c is None

    def test_callback_invoked(self):
        """回调被正确调用。"""
        calls = []
        result = run_sweep(
            base_params=_base_params(),
            axis_x={"param": "alpha", "min": 0.3, "max": 1.0, "steps": 3},
            axis_y=None,
            order_param_ids=["phi_em"],
            callback=lambda c, t, ops: calls.append((c, t)),
        )
        assert len(calls) == 3
        assert calls[-1] == (3, 3)

    def test_cancel_event_stops_early(self):
        cancel_event = threading.Event()
        calls = []

        def cb(c, t, ops):
            calls.append(c)
            if c == 2:
                cancel_event.set()

        result = run_sweep(
            base_params=_base_params(),
            axis_x={"param": "alpha", "min": 0.3, "max": 1.0, "steps": 5},
            axis_y=None,
            order_param_ids=["phi_em"],
            callback=cb,
            cancel_event=cancel_event,
        )
        assert len(calls) == 2
        assert isinstance(result, SweepResult)


class TestSweep2D:
    """2D 扫描。"""

    def test_basic_2d(self):
        """2D alpha × tau 扫描返回正确形状。"""
        result = run_sweep(
            base_params=_base_params(),
            axis_x={"param": "alpha", "min": 0.3, "max": 1.0, "steps": 3},
            axis_y={"param": "tau", "min": 0.1, "max": 0.5, "steps": 2},
            order_param_ids=["phi_em", "xi"],
        )
        assert len(result.axis_x_values) == 3
        assert len(result.axis_y_values) == 2
        # phi_em: [2][3] 矩阵
        assert len(result.order_params["phi_em"]) == 2
        assert len(result.order_params["phi_em"][0]) == 3


class TestThumbnails:
    """缩略图采样。"""

    def test_stride_sampling(self):
        """thumbnail_stride 控制采样频率。"""
        result = run_sweep(
            base_params=_base_params(),
            axis_x={"param": "alpha", "min": 0.3, "max": 1.0, "steps": 4},
            axis_y=None,
            order_param_ids=["phi_em"],
            thumbnail_stride=2,
        )
        # flat indices: 0, 1, 2, 3 → stride=2 → 采样 0, 2
        thumbnails_row = result.thumbnails[0]
        assert thumbnails_row[0] is not None
        assert thumbnails_row[1] is None
        assert thumbnails_row[2] is not None
        assert thumbnails_row[3] is None


class TestMultipleOrderParams:
    """多序参量同时请求。"""

    def test_all_five(self):
        """请求全部 5 个序参量。"""
        result = run_sweep(
            base_params=_base_params(),
            axis_x={"param": "alpha", "min": 0.5, "max": 1.0, "steps": 2},
            axis_y=None,
            order_param_ids=["phi_em", "phi_cl", "xi", "phi_dir", "phi_mirror"],
        )
        assert len(result.order_params) == 5
        for k in ["phi_em", "phi_cl", "xi", "phi_dir", "phi_mirror"]:
            assert k in result.order_params
            # 值应为 float
            assert isinstance(result.order_params[k][0][0], float)


class TestSweepRGB:

    def test_rgb_mode_runs(self):
        result = run_sweep(
            base_params=_base_params(color_mode="rgb"),
            axis_x={"param": "alpha", "min": 0.5, "max": 1.0, "steps": 2},
            axis_y=None,
            order_param_ids=["phi_em"],
            thumbnail_stride=1,
        )
        thumb = result.thumbnails[0][0]
        assert thumb is not None
        # RGB 图像最内层应为 3 通道
        assert len(thumb["image"][0][0]) == 3
