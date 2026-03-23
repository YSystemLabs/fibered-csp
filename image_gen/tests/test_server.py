"""server.py API 端点测试。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import json


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from server import app
    return TestClient(app)


class TestDefaults:

    def test_get_defaults(self, client):
        resp = client.get("/api/defaults")
        assert resp.status_code == 200
        data = resp.json()
        assert "alpha" in data
        assert data["alpha"]["value"] == 0.5


class TestGenerate:

    def test_generate_minimal(self, client):
        """最小参数调用 /api/generate。"""
        resp = client.post("/api/generate", json={
            "width": 4, "height": 4, "levels": 4,
            "max_iter": 500, "seed": 42,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "image" in data
        assert len(data["image"]) == 4  # H rows
        assert len(data["image"][0]) == 4  # W cols
        assert "scores" in data
        assert "metadata" in data
        assert "closure_map" in data
        assert data["metadata"]["total_pixels"] == 16

    def test_generate_with_symmetry(self, client):
        """带对称的生成。"""
        resp = client.post("/api/generate", json={
            "width": 6, "height": 6, "levels": 4,
            "max_iter": 500, "seed": 42,
            "symmetry": ["lr"],
        })
        assert resp.status_code == 200
        data = resp.json()
        img = data["image"]
        # 验证左右对称
        for row in img:
            assert row == row[::-1]


class TestScore:

    def test_score_endpoint(self, client):
        """/api/score 仅评分。"""
        img = [[3, 3, 3, 3]] * 4
        targets = [[1, 2, 3, 4]] * 4
        resp = client.post("/api/score", json={
            "image": img,
            "targets": targets,
            "params": {"levels": 8},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "scores" in data
        assert "dir_region" in data["scores"]


class TestValidation:

    def test_generate_invalid_c4_non_square(self, client):
        resp = client.post("/api/generate", json={
            "width": 4, "height": 6, "levels": 4,
            "symmetry": ["c4"],
        })
        assert resp.status_code == 400
        assert "width == height" in resp.json()["error"]


class TestSweep:

    def test_sweep_1d_json_fallback(self, client):
        """1D 扫描 /api/sweep 的 JSON 回退模式。"""
        resp = client.post("/api/sweep", json={
            "base_params": {
                "width": 4, "height": 4, "levels": 4,
                "max_iter": 200, "seed": 42,
            },
            "sweep": {
                "axis_x": {"param": "alpha", "min": 0.3, "max": 1.0, "steps": 2},
            },
            "order_params": ["phi_em"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "phi_em" in data["results"]
        assert len(data["results"]["phi_em"][0]) == 2

    def test_sweep_sse_stream(self, client):
        with client.stream("POST", "/api/sweep", json={
            "stream": True,
            "base_params": {
                "width": 4, "height": 4, "levels": 4,
                "max_iter": 100, "seed": 42,
            },
            "sweep": {
                "axis_x": {"param": "alpha", "min": 0.5, "max": 1.0, "steps": 2},
            },
            "order_params": ["phi_em"],
        }) as resp:
            assert resp.status_code == 200
            text = "".join(resp.iter_text())
        assert "event: progress" in text
        assert "event: done" in text
