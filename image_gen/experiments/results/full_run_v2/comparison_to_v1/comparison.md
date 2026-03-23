# V1 / V2 协议对比报告

## 协议信息

- V1 结果目录：/home/laole/ai/fibered_csp/image_gen/experiments/results/full_run_v1
- V2 结果目录：/home/laole/ai/fibered_csp/image_gen/experiments/results/full_run_v2
- V1 协议哈希：22c71498dbf9f40827a58285ddfd3848f95b6864d45e63f485a478bb5507b4b9
- V2 协议哈希：615cfa7cb6e7f3954e37f9d88e3d3166e05cc2faeb43008bf894acbb611930c3

## 共有 case 一致性

### relaxed_12x12
- stable_fraction: V1=0.811, V2=0.811, delta=0.000
- full_threshold_mean: V1=1.300, V2=1.300, delta=0
- focus_summary 是否完全一致：True
- stable_fraction 是否完全一致：True
- ascii_phase_map 是否完全一致：True

### relaxed_16x16
- stable_fraction: V1=0.719, V2=0.719, delta=0.000
- full_threshold_mean: V1=1.533, V2=1.533, delta=0
- focus_summary 是否完全一致：True
- stable_fraction 是否完全一致：True
- ascii_phase_map 是否完全一致：True

### relaxed_8x8
- stable_fraction: V1=0.899, V2=0.899, delta=0.000
- full_threshold_mean: V1=0.825, V2=0.825, delta=0
- focus_summary 是否完全一致：True
- stable_fraction 是否完全一致：True
- ascii_phase_map 是否完全一致：True

### standard_8x8
- stable_fraction: V1=0.846, V2=0.846, delta=0.000
- full_threshold_mean: V1=1.000, V2=1.000, delta=0
- focus_summary 是否完全一致：True
- stable_fraction 是否完全一致：True
- ascii_phase_map 是否完全一致：True

## V2 新增 case

- 新增：relaxed_24x24
- 删除：无

## V2 尺度趋势

### relaxed_12x12
- stable_fraction=0.811
- focus_full_threshold_mean=1.300
- alpha=0.10: any_survival_sigma=0.800, full_survival_sigma=0.800
- alpha=0.08: any_survival_sigma=1.000, full_survival_sigma=1.100
- alpha=0.06: any_survival_sigma=1.300, full_survival_sigma=1.400
- alpha=0.04: any_survival_sigma=1.700, full_survival_sigma=1.900

### relaxed_16x16
- stable_fraction=0.719
- focus_full_threshold_mean=1.533
- alpha=0.10: any_survival_sigma=1.000, full_survival_sigma=1.100
- alpha=0.08: any_survival_sigma=1.400, full_survival_sigma=1.500
- alpha=0.06: any_survival_sigma=1.800, full_survival_sigma=2.000
- alpha=0.04: any_survival_sigma=N/A, full_survival_sigma=N/A

### relaxed_24x24
- stable_fraction=0.622
- focus_full_threshold_mean=1.700
- alpha=0.10: any_survival_sigma=1.600, full_survival_sigma=1.700
- alpha=0.08: any_survival_sigma=N/A, full_survival_sigma=N/A
- alpha=0.06: any_survival_sigma=N/A, full_survival_sigma=N/A
- alpha=0.04: any_survival_sigma=N/A, full_survival_sigma=N/A

### relaxed_8x8
- stable_fraction=0.899
- focus_full_threshold_mean=0.825
- alpha=0.10: any_survival_sigma=0.500, full_survival_sigma=0.500
- alpha=0.08: any_survival_sigma=0.600, full_survival_sigma=0.700
- alpha=0.06: any_survival_sigma=0.900, full_survival_sigma=0.900
- alpha=0.04: any_survival_sigma=1.100, full_survival_sigma=1.200
