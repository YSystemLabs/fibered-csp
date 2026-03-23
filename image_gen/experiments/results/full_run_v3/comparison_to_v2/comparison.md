# 24x24 sigma 扩展 V2/V3 对比报告

## 基本信息

- V2 结果目录：/home/laole/ai/fibered_csp/image_gen/experiments/results/full_run_v2
- V3 结果目录：/home/laole/ai/fibered_csp/image_gen/experiments/results/full_run_v3
- 重叠窗口：sigma <= 2.0
- 重叠窗口内 cell 数：513
- 重叠窗口结果是否完全一致：True

## 低 alpha 对比

### alpha=0.10
- V2 任意幸存阈值：1.600
- V2 全稳定阈值：1.700
- V3 任意幸存阈值：1.600
- V3 全稳定阈值：1.700

### alpha=0.08
- V2 任意幸存阈值：N/A
- V2 全稳定阈值：N/A
- V3 任意幸存阈值：2.100
- V3 全稳定阈值：2.200

### alpha=0.06
- V2 任意幸存阈值：N/A
- V2 全稳定阈值：N/A
- V3 任意幸存阈值：2.800
- V3 全稳定阈值：2.900

### alpha=0.04
- V2 任意幸存阈值：N/A
- V2 全稳定阈值：N/A
- V3 任意幸存阈值：3.700
- V3 全稳定阈值：3.900

## 扩展窗口 (sigma > 2.0) 摘要

- stable_cells=497
- mixed_cells=6
- collapsed_cells=37
- total_cells=540
