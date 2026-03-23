# 实验报告

## 协议信息

- 协议名称：alpha_sigma_size_full
- 协议版本：1.0
- 协议哈希：22c71498dbf9f40827a58285ddfd3848f95b6864d45e63f485a478bb5507b4b9
- 结果目录：/home/laole/ai/fibered_csp/image_gen/experiments/results/full_run_v1
- 原始数据：raw_runs.jsonl
- 分析数据：analysis.json

## 研究问题

1. Across the alpha-sigma grid, where are the stable, mixed, and collapsed regions for each case?
2. For low-alpha slices, what sigma threshold is required for any survival and for full survival?
3. How do these thresholds shift under relaxed parameters and larger image sizes?

## 结果总览

- 所有 case 的低 alpha 全稳定阈值是否单调：True
- 所有 case 的低 alpha 任意幸存阈值是否单调：True

各 case 的稳定格点占比：
- standard_8x8: 0.846
- relaxed_8x8: 0.899
- relaxed_12x12: 0.811
- relaxed_16x16: 0.719

各 case 的低 alpha 全稳定阈值均值：
- standard_8x8: 1.000
- relaxed_8x8: 0.825
- relaxed_12x12: 1.300
- relaxed_16x16: 1.533

## standard_8x8

### 聚合统计

- 稳定格点占比：0.846
- 混合格点占比：0.008
- 坍缩格点占比：0.146
- 低 alpha 全稳定阈值均值：1.000
- 低 alpha 任意幸存阈值均值：0.950
- 低 alpha 全稳定阈值是否单调：True
- 低 alpha 任意幸存阈值是否单调：True

### 低 alpha 截面

- alpha=0.10: 任意幸存阈值 sigma=0.700，全稳定阈值 sigma=0.700
- alpha=0.08: 任意幸存阈值 sigma=0.800，全稳定阈值 sigma=0.900
- alpha=0.06: 任意幸存阈值 sigma=1.000，全稳定阈值 sigma=1.100
- alpha=0.04: 任意幸存阈值 sigma=1.300，全稳定阈值 sigma=1.300

### 文本相图

```text
α\σ   0.2  0.3  0.4  0.5  0.6  0.7  0.8  0.9  1.0  1.1  1.2  1.3  1.4  1.5  1.6  1.7  1.8  1.9  2.0
0.30 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.29 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.28 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.27 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.26 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.25 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.24 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.23 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.22 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.21 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.20 X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.19 X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.18 X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.17 X    M    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.16 X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.15 X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.14 X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.13 X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.12 X    X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.11 X    X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.10 X    X    X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.09 X    X    X    X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S
0.08 X    X    X    X    X    X    M    S    S    S    S    S    S    S    S    S    S    S    S
0.07 X    X    X    X    X    X    X    M    S    S    S    S    S    S    S    S    S    S    S
0.06 X    X    X    X    X    X    X    X    M    S    S    S    S    S    S    S    S    S    S
0.05 X    X    X    X    X    X    X    X    X    X    S    S    S    S    S    S    S    S    S
0.04 X    X    X    X    X    X    X    X    X    X    X    S    S    S    S    S    S    S    S
```

## relaxed_8x8

### 聚合统计

- 稳定格点占比：0.899
- 混合格点占比：0.010
- 坍缩格点占比：0.092
- 低 alpha 全稳定阈值均值：0.825
- 低 alpha 任意幸存阈值均值：0.775
- 低 alpha 全稳定阈值是否单调：True
- 低 alpha 任意幸存阈值是否单调：True

### 低 alpha 截面

- alpha=0.10: 任意幸存阈值 sigma=0.500，全稳定阈值 sigma=0.500
- alpha=0.08: 任意幸存阈值 sigma=0.600，全稳定阈值 sigma=0.700
- alpha=0.06: 任意幸存阈值 sigma=0.900，全稳定阈值 sigma=0.900
- alpha=0.04: 任意幸存阈值 sigma=1.100，全稳定阈值 sigma=1.200

### 文本相图

```text
α\σ   0.2  0.3  0.4  0.5  0.6  0.7  0.8  0.9  1.0  1.1  1.2  1.3  1.4  1.5  1.6  1.7  1.8  1.9  2.0
0.30 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.29 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.28 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.27 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.26 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.25 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.24 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.23 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.22 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.21 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.20 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.19 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.18 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.17 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.16 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.15 X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.14 X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.13 X    M    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.12 X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.11 X    X    M    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.10 X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.09 X    X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.08 X    X    X    X    M    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.07 X    X    X    X    X    M    S    S    S    S    S    S    S    S    S    S    S    S    S
0.06 X    X    X    X    X    X    X    S    S    S    S    S    S    S    S    S    S    S    S
0.05 X    X    X    X    X    X    X    X    S    S    S    S    S    S    S    S    S    S    S
0.04 X    X    X    X    X    X    X    X    X    M    S    S    S    S    S    S    S    S    S
```

