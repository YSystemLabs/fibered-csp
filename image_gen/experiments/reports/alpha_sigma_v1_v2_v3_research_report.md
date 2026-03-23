# alpha-sigma-size V1/V2/V3 研究报告

## 1. 报告范围与证据来源

本报告只基于以下结果文件：

- [V1 协议](../protocols/alpha_sigma_size_full_v1.json)
- [V1 manifest](../results/full_run_v1/manifest.json)
- [V1 analysis](../results/full_run_v1/analysis.json)
- [V1 report](../results/full_run_v1/report.md)
- [V1 summary](../results/full_run_v1/summary.md)
- [V2 协议](../protocols/alpha_sigma_size_full_v2.json)
- [V2 manifest](../results/full_run_v2/manifest.json)
- [V2 analysis](../results/full_run_v2/analysis.json)
- [V2 report](../results/full_run_v2/report.md)
- [V2 summary](../results/full_run_v2/summary.md)
- [V1/V2 comparison](../results/full_run_v2/comparison_to_v1/comparison.md)
- [V1/V2 comparison summary](../results/full_run_v2/comparison_to_v1/comparison_summary.md)
- [V3 协议](../protocols/alpha_sigma_size_full_v3.json)
- [V3 manifest](../results/full_run_v3/manifest.json)
- [V3 analysis](../results/full_run_v3/analysis.json)
- [V3 report](../results/full_run_v3/report.md)
- [V3 summary](../results/full_run_v3/summary.md)
- [V2/V3 24x24 comparison](../results/full_run_v3/comparison_to_v2/comparison.md)
- [V2/V3 24x24 comparison summary](../results/full_run_v3/comparison_to_v2/comparison_summary.md)

本报告不引入协议外实验，不把未扫描到的区域写成结论，也不把趋势写成证明。

---

## 2. 实验协议概述

### 2.1 V1 协议

- 协议文件： [alpha_sigma_size_full_v1.json](../protocols/alpha_sigma_size_full_v1.json)
- 协议版本：`1.0`
- 协议哈希：`22c71498dbf9f40827a58285ddfd3848f95b6864d45e63f485a478bb5507b4b9`
- 结果目录： [full_run_v1](../results/full_run_v1)
- 网格：`alpha=0.04~0.30, step=0.01`；`sigma=0.2~2.0, step=0.1`
- 种子：`11, 23, 37`
- case：
  - `standard_8x8`
  - `relaxed_8x8`
  - `relaxed_12x12`
  - `relaxed_16x16`

### 2.2 V2 协议

- 协议文件： [alpha_sigma_size_full_v2.json](../protocols/alpha_sigma_size_full_v2.json)
- 协议版本：`2.0`
- 协议哈希：`615cfa7cb6e7f3954e37f9d88e3d3166e05cc2faeb43008bf894acbb611930c3`
- 结果目录： [full_run_v2](../results/full_run_v2)
- V2 相比 V1 的唯一结构性变化：新增 `relaxed_24x24`

### 2.3 V3 协议

- 协议文件： [alpha_sigma_size_full_v3.json](../protocols/alpha_sigma_size_full_v3.json)
- 协议版本：`3.0`
- 协议哈希：`fa389b76ac7768aab97fc22d9922e42f085f526b1bc5ac2ff6f0f7d3621ca77e`
- 结果目录： [full_run_v3](../results/full_run_v3)
- V3 的目标不是新增尺寸，而是只针对 `relaxed_24x24` 把 `sigma` 上限从 `2.0` 扩展到 `4.0`
- V3 case：
  - `relaxed_24x24`

### 2.4 共同固定条件

三次协议共同固定：

- `target_mode = random_smooth`
- `color_mode = grayscale`
- `symmetry = none`
- focus alpha：`0.10, 0.08, 0.06, 0.04`

因此，本报告中的结论只对应这一组固定条件下的 `alpha-sigma-size` 关系。

---

## 3. V1 的直接结果

根据 [V1 summary](../results/full_run_v1/summary.md)，V1 的全局摘要为：

- 低 alpha 全稳定阈值在全部 case 上是否单调：`True`
- 低 alpha 任意幸存阈值在全部 case 上是否单调：`True`

各 case 稳定格点占比：

- `standard_8x8`: `0.846`
- `relaxed_8x8`: `0.899`
- `relaxed_12x12`: `0.811`
- `relaxed_16x16`: `0.719`

各 case 低 alpha 全稳定阈值均值：

- `standard_8x8`: `1.000`
- `relaxed_8x8`: `0.825`
- `relaxed_12x12`: `1.300`
- `relaxed_16x16`: `1.533`

### 3.1 V1 中低 alpha 截面的阈值

