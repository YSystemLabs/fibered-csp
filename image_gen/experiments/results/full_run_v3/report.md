# 实验报告

## 协议信息

- 协议名称：alpha_sigma_size_full
- 协议版本：3.0
- 协议哈希：fa389b76ac7768aab97fc22d9922e42f085f526b1bc5ac2ff6f0f7d3621ca77e
- 结果目录：/home/laole/ai/fibered_csp/image_gen/experiments/results/full_run_v3
- 原始数据：raw_runs.jsonl
- 分析数据：analysis.json

## 研究问题

1. For relaxed_24x24, does extending sigma beyond 2.0 reveal survival for low-alpha slices that were N/A in V2?
2. Over the overlap window sigma<=2.0, are the V3 results identical to the V2 relaxed_24x24 results?
3. Within the extended sigma window, which low-alpha slices first show any survival or full survival, if any?

## 结果总览

- 所有 case 的低 alpha 全稳定阈值是否单调：True
- 所有 case 的低 alpha 任意幸存阈值是否单调：True

各 case 的稳定格点占比：
- relaxed_24x24: 0.775

各 case 的低 alpha 全稳定阈值均值：
- relaxed_24x24: 2.675

## relaxed_24x24

### 聚合统计

- 稳定格点占比：0.775
- 混合格点占比：0.009
- 坍缩格点占比：0.216
- 低 alpha 全稳定阈值均值：2.675
- 低 alpha 任意幸存阈值均值：2.550
- 低 alpha 全稳定阈值是否单调：True
- 低 alpha 任意幸存阈值是否单调：True

### 低 alpha 截面

- alpha=0.10: 任意幸存阈值 sigma=1.600，全稳定阈值 sigma=1.700
- alpha=0.08: 任意幸存阈值 sigma=2.100，全稳定阈值 sigma=2.200
- alpha=0.06: 任意幸存阈值 sigma=2.800，全稳定阈值 sigma=2.900
- alpha=0.04: 任意幸存阈值 sigma=3.700，全稳定阈值 sigma=3.900

### 文本相图

```text
α\σ   0.2  0.3  0.4  0.5  0.6  0.7  0.8  0.9  1.0  1.1  1.2  1.3  1.4  1.5  1.6  1.7  1.8  1.9  2.0  2.1  2.2  2.3  2.4  2.5  2.6  2.7  2.8  2.9  3.0  3.1  3.2  3.3  3.4  3.5  3.6  3.7  3.8  3.9  4.0
0.30 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.29 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.28 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.27 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.26 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.25 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.24 X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.23 X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.22 X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.21 X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.20 X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.19 X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.18 X    X    X    M    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.17 X    X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.16 X    X    X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.15 X    X    X    X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.14 X    X    X    X    X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.13 X    X    X    X    X    X    X    X    M    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.12 X    X    X    X    X    X    X    X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.11 X    X    X    X    X    X    X    X    X    X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.10 X    X    X    X    X    X    X    X    X    X    X    X    X    X    M    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.09 X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    M    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.08 X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    M    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.07 X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    M    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.06 X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    M    S    S    S    S    S    S    S    S    S    S    S    S
0.05 X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    M    S    S    S    S    S    S    S    S
0.04 X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    M    M    S    S
```
