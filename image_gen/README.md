# Fibered CSP Image Generator

基于纤维化 CSP 框架的图像生成与相图实验子工程。该子工程提供：

- 一个 FastAPI + 静态前端的交互式 Web 应用。
- 一组核心引擎模块，用于评分、搜索、序参量计算和参数扫描。
- 一套实验协议流水线，用于批量运行、统计分析和自动生成报告。

## 功能概览

- 生成灰度或 RGB 小尺寸图像。
- 调节像素层偏好、区域层代价和对称性硬约束。
- 观察 `alpha` 驱动的涌现效应与闭包修正。
- 执行 1D / 2D 参数扫描，输出序参量热图和临界点估计。
- 保存规范化实验结果：原始记录、分析 JSON、Markdown 报告。

## 目录结构

```text
image_gen/
├── README.md
├── requirements.txt                     # 运行依赖
├── server.py                            # FastAPI 服务入口
├── docs/
│   └── image-gen-spec-0v1.md            # 工程规范与理论实现约定
├── engine/
│   ├── constraints.py                   # 对称性与区域/像素层约束
│   ├── fibers.py                        # 层间函子与纤维代数实现
│   ├── order_params.py                  # 序参量计算
│   ├── phase_scan.py                    # 1D / 2D 参数扫描
│   ├── scoring.py                       # 逐层评分与闭包
│   └── search.py                        # 图像搜索与目标图生成
├── experiments/
│   ├── README.md                        # 实验流水线说明
│   ├── run_protocol.py                  # 生成 raw_runs.jsonl
│   ├── analyze_protocol_run.py          # 生成 analysis.json
│   ├── render_protocol_report.py        # 生成 report.md / summary.md
│   ├── run_protocol_pipeline.py         # 串联执行三步
│   ├── protocols/                       # 协议样例
│   └── results/                         # 已保存结果
├── static/
│   ├── index.html                       # 前端页面
│   ├── style.css                        # 页面样式
│   └── app.js                           # 前端逻辑与 API 调用
└── tests/                               # pytest 测试集
```

## 环境要求

- Python 3.10+
- `pip`

安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

如果你在仓库根目录执行，也可以使用：

```bash
python3 -m pip install -r image_gen/requirements.txt
```

## 启动方式

### 方式 1：直接运行

在 `image_gen/` 目录中执行：

```bash
python3 server.py
```

### 方式 2：使用 uvicorn

在仓库根目录执行：

```bash
uvicorn image_gen.server:app --host 0.0.0.0 --port 8000
```

服务启动后访问：

```text
http://127.0.0.1:8000
```

## Web 应用能力

前端通过 `server.py` 暴露的 API 与引擎交互，支持：

- 设置画布宽高、色阶数、随机种子和目标图模式。
- 调整退火参数：`max_iter`、`T_init`、`T_min`、`cooling`。
- 调整理论参数：`alpha`、`K`、`sigma`、`tau`、`beta`、`gamma`、`mu`。
- 选择对称性：`lr`、`ud`、`quad`、`c4`、`trans_h`。
- 查看评分分解、区域热图、闭包修正图。
- 启动 1D / 2D 参数扫描，查看序参量结果和进度流。

## API 概览

### `GET /api/defaults`

返回前端参数面板的默认值、范围和枚举选项。

### `POST /api/generate`

根据传入参数生成图像，并返回：

- `image`：生成结果。
- `targets`：目标图。
- `scores`：像素层 / 区域层 / 对称层评分。
- `region_heatmap`：区域层局部代价热图。
- `closure_map`：闭包修正图。
- `metadata`：耗时、迭代次数、自由像素数等信息。

### `POST /api/score`

仅对给定 `image` 和 `targets` 重新评分，不执行搜索。

### `POST /api/sweep`

执行参数扫描：

- 非流式模式：直接返回完整扫描结果。
- 流式模式：通过 SSE 推送 `progress` 和 `done` 事件。

## 测试

在仓库根目录执行：

```bash
python3 -m pytest image_gen/tests -v
```

或在 `image_gen/` 目录中执行：

```bash
python3 -m pytest tests -v
```

测试覆盖：

- 约束与纤维代数。
- 评分与搜索。
- RGB 模式。
- 参数扫描。
- FastAPI 端点。
- 基本集成流程。

## 实验流水线

`experiments/` 目录按“原始数据 → 分析统计 → 报告渲染”的单向链条组织。

推荐流程：

1. 先跑冒烟协议验证环境与脚本。
2. 再跑完整协议。
3. 只根据 `analysis.json` 渲染和阅读结论。

在 `image_gen/` 目录中执行一个冒烟流程：

```bash
python3 experiments/run_protocol_pipeline.py \
  --protocol experiments/protocols/alpha_sigma_size_smoke_v1.json \
  --output-dir experiments/results/manual_smoke_run
```

单步执行：

```bash
python3 experiments/run_protocol.py \
  --protocol experiments/protocols/alpha_sigma_size_full_v1.json \
  --output-dir experiments/results/manual_full_run

python3 experiments/analyze_protocol_run.py \
  experiments/results/manual_full_run

python3 experiments/render_protocol_report.py \
  experiments/results/manual_full_run
```

结果目录通常包含：

- `manifest.json`
- `raw_runs.jsonl`
- `analysis.json`
- `report.md`
- `summary.md`

更详细的实验约定见 `experiments/README.md`。

## 工程说明

该子工程不是通用图像模型，而是一个为理论验证设计的实验系统：

- 图像分辨率聚焦在小尺寸范围内。
- 重点关注参数行为、相变迹象和对称性闭包效应。
- 评分与扫描实现优先保证理论可解释性，而不是追求大规模性能。

完整规范见 `docs/image-gen-spec-0v1.md`。
