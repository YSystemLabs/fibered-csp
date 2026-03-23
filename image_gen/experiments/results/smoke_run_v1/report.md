# 实验报告

## 协议信息

- 协议名称：alpha_sigma_size_smoke
- 协议版本：1.0
- 协议哈希：ce74e51c708d4b93636e0eef73b206e66ef44d9fed4d750f150a277400d2151b
- 结果目录：/home/laole/ai/fibered_csp/image_gen/experiments/results/smoke_run_v1
- 原始数据：raw_runs.jsonl
- 分析数据：analysis.json

## 研究问题

1. For the chosen cases, how does collapse_rate vary over the alpha-sigma grid?
2. For the focus alpha slices, what sigma threshold is required for any survival and full survival?
3. How do these thresholds differ between standard and relaxed parameter settings at 8x8?

## 结果总览

- 所有 case 的低 alpha 全稳定阈值是否单调：True
- 所有 case 的低 alpha 任意幸存阈值是否单调：True

各 case 的稳定格点占比：
- standard_8x8: 0.300
- relaxed_8x8: 0.500

各 case 的低 alpha 全稳定阈值均值：
- standard_8x8: 1.000
- relaxed_8x8: 0.900

## standard_8x8

### 聚合统计

- 稳定格点占比：0.300
- 混合格点占比：0.100
- 坍缩格点占比：0.600
- 低 alpha 全稳定阈值均值：1.000
- 低 alpha 任意幸存阈值均值：0.867
- 低 alpha 全稳定阈值是否单调：True
- 低 alpha 任意幸存阈值是否单调：True

### 低 alpha 截面

- alpha=0.10: 任意幸存阈值 sigma=0.800，全稳定阈值 sigma=0.800
- alpha=0.08: 任意幸存阈值 sigma=0.800，全稳定阈值 sigma=1.000
- alpha=0.06: 任意幸存阈值 sigma=1.000，全稳定阈值 sigma=1.200
- alpha=0.04: 任意幸存阈值 sigma=N/A，全稳定阈值 sigma=N/A

### 文本相图

```text
α\σ   0.4  0.6  0.8  1.0  1.2
0.10 X    X    S    S    S
0.08 X    X    M    S    S
0.06 X    X    X    M    S
0.04 X    X    X    X    X
```

## relaxed_8x8

### 聚合统计

- 稳定格点占比：0.500
- 混合格点占比：0.050
- 坍缩格点占比：0.450
- 低 alpha 全稳定阈值均值：0.900
- 低 alpha 任意幸存阈值均值：0.850
- 低 alpha 全稳定阈值是否单调：True
- 低 alpha 任意幸存阈值是否单调：True

### 低 alpha 截面

- alpha=0.10: 任意幸存阈值 sigma=0.600，全稳定阈值 sigma=0.600
- alpha=0.08: 任意幸存阈值 sigma=0.600，全稳定阈值 sigma=0.800
- alpha=0.06: 任意幸存阈值 sigma=1.000，全稳定阈值 sigma=1.000
- alpha=0.04: 任意幸存阈值 sigma=1.200，全稳定阈值 sigma=1.200

### 文本相图

```text
α\σ   0.4  0.6  0.8  1.0  1.2
0.10 X    S    S    S    S
0.08 X    M    S    S    S
0.06 X    X    X    S    S
0.04 X    X    X    X    S
```