## relaxed_12x12

### 聚合统计

- 稳定格点占比：0.811
- 混合格点占比：0.018
- 坍缩格点占比：0.172
- 低 alpha 全稳定阈值均值：1.300
- 低 alpha 任意幸存阈值均值：1.200
- 低 alpha 全稳定阈值是否单调：True
- 低 alpha 任意幸存阈值是否单调：True

### 低 alpha 截面

- alpha=0.10: 任意幸存阈值 sigma=0.800，全稳定阈值 sigma=0.800
- alpha=0.08: 任意幸存阈值 sigma=1.000，全稳定阈值 sigma=1.100
- alpha=0.06: 任意幸存阈值 sigma=1.300，全稳定阈值 sigma=1.400
- alpha=0.04: 任意幸存阈值 sigma=1.700，全稳定阈值 sigma=1.900

### 文本相图

```text
α\σ   0.2  0.3  0.4  0.5  0.6  0.7  0.8  0.9  1.0  1.1  1.2  1.3  1.4  1.5  1.6  1.7  1.8  1.9  2.0
0.30 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.29 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.28 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.27 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.26 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.25 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.24 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.23 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.22 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.21 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.20 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.19 M    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.18 X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.17 X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.16 X    M    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.15 X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.14 X    X    M    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.13 X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.12 X    X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.11 X    X    X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.10 X    X    X    X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S
0.09 X    X    X    X    X    X    X    S    S    S    S    S    S    S    S    S    S    S    S
0.08 X    X    X    X    X    X    X    X    M    S    S    S    S    S    S    S    S    S    S
0.07 X    X    X    X    X    X    X    X    X    M    S    S    S    S    S    S    S    S    S
0.06 X    X    X    X    X    X    X    X    X    X    X    M    S    S    S    S    S    S    S
0.05 X    X    X    X    X    X    X    X    X    X    X    X    X    M    S    S    S    S    S
0.04 X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    M    M    S    S
```

## relaxed_16x16

### 聚合统计

- 稳定格点占比：0.719
- 混合格点占比：0.023
- 坍缩格点占比：0.257
- 低 alpha 全稳定阈值均值：1.533
- 低 alpha 任意幸存阈值均值：1.400
- 低 alpha 全稳定阈值是否单调：True
- 低 alpha 任意幸存阈值是否单调：True

### 低 alpha 截面

- alpha=0.10: 任意幸存阈值 sigma=1.000，全稳定阈值 sigma=1.100
- alpha=0.08: 任意幸存阈值 sigma=1.400，全稳定阈值 sigma=1.500
- alpha=0.06: 任意幸存阈值 sigma=1.800，全稳定阈值 sigma=2.000
- alpha=0.04: 任意幸存阈值 sigma=N/A，全稳定阈值 sigma=N/A

### 文本相图

```text
α\σ   0.2  0.3  0.4  0.5  0.6  0.7  0.8  0.9  1.0  1.1  1.2  1.3  1.4  1.5  1.6  1.7  1.8  1.9  2.0
0.30 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.29 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.28 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.27 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.26 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.25 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.24 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.23 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.22 S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.21 M    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.20 X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.19 X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.18 X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.17 X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.16 X    X    X    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.15 X    X    X    M    S    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.14 X    X    X    X    M    S    S    S    S    S    S    S    S    S    S    S    S    S    S
0.13 X    X    X    X    X    M    S    S    S    S    S    S    S    S    S    S    S    S    S
0.12 X    X    X    X    X    X    M    S    S    S    S    S    S    S    S    S    S    S    S
0.11 X    X    X    X    X    X    X    M    S    S    S    S    S    S    S    S    S    S    S
0.10 X    X    X    X    X    X    X    X    M    S    S    S    S    S    S    S    S    S    S
0.09 X    X    X    X    X    X    X    X    X    X    M    S    S    S    S    S    S    S    S
0.08 X    X    X    X    X    X    X    X    X    X    X    X    M    S    S    S    S    S    S
0.07 X    X    X    X    X    X    X    X    X    X    X    X    X    X    M    S    S    S    S
0.06 X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    M    M    S
0.05 X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X
0.04 X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X    X
```