根据 [V1 report](../results/full_run_v1/report.md)：

#### `standard_8x8`
- `alpha=0.10`: 任意幸存 `sigma=0.700`，全稳定 `sigma=0.700`
- `alpha=0.08`: 任意幸存 `sigma=0.800`，全稳定 `sigma=0.900`
- `alpha=0.06`: 任意幸存 `sigma=1.000`，全稳定 `sigma=1.100`
- `alpha=0.04`: 任意幸存 `sigma=1.300`，全稳定 `sigma=1.300`

#### `relaxed_8x8`
- `alpha=0.10`: 任意幸存 `sigma=0.500`，全稳定 `sigma=0.500`
- `alpha=0.08`: 任意幸存 `sigma=0.600`，全稳定 `sigma=0.700`
- `alpha=0.06`: 任意幸存 `sigma=0.900`，全稳定 `sigma=0.900`
- `alpha=0.04`: 任意幸存 `sigma=1.100`，全稳定 `sigma=1.200`

#### `relaxed_12x12`
- `alpha=0.10`: 任意幸存 `sigma=0.800`，全稳定 `sigma=0.800`
- `alpha=0.08`: 任意幸存 `sigma=1.000`，全稳定 `sigma=1.100`
- `alpha=0.06`: 任意幸存 `sigma=1.300`，全稳定 `sigma=1.400`
- `alpha=0.04`: 任意幸存 `sigma=1.700`，全稳定 `sigma=1.900`

#### `relaxed_16x16`
- `alpha=0.10`: 任意幸存 `sigma=1.000`，全稳定 `sigma=1.100`
- `alpha=0.08`: 任意幸存 `sigma=1.400`，全稳定 `sigma=1.500`
- `alpha=0.06`: 任意幸存 `sigma=1.800`，全稳定 `sigma=2.000`
- `alpha=0.04`: 任意幸存 `N/A`，全稳定 `N/A`

### 3.2 对 V1 的结果解读

严格按结果，可以得到以下表述：

1. 在 V1 的四个 case 上，focus alpha 截面的“任意幸存阈值”和“全稳定阈值”都随 alpha 降低而上升。
2. 在 8x8 上，relaxed 参数相对 standard 参数降低了低 alpha 的稳定门槛。
3. 在 relaxed 参数下，尺寸从 8x8 升到 16x16 时，稳定格点占比下降，全稳定阈值均值上升。
4. 在 `relaxed_16x16` 上，`alpha=0.04` 在本次扫描范围 `sigma<=2.0` 内未观察到任意幸存或全稳定。

---

## 4. V2 的直接结果

根据 [V2 summary](../results/full_run_v2/summary.md)，V2 的全局摘要为：

- 低 alpha 全稳定阈值在全部 case 上是否单调：`True`
- 低 alpha 任意幸存阈值在全部 case 上是否单调：`True`

各 case 稳定格点占比：

- `standard_8x8`: `0.846`
- `relaxed_8x8`: `0.899`
- `relaxed_12x12`: `0.811`
- `relaxed_16x16`: `0.719`
- `relaxed_24x24`: `0.622`

各 case 低 alpha 全稳定阈值均值：

- `standard_8x8`: `1.000`
- `relaxed_8x8`: `0.825`
- `relaxed_12x12`: `1.300`
- `relaxed_16x16`: `1.533`
- `relaxed_24x24`: `1.700`

### 4.1 V2 新增 case：`relaxed_24x24`

根据 [V1/V2 comparison](../results/full_run_v2/comparison_to_v1/comparison.md)：

- `alpha=0.10`: 任意幸存 `sigma=1.600`，全稳定 `sigma=1.700`
- `alpha=0.08`: 任意幸存 `N/A`，全稳定 `N/A`
- `alpha=0.06`: 任意幸存 `N/A`，全稳定 `N/A`
- `alpha=0.04`: 任意幸存 `N/A`，全稳定 `N/A`

### 4.2 对 V2 的结果解读

严格按结果，可以增加以下表述：

1. V2 中新增的 `relaxed_24x24` 继续保持了 V1 中已经出现的尺度方向：更大尺寸对应更小稳定区和更高稳定门槛。
2. 在 `relaxed_24x24` 上，focus alpha 中只有 `alpha=0.10` 在扫描范围内观察到幸存；`alpha=0.08/0.06/0.04` 在 `sigma<=2.0` 内未观察到任意幸存或全稳定。
3. `relaxed_24x24` 的稳定格点占比 `0.622` 低于 `relaxed_16x16` 的 `0.719`。
4. `relaxed_24x24` 的低 alpha 全稳定阈值均值 `1.700` 高于 `relaxed_16x16` 的 `1.533`。

---

## 5. V1 与 V2 的对比结果

