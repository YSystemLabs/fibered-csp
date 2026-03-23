# 实验协议与结果驱动流水线

本目录按“原始数据 → 分析统计 → 报告渲染”的单向链条组织。

## 原则

1. 先固定协议，再运行实验。
2. `run_protocol.py` 只产出原始逐次运行记录，不写结论。
3. `analyze_protocol_run.py` 只从原始记录计算统计量，不写自然语言结论。
4. `render_protocol_report.py` 只读取 `analysis.json`，把已有统计量格式化成 Markdown。
5. 任何报告结论都必须能回溯到 `raw_runs.jsonl` 中的原始记录。

## 目录结构

- [README.md](README.md)：本说明。
- [core.py](core.py)：共享函数与协议校验。
- [run_protocol.py](run_protocol.py)：运行协议并写出 `raw_runs.jsonl`。
- [analyze_protocol_run.py](analyze_protocol_run.py)：分析原始结果并写出 `analysis.json`。
- [render_protocol_report.py](render_protocol_report.py)：从 `analysis.json` 生成报告。
- [run_protocol_pipeline.py](run_protocol_pipeline.py)：串联执行三步。
- [protocols/alpha_sigma_size_smoke_v1.json](protocols/alpha_sigma_size_smoke_v1.json)：小规模冒烟协议。
- [protocols/alpha_sigma_size_full_v1.json](protocols/alpha_sigma_size_full_v1.json)：完整协议。
- [results/](results/)：每次运行的独立结果目录。

## 推荐流程

1. 先跑冒烟协议验证流水线。
2. 再跑完整协议。
3. 只阅读对应结果目录里的 `summary.md` / `report.md`。

## 结果目录约定

每次运行写入独立目录，至少包含：

- `manifest.json`
- `raw_runs.jsonl`
- `analysis.json`
- `report.md`
- `summary.md`

其中：

- `manifest.json` 记录协议路径、协议哈希、网格、种子、输出路径。
- `raw_runs.jsonl` 是唯一原始实验记录源。
- `analysis.json` 只包含从原始记录导出的统计量。
- `report.md` 和 `summary.md` 必须仅依赖 `analysis.json`。
