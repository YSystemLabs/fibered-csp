# alpha-sigma-size V1/V2 研究报告

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

### 2.3 共同固定条件

两次协议共同固定：

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

这些表述都直接对应报告中的阈值和占比数据。

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

根据 [comparison.md](../results/full_run_v2/comparison_to_v1/comparison.md)：

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

根据 [comparison_summary.md](../results/full_run_v2/comparison_to_v1/comparison_summary.md)，共有 case 的复现性如下：

- `relaxed_12x12`: `focus_summary_equal=True`, `stable_fraction_equal=True`, `ascii_phase_map_equal=True`
- `relaxed_16x16`: `focus_summary_equal=True`, `stable_fraction_equal=True`, `ascii_phase_map_equal=True`
- `relaxed_8x8`: `focus_summary_equal=True`, `stable_fraction_equal=True`, `ascii_phase_map_equal=True`
- `standard_8x8`: `focus_summary_equal=True`, `stable_fraction_equal=True`, `ascii_phase_map_equal=True`

### 5.1 这组对比实际说明了什么

它说明：

1. V2 作为“在 V1 上新增一个 24x24 case”的扩展，没有改变已有 4 个 case 的结果。
2. 在当前严格流水线上，V1 的已有结果在 V2 中被完整复现。
3. 因此，对 `24x24` 的解读可以被视为在已复现 V1 的前提下所增加的新证据，而不是由协议变动引入的漂移。

### 5.2 V1/V2 对比后最稳的结论

只根据对比文件，可得到以下最稳结论：

- V1 中的 4 个 case 结果在 V2 中完全复现。
- V2 唯一新增的是 `relaxed_24x24`。
- `relaxed_24x24` 在稳定格点占比和低 alpha 全稳定阈值均值上，都继续沿着 `8x8 -> 12x12 -> 16x16` 已有趋势向更“困难”的方向移动。

---

## 6. 综合结果解读

在不越过结果本身的前提下，这两次实验共同支持以下表述：

### 6.1 关于 alpha 与 sigma 的关系

在本协议的 focus alpha 截面上，全部 case 都满足：

- alpha 越低，任意幸存所需 sigma 越高；
- alpha 越低，全稳定所需 sigma 越高。

这对应于 [V1 summary](../results/full_run_v1/summary.md) 与 [V2 summary](../results/full_run_v2/summary.md) 中两个全局布尔值均为 `True`。

### 6.2 关于 standard 与 relaxed 的差别

在 8x8 上，relaxed 参数比 standard 参数具有更低的低 alpha 稳定门槛：

- 全稳定阈值均值：`1.000 -> 0.825`
- 稳定格点占比：`0.846 -> 0.899`

因此，在本协议下，relaxed 参数对应更大的稳定区。

### 6.3 关于尺寸效应

在 relaxed 参数下，尺寸增大对应：

- 稳定格点占比下降：`0.899 -> 0.811 -> 0.719 -> 0.622`
- 全稳定阈值均值上升：`0.825 -> 1.300 -> 1.533 -> 1.700`

因此，在本协议下，尺寸增大与低 alpha 区稳定性下降是同向出现的。

### 6.4 关于 24x24 的新增信息

V2 增加的 `relaxed_24x24` 给出的新增结果是：

- `alpha=0.10` 仍可在扫描范围内达到幸存/全稳定；
- `alpha=0.08/0.06/0.04` 在 `sigma<=2.0` 内未观察到任意幸存；
- 这使得 24x24 在本协议中成为目前最困难的已测尺寸。

---

## 7. 本报告不声称什么

为了保持结果驱动，本报告明确不声称以下内容：

1. 不声称 `sigma` 是模型中的“全局最重要变量”。
   - 这里只系统扫描了 `alpha` 与 `sigma`，没有对 `K`、`target_mode`、`symmetry` 做同等级比较。

2. 不声称 `24x24` 下 `alpha<=0.08` “不可能存活”。
   - 这里只能说：在本次扫描范围 `sigma<=2.0` 内未观察到幸存。

3. 不声称结果自动推广到 RGB、其他 target 或其他 symmetry。
   - 当前协议固定的是 `grayscale + random_smooth + symmetry=none`。

4. 不声称这组实验已经构成理论证明。
   - 它们只提供这组协议下的计算结果与边界数据。

---

## 8. 结论

在当前严格流水线下，V1 和 V2 共同给出的结果可以压缩成以下几句：

1. V1 的 4 个 case 在 V2 中被完全复现。
2. 在本协议中，focus alpha 截面的任意幸存阈值和全稳定阈值都随 alpha 降低而单调升高。
3. 在 8x8 上，relaxed 参数相对于 standard 参数扩大了稳定区并降低了低 alpha 的稳定门槛。
4. 在 relaxed 参数下，从 8x8 到 24x24，稳定格点占比持续下降，低 alpha 全稳定阈值均值持续上升。
5. 在 `relaxed_24x24` 上，`alpha=0.08/0.06/0.04` 在本次 `sigma<=2.0` 扫描范围内未观察到任何幸存。

这些结论全部可回溯到上述结果文件中的具体数值。