根据 [V1/V2 comparison summary](../results/full_run_v2/comparison_to_v1/comparison_summary.md)，共有 case 的复现性如下：

- `relaxed_12x12`: `focus_summary_equal=True`, `stable_fraction_equal=True`, `ascii_phase_map_equal=True`
- `relaxed_16x16`: `focus_summary_equal=True`, `stable_fraction_equal=True`, `ascii_phase_map_equal=True`
- `relaxed_8x8`: `focus_summary_equal=True`, `stable_fraction_equal=True`, `ascii_phase_map_equal=True`
- `standard_8x8`: `focus_summary_equal=True`, `stable_fraction_equal=True`, `ascii_phase_map_equal=True`

### 5.1 这组对比实际说明了什么

它说明：

1. V2 作为“在 V1 上新增一个 24x24 case”的扩展，没有改变已有 4 个 case 的结果。
2. 在当前严格流水线上，V1 的已有结果在 V2 中被完整复现。
3. 因此，对 `24x24` 的解读可以被视为在已复现 V1 的前提下所增加的新证据，而不是由协议变动引入的漂移。

---

## 6. V3 的直接结果

根据 [V3 summary](../results/full_run_v3/summary.md)，V3 的全局摘要为：

- 低 alpha 全稳定阈值在全部 case 上是否单调：`True`
- 低 alpha 任意幸存阈值在全部 case 上是否单调：`True`
- `relaxed_24x24` 稳定格点占比：`0.775`
- `relaxed_24x24` 低 alpha 全稳定阈值均值：`2.675`

### 6.1 V3 中 `relaxed_24x24` 的低 alpha 截面

根据 [V2/V3 24x24 comparison](../results/full_run_v3/comparison_to_v2/comparison.md)：

- `alpha=0.10`: 任意幸存 `sigma=1.600`，全稳定 `sigma=1.700`
- `alpha=0.08`: 任意幸存 `sigma=2.100`，全稳定 `sigma=2.200`
- `alpha=0.06`: 任意幸存 `sigma=2.800`，全稳定 `sigma=2.900`
- `alpha=0.04`: 任意幸存 `sigma=3.700`，全稳定 `sigma=3.900`

### 6.2 对 V3 的结果解读

严格按结果，可以得到以下表述：

1. V3 把 V2 中 `relaxed_24x24` 的 `N/A` 区域部分转化成了可观测阈值。
2. 对 `relaxed_24x24` 来说，`alpha=0.08/0.06/0.04` 并不是在更大 sigma 范围内始终无幸存，而是需要更高的 sigma 才出现任意幸存与全稳定。
3. 在 V3 的扩展范围内，focus alpha 四个截面的任意幸存阈值和全稳定阈值仍然是单调上升的。
4. `alpha=0.04` 在 `relaxed_24x24` 上并非在更大 sigma 范围内完全不可恢复；在当前协议中，第一次观测到任意幸存是在 `sigma=3.700`，第一次观测到全稳定是在 `sigma=3.900`。

---

## 7. V2 与 V3 的 24x24 对比结果

根据 [V2/V3 24x24 comparison summary](../results/full_run_v3/comparison_to_v2/comparison_summary.md)：

- 重叠窗口结果是否完全一致：`True`
- `alpha=0.10`: V2(any/full)=`(1.600/1.700)`，V3(any/full)=`(1.600/1.700)`
- `alpha=0.08`: V2(any/full)=`(N/A/N/A)`，V3(any/full)=`(2.100/2.200)`
- `alpha=0.06`: V2(any/full)=`(N/A/N/A)`，V3(any/full)=`(2.800/2.900)`
- `alpha=0.04`: V2(any/full)=`(N/A/N/A)`，V3(any/full)=`(3.700/3.900)`
- 扩展窗口统计：`stable=497`, `mixed=6`, `collapsed=37`, `total=540`

### 7.1 这组对比实际说明了什么

它说明：

1. 在重叠窗口 `sigma<=2.0` 内，V3 与 V2 的 `relaxed_24x24` 结果完全一致。
2. 因此，V3 在 `sigma>2.0` 上观测到的新幸存结果，可以视为对 V2 扫描上限的外延补充，而不是由于协议不一致导致的结果漂移。
3. V2 中的 `N/A` 至少部分来自扫描截断，而不是在更大 sigma 范围内仍然没有幸存。

### 7.2 关于“扫描截断还是尺度壁垒”的结果驱动回答

基于 V2 与 V3 的对比，当前最严格的回答是：

- 对 `relaxed_24x24` 的 `alpha=0.08/0.06/0.04` 来说，V2 中的“无幸存”不是最终壁垒结论，而是受 `sigma<=2.0` 扫描范围限制的结果。
- V3 表明，当 `sigma` 继续提高到 `2.1~3.9` 区间时，这些低 alpha 截面都可以重新出现任意幸存，甚至出现全稳定。
- 因此，就本次协议而言，V2 的 `N/A` 更适合解释为“扫描截断”，而不是“在更高 sigma 下仍然无幸存”。

同时，本报告不把这句话夸大为“尺度壁垒不存在”。当前结果只说明：

- 在 `24x24` 上，低 alpha 需要显著更高的 sigma；
- 但在本次扩展范围 `sigma<=4.0` 内，这个门槛仍然是可达到的。

---

## 8. 综合结果解读

在不越过结果本身的前提下，V1/V2/V3 共同支持以下表述：

### 8.1 关于 alpha 与 sigma 的关系

在当前协议的 focus alpha 截面上，所有已测 case 都满足：

- alpha 越低，任意幸存所需 sigma 越高；
- alpha 越低，全稳定所需 sigma 越高。

这在 V1、V2、V3 的摘要中都体现为相应布尔值为 `True`。

### 8.2 关于 standard 与 relaxed 的差别

在 8x8 上，relaxed 参数比 standard 参数具有更低的低 alpha 稳定门槛：

- 全稳定阈值均值：`1.000 -> 0.825`
- 稳定格点占比：`0.846 -> 0.899`

因此，在本协议下，relaxed 参数对应更大的稳定区。

### 8.3 关于尺寸效应

在 relaxed 参数下，随着尺寸从 8x8 升到 24x24：

- 稳定格点占比下降：`0.899 -> 0.811 -> 0.719 -> 0.622`
- 全稳定阈值均值上升：`0.825 -> 1.300 -> 1.533 -> 1.700`

因此，在 V2 的扫描窗口内，尺寸增大与低 alpha 区稳定性下降是同向出现的。

### 8.4 关于 24x24 的扩展解释

V3 增加的核心信息是：

- `24x24` 的低 alpha 并不是在更大 sigma 范围内始终无幸存；
- 而是需要比 V2 上限更高的 sigma，才会重新进入幸存或全稳定区。

换句话说，V2 呈现出的 `24x24` 低 alpha “无幸存”状态，在 V3 中被进一步拆分成：

- `alpha=0.08`: `sigma=2.100/2.200` 出现任意幸存/全稳定
- `alpha=0.06`: `sigma=2.800/2.900` 出现任意幸存/全稳定
- `alpha=0.04`: `sigma=3.700/3.900` 出现任意幸存/全稳定

因此，V3 给出的新增信息不是“24x24 很容易稳定”，而是：

> `24x24` 的低 alpha 仍可恢复，但恢复门槛显著高于 V2 已扫描范围。

---

## 9. 本报告不声称什么

为了保持结果驱动，本报告明确不声称以下内容：

1. 不声称 `sigma` 是模型中的“全局最重要变量”。
   - 这里只系统扫描了 `alpha` 与 `sigma`，没有对 `K`、`target_mode`、`symmetry` 做同等级比较。

2. 不声称 `24x24` 下低 alpha 没有尺度壁垒。
   - 当前结果只说明：在 `sigma<=4.0` 的扩展范围内，`alpha=0.08/0.06/0.04` 重新出现了幸存与全稳定。

3. 不声称结果自动推广到 RGB、其他 target 或其他 symmetry。
   - 当前协议固定的是 `grayscale + random_smooth + symmetry=none`。

4. 不声称这组实验已经构成理论证明。
   - 它们只提供这组协议下的计算结果与边界数据。

---

## 10. 结论

在当前严格流水线下，V1、V2、V3 共同给出的结果可以压缩成以下几句：

1. V1 的 4 个 case 在 V2 中被完全复现，V2 的 `relaxed_24x24` 又在 V3 的重叠窗口内被完全复现。
2. 在当前协议中，focus alpha 截面的任意幸存阈值和全稳定阈值都随 alpha 降低而单调升高。
3. 在 8x8 上，relaxed 参数相对于 standard 参数扩大了稳定区并降低了低 alpha 的稳定门槛。
4. 在 V2 的扫描窗口内，随着尺寸从 8x8 增大到 24x24，稳定格点占比持续下降，低 alpha 全稳定阈值均值持续上升。
5. V3 表明，`relaxed_24x24` 在 V2 中的 `alpha=0.08/0.06/0.04` “无幸存”主要反映了扫描截断，而不是在更高 sigma 范围内仍然没有幸存。
6. 在当前协议下，`relaxed_24x24` 的低 alpha 仍可恢复，但需要显著更高的 sigma：`2.1~3.9` 的量级。

这些结论全部可回溯到上述结果文件中的具体数值。
