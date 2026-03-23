# Fibered CSP Image Generator — 工程规范

> 版本 0.1 · 2026-03-09

---

## 0 文档约定

- **必须 (MUST)**：实现中不可省略的要求。
- **应当 (SHOULD)**：推荐的实现方式，仅在有充分理由时可偏离。
- **可选 (MAY)**：增值功能，不影响核心正确性。
- 所有数学符号与论文 `thoughts/纤维化富集范畴视角下的CSP.md` 保持一致。

> **0.1 颜色通道归一化约定**
>
> 记颜色通道数为 $C$：灰度模式 $C=1$，RGB 模式 $C=3$。凡出现 $\|v-w\|$ 的地方，均取欧氏范数；其统一归一化写为
>
> $$d(v,w)=\frac{\|v-w\|}{\sqrt{C}(L-1)} \in [0,1]$$
>
> 因而灰度模式退化为 $|v-w|/(L-1)$，RGB 模式则为 $\|v-w\|/(\sqrt{3}(L-1))$。后文所有“归一化到 $[0,1]$”的距离均指此约定。

> **0.2 固定分辨率实验约定**
>
> 本文的相图扫描和序参量比较默认在**固定画布尺寸**（例如 $16\times 16$）下进行。特别地，§2.8 的 $\phi_{\text{em}}$ 在 $\alpha<1$ 时不具严格的跨分辨率尺度不变性，因此不应用于不同分辨率之间的直接比较。

---

## 1 项目概述

### 1.1 目标

构建一个可交互的 Web 应用，用于在「纤维化 CSP」框架下生成、可视化和探索图像。用户可实时调节各层约束参数（涌现强度 $\alpha$、对称类型、边缘感知阈值等），观察：

1. 不同 $\alpha$ 下像素集体行为的相变现象（涌现可视化）。
2. 对称性层硬约束的级联坍缩效应。
3. 边缘感知约束对区域分割的影响。
4. **涌现相变与对称性自发破缺**：通过序参量（§2.8）定量检测 $\alpha$ 驱动的结构相变和自发对称性破缺。
5. **相图扫描**：在 1D/2D 参数空间上批量扫描，绘制相图热力图和序参量曲线，定位临界点 $\alpha_c$。

### 1.2 非目标

- 不追求生成"自然图像"级别的质量。
- 不追求大规模（>64×64）的实时性。
- 不实现完整的纤维化 CSP 求解器（仅实现本实例所需的评分 + 搜索子集）。

---

## 2 理论基础（实现所需的最小子集）

### 2.1 层级结构 $\mathcal{L}$

三层线性偏序（链）：

$$\mathcal{L} = \{l_{\text{pixel}} \xrightarrow{f_1} l_{\text{region}} \xrightarrow{f_2} l_{\text{sym}}\}$$

方向：精细 → 粗糙。像素最精细，对称性最粗糙/最基础。

### 2.2 纤维（值域代数）

| 层 | 纤维 $V_l$ | 底集 | $\otimes_l$ | $\bigoplus_l$ | $\top_l$ | $\bot_l$ | 语义 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| $l_{\text{pixel}}$ | $([0,1], \leq)$ | $[0,1]$ | $\times$（乘法） | $\sup$ | $1$ | $0$ | 概率/偏好 |
| $l_{\text{region}}$ | $([0,\infty]^{op}, \geq_{\mathrm{nat}})$ | $[0,\infty]$ | $+$（加法） | $\inf$ | $0$ | $\infty$ | 代价 |
| $l_{\text{sym}}$ | $(\{0,1\}, \leq)$ | $\{0,1\}$ | $\wedge$（逻辑与） | $\vee$（逻辑或） | $1$ | $0$ | 布尔 |

**注意**：区域层序为代价的反自然序（$[0,\infty]^{op}$）——代价越低序越高。在实现中，存储自然序数值，比较时取反。

### 2.3 层间函子

#### 2.3.1 $f_2^* : V_{\text{sym}} \to V_{\text{region}}$（对称性 → 区域）

$$f_2^*(1) = 0, \qquad f_2^*(0) = \infty$$

布尔转代价：满足 → 零代价，不满足 → 无穷代价。**强幺半**。

实现中 $\infty$ 用 `float('inf')` 或一个足够大的常数 `COST_INF = 1e12` 表示。

$f_2^*$ 的左伴随 $(f_2)_!$（由伴随自动确定）：

$$(f_2)_!(c) = \begin{cases} 1 & \text{if } c < \infty \\ 0 & \text{if } c = \infty \end{cases}$$

即：有限代价 → 布尔满足，无穷代价 → 布尔坍缩。$(f_2)_!$ 是**强幺半**的（$(f_2)_!(c_1 + c_2) = 1 \iff c_1, c_2$ 均有限 $\iff (f_2)_!(c_1) \wedge (f_2)_!(c_2)$）。因此 $f_2$ 方向**无涌现**。

#### 2.3.2 $f_1^* : V_{\text{region}} \to V_{\text{pixel}}$（区域 → 像素）

$$f_1^*(c) = e^{-(c/K)^\alpha}, \qquad K > 0, \quad \alpha \in (0, 1]$$

**参数**：

- $K$：归一化常数，控制代价到偏好的映射尺度。默认 $K = 255$。
- $\alpha$：**涌现控制参数**，这是整个系统最核心的旋钮。

**性质**（摘自论文 A.13，实现时不需要重新验证）：

- 保持 $\bot$：$f_1^*(\infty) = 0 = \bot_{\text{pixel}}$。 ✓
- 保持 $\bigwedge$：连续严格递减 → 将 $\sup_{\mathrm{nat}}$ 映为 $\inf_{\mathrm{nat}}$。 ✓
- Oplax 幺半：$f_1^*(c_1 + c_2) \geq f_1^*(c_1) \times f_1^*(c_2)$，当 $\alpha < 1$ 时严格。 ✓
- $\alpha = 1$ 时强幺半（无涌现），$\alpha < 1$ 时严格 oplax（有涌现）。

$f_1^*$ 的左伴随 $(f_1)_!$（由伴随自动确定）：

$$(f_1)_!(p) = K \cdot \big(\ln(1/p)\big)^{1/\alpha}, \qquad p \in (0,1]; \qquad (f_1)_!(0) = \infty$$

**数值稳定性**：当 $p$ 接近 0 时 $\ln(1/p) \to \infty$，需 clamp。实现中取 `p = max(p, 1e-15)` 后计算。

### 2.4 变量与域

- 变量集合 $X = \{(i,j) : 0 \leq i < H, 0 \leq j < W\}$，$H \times W$ 为图像尺寸。
- 域 $D_{(i,j)}$：
  - **灰度模式**：$D = \{0, 1, 2, \ldots, L-1\}$，$L$ 为灰度级数（如 $L=8$ 或 $L=16$）。偏好值 $v/（L-1） \in [0,1]$。
  - **RGB 模式**：$D = \{0, \ldots, L-1\}^3$，每通道 $L$ 级。

### 2.5 约束族

#### 2.5.1 像素层约束（一元）

对每个像素 $p = (i,j)$，目标色 $t_p \in D$（随机生成或由"种子图"提供）：

$$\varphi_{\{p\}}(v) = \exp\!\Big(-\frac{d_p^2}{2\sigma^2}\Big) \in [0,1], \qquad d_p = \frac{\|v - t_p\|}{\sqrt{C}(L - 1)}$$

其中 $d_p \in [0, 1]$ 是**归一化距离**（与区域层 §2.5.2 的归一化方式一致），$C$ 为颜色通道数。$\|v - t_p\|$ 在灰度模式下为 $|v - t_p|$，RGB 模式下为欧氏距离 $\sqrt{\sum_c (v_c - t_{p,c})^2}$。

**参数**：

- $t_p$：目标色。生成方式见 §4.4。
- $\sigma$：偏好强度（$\sigma$ 小 → 偏好强，$\sigma$ 大 → 偏好弱）。默认 $\sigma = 0.3$。

**层级指派**：$\Sigma(\{p\}) = l_{\text{pixel}}$。

#### 2.5.2 区域层约束（二元，边缘感知 Potts）

对每对 4-邻接像素对 $(p_i, p_j)$，作用域 $R = \{p_i, p_j\}$：

$$\varphi_R(v_i, v_j) = \begin{cases}
\gamma \cdot d & \text{if } d \leq \tau \qquad (\text{同区域：差异越大惩罚越大}) \\
\beta \cdot d & \text{if } d > \tau \qquad (\text{跨边缘：惩罚过多边缘})
\end{cases}$$

其中

$$d = \frac{\|v_i - v_j\|}{\sqrt{C}(L-1)} \in [0,1]$$

为归一化差异，$C$ 为颜色通道数，$\varphi_R \in [0, \infty)$ 是代价值。

> **行为说明**：$d = 0$（完全一致）→ 代价 0（最优）；$d = \tau^-$（同区域边界）→ 代价 $\gamma\tau$；$d = \tau^+$（跨边缘）→ 代价 $\beta\tau$。默认参数 $\gamma > \beta$ 使得在阈值处存在一个向下跳跃（从 $\gamma\tau$ 到 $\beta\tau$），这激励像素间差异要么很小（同区域平滑）要么明显超过阈值（形成清晰边缘），抑制模糊的中间状态。

**参数**：
- $\tau \in (0, 1)$：边缘阈值。$\tau$ 大 → 更难形成边缘，倾向大色块。默认 $\tau = 0.3$。
- $\beta > 0$：跨边缘惩罚系数。默认 $\beta = 5.0$。
- $\gamma > 0$：区域内不一致惩罚系数（$\gamma > \beta$ 时鼓励锐利边缘）。默认 $\gamma = 10.0$。
- $\mu \ge 0$：**纹理/反铁磁项强度**。实现中同区域分支实际写为

  $$\varphi_R(v_i,v_j) = (\gamma-\mu)\,d \qquad (d \le \tau)$$

  当 $\mu=0$ 时退化为标准 Potts；当 $\mu > \gamma$ 时，同区域分支系数变为负值，系统会奖励局部差异，倾向出现棋盘/条纹等微结构。该扩展项在当前工程实现中**保留**，用于探索纹理化与局部竞争效应。

**可选扩展：方向敏感边缘**。

$$\varphi_R(v_i, v_j) = w(\theta_{ij}) \cdot \varphi_R^{\text{base}}(v_i, v_j)$$

$\theta_{ij}$ 为像素对方向（水平=0°，垂直=90°），$w(\theta)$ 为方向权重：

$$w(\theta) = 1 + \delta_{\text{dir}} \cdot \cos(2(\theta - \theta_0))$$

$\theta_0$ 为偏好方向，$\delta_{\text{dir}} \in [-1, 1]$ 为方向各向异性强度。默认 $\delta_{\text{dir}} = 0$（各向同性）。

**层级指派**：$\Sigma(R) = l_{\text{region}}$。

#### 2.5.3 对称性层约束（全局，布尔）

对称性约束是定义在整个变量集合 $X$（或其子集）上的全局布尔约束。根据对称类型不同，定义如下：

**左右镜像**（关于垂直中轴 $j = (W-1)/2$）：

$$\varphi_{\text{lr}}(a) = \bigwedge_{i,\, j < W/2} \big[\|a(i,j) - a(i, W\!-\!1\!-\!j)\| \leq \epsilon\big]$$

**上下镜像**（关于水平中轴）：

$$\varphi_{\text{ud}}(a) = \bigwedge_{i < H/2,\, j} \big[\|a(i,j) - a(H\!-\!1\!-\!i, j)\| \leq \epsilon\big]$$

**四重对称**（左右 + 上下同时满足）：

$$\varphi_{\text{quad}}(a) = \varphi_{\text{lr}}(a) \wedge \varphi_{\text{ud}}(a)$$

**$C_4$ 旋转对称**（90° 旋转不变，要求 $H = W$）：

$$\varphi_{C_4}(a) = \bigwedge_{i,j} \big[\|a(i,j) - a(j, W\!-\!1\!-\!i)\| \leq \epsilon\big]$$

**平移对称**（水平周期 $T$）：

$$\varphi_{\text{trans}}(a) = \bigwedge_{i,\, j} \big[\|a(i,j) - a(i, (j+T) \bmod W)\| \leq \epsilon\big]$$

**参数**：
- $\epsilon \geq 0$：对称容差（色值差异在 $\epsilon$ 以内视为"相等"）。灰度模式下以灰度级为单位。默认 $\epsilon = 0$（精确对称）。
- 对称类型：枚举值，可多选组合。

**层级指派**：$\Sigma(X) = l_{\text{sym}}$。

**关于对称约束在搜索中的实现**：硬布尔约束在搜索过程中不通过评分函数优化，而是通过**约束消元**直接实现——将自由变量从 $H \times W$ 缩减到对称基本域中的变量数（见 §5.3）。

### 2.6 评分流水线

给定全局赋值 $a \in A(X) = \prod_{(i,j)} D_{(i,j)}$，按 §3.3 的 (S1)–(S4) 计算：

#### (S1) 逐层直接评分

$$\mathrm{Dir}_{\text{pixel}}(a) = \prod_{p \in X} \varphi_{\{p\}}(a(p))$$

$$\mathrm{Dir}_{\text{region}}(a) = \sum_{R \in \mathcal{N}} \varphi_R(a|_R)$$

其中 $\mathcal{N}$ 为所有 4-邻接像素对的集合。

$$\mathrm{Dir}_{\text{sym}}(a) = \bigwedge_k \varphi_{\text{sym}_k}(a)$$

（多个对称约束同时启用时取逻辑与。）

**实现注意**：$\mathrm{Dir}_{\text{pixel}}$ 为大量 $[0,1]$ 值的连乘，会数值下溢。**必须使用对数域运算**：

$$\ln \mathrm{Dir}_{\text{pixel}}(a) = \sum_p \ln \varphi_{\{p\}}(a(p))$$

所有像素层运算在对数域进行，仅在需要送入 $f_1^*$ 或展示时转回原域。

#### (S2) 涌现贡献

$$\mathrm{Em}_{\text{pixel}}(a) = \top_{\text{pixel}} = 1 \qquad (\text{无更精细层})$$

$$\mathrm{Em}_{\text{region}}(a) = (f_1)_!\big(\mathrm{Dir}_{\text{pixel}}(a)\big)$$

> **实现约束**：此处必须保留“**先聚合，再推前**”的集体形式，即先计算 $\mathrm{Dir}_{\text{pixel}} = \prod_p \varphi_p$，再整体送入 $(f_1)_!$。**不得**将其替换为 $\sum_p (f_1)_!(\varphi_p)$ 一类逐像素可加 surrogate；后者虽实现简单，但会抹掉本文希望观察的非幺半集体效应。

$$\mathrm{Em}_{\text{sym}}(a) = (f_2)_!\big(\mathrm{Dir}_{\text{region}}(a)\big) \wedge (f_2)_!\big((f_1)_!(\mathrm{Dir}_{\text{pixel}}(a))\big)$$

> 简化：由于 $(f_2)_!$ 仅判断代价是否有限，且 $\mathrm{Dir}_{\text{pixel}} > 0 \implies (f_1)_!(\mathrm{Dir}_{\text{pixel}}) < \infty \implies (f_2)_!(\cdots) = 1$，当所有像素偏好值非零时，$\mathrm{Em}_{\text{sym}} = 1$。对称层涌现贡献通常为 $\top$——对称层的主要作用通过 $\mathrm{Dir}_{\text{sym}}$ 和截面化闭包传播体现，而非涌现。

实际上，**涌现效应集中在 $f_1$ 方向**（像素 → 区域），这正是 $\alpha$ 旋钮控制的。

#### (S3) 总评分

$$\mathrm{Score}_{\text{pixel}}(a) = \mathrm{Dir}_{\text{pixel}}(a) \times 1 = \mathrm{Dir}_{\text{pixel}}(a)$$

$$\mathrm{Score}_{\text{region}}(a) = \mathrm{Dir}_{\text{region}}(a) + \mathrm{Em}_{\text{region}}(a)$$

$$\mathrm{Score}_{\text{sym}}(a) = \mathrm{Dir}_{\text{sym}}(a) \wedge \mathrm{Em}_{\text{sym}}(a)$$

#### (S4) 截面化闭包

按逆拓扑序（对称性 → 区域 → 像素）递推：

$$s_{\text{sym}} = \mathrm{Score}_{\text{sym}}(a)$$

$$s_{\text{region}} = \mathrm{Score}_{\text{region}}(a) \wedge_{\text{region}} f_2^*(s_{\text{sym}})$$

> 即 $s_{\text{region}} = \max_{\mathrm{nat}}(\mathrm{Score}_{\text{region}}(a),\ f_2^*(s_{\text{sym}}))$。
> （$\wedge$ 在 $[0,\infty]^{op}$ 中是自然序的 $\max$，即取更糟的代价。）
>
> 当 $s_{\text{sym}} = 0$（$\bot_{\text{sym}}$）时，$f_2^*(0) = \infty$，故 $s_{\text{region}} = \infty = \bot_{\text{region}}$。坍缩传播。
> 当 $s_{\text{sym}} = 1$（$\top_{\text{sym}}$）时，$f_2^*(1) = 0$，故 $s_{\text{region}} = \mathrm{Score}_{\text{region}}(a)$。无修正。

$$s_{\text{pixel}} = \mathrm{Score}_{\text{pixel}}(a) \wedge_{\text{pixel}} f_1^*(s_{\text{region}})$$

> 即 $s_{\text{pixel}} = \min(\mathrm{Score}_{\text{pixel}}(a),\ f_1^*(s_{\text{region}}))$。
> （$\wedge$ 在 $[0,1]$ 中是 $\min$。）
>
> 当 $s_{\text{region}} = \infty$（坍缩）时，$f_1^*(\infty) = 0$，故 $s_{\text{pixel}} = 0 = \bot_{\text{pixel}}$。坍缩继续传播。
> 当 $s_{\text{region}}$ 有限时，$f_1^*(s_{\text{region}}) = e^{-(s_{\text{region}}/K)^\alpha}$，若此值 < $\mathrm{Score}_{\text{pixel}}$，则像素层被修正（截面化闭包的核心效应）。

### 2.7 搜索目标

由于 $\mathcal{L}$ 为全序（链），采用**字典序**优化（论文 §5 退化表第 5 行）：

1. **优先保证对称性层满足**（$s_{\text{sym}} = 1$）。通过约束消元实现（§5.3），不参与搜索。
2. **在满足对称的赋值中，最小化区域层代价** $s_{\text{region}}$。
3. **在区域层代价最优的邻域中，最大化像素层偏好** $s_{\text{pixel}}$。

实际实现中，字典序通过**加权标量化启发式**近似：

$$\mathrm{Obj}(a) = w_{\text{sym}} \cdot \mathbb{1}[s_{\text{sym}} = 0] + w_{\text{region}} \cdot s_{\text{region}} - w_{\text{pixel}} \cdot \ln(s_{\text{pixel}})$$

其中 $w_{\text{sym}} \gg w_{\text{region}} \gg w_{\text{pixel}}$（如 $10^6 : 1 : 0.01$）。**最小化 $\mathrm{Obj}$**。

> 使用 $\ln(s_{\text{pixel}})$ 而非 $s_{\text{pixel}}$ 是因为像素层在对数域运算（§2.6 注意事项）。
>
> **说明**：这只是字典序的工程近似，而非严格等价变换。后端实现应优先优化 **closure-aware** 的目标（即使用 $s_{\text{region}}, s_{\text{pixel}}$，而不是仅使用未闭包的 `Dir` 项），以尽量贴近理论语义。

### 2.8 序参量与相变检测

#### 2.8.1 涌现相变

当 $\alpha$ 从 1.0 连续降到 0 时，系统从"无涌现"过渡到"强涌现"。定义以下**序参量**来定量检测相变：

**序参量 1：归一化涌现强度**

$$\phi_{\text{em}}(\alpha) = \frac{\mathrm{Em}_{\text{region}}(a^*)}{H \times W}$$

其中 $a^*$ 是给定 $\alpha$ 下搜索收敛后的最优赋值。$\phi_{\text{em}}$ 衡量每像素平均涌现贡献的代价。

> **尺度说明**：当 $\alpha=1$ 时，上式对分辨率的依赖较弱；当 $\alpha<1$ 时，由于 $(f_1)_!$ 的非线性，$\phi_{\text{em}}$ 对图像尺寸并非严格尺度不变。因此它适合作为**固定分辨率扫描**中的序参量，而不适合作为不同分辨率之间的直接比较量。

- $\alpha = 1$（幺半）：$\mathrm{Em}_{\text{region}} = (f_1)_!(\prod_p \varphi_p)$，可分解为单像素贡献之和，$\phi_{\text{em}}$ 平滑。
- $\alpha < 1$（oplax）：$(f_1)_!$ 的次可加性使 $\mathrm{Em}_{\text{region}}$ 小于各部分之和——涌现贡献"集体地"更便宜。$\phi_{\text{em}}$ 在某个 $\alpha_c$ 附近出现拐点。

**序参量 2：闭包修正比率**

$$\phi_{\text{cl}}(\alpha) = \frac{|s_{\text{pixel}} - \mathrm{Score}_{\text{pixel}}|}{\max(|\mathrm{Score}_{\text{pixel}}|, \epsilon_0)} \times 100\%$$

截面化闭包的修正幅度。$\alpha = 1$ 时修正可能较小；$\alpha$ 降低到 $\alpha_c$ 时修正会跳跃式增大（区域代价通过 $f_1^*$ 向下挤压像素层评分）。

**序参量 3：空间相关长度**

$$\xi(\alpha) = \text{argmin}_r \Big\{ C(r) < e^{-1} \cdot C(0) \Big\}$$

其中 $C(r) = \langle a(p) \cdot a(p') \rangle_{|p-p'|=r} - \langle a(p) \rangle^2$ 是像素值的空间自相关函数。$\xi$ 衡量"色块"的特征尺寸：

- $\alpha \approx 1$：$\xi \approx 1$（几乎无空间相关，像素独立）。
- $\alpha < \alpha_c$：$\xi$ 突然增大（涌现"粘合"了远距离像素，形成宏观色块）。

**相变临界点 $\alpha_c$ 的实操估计**：$\alpha_c$ 依赖于其他参数（$\sigma, \tau, \gamma, \beta, K$），因此不是一个固定常数。扫描 $\alpha$ 时，取 $d\phi_{\text{em}} / d\alpha$ 或 $d\xi / d\alpha$ 绝对值最大处作为 $\alpha_c$ 的估计。

#### 2.8.2 对称性自发破缺

即使**未启用**显式对称约束，涌现也可能导致生成图像自发出现结构性偏向。检测方法：

**方向序参量**（检测自发各向异性）：

$$\bar C_H = \frac{C_H}{H(W-1)}, \qquad \bar C_V = \frac{C_V}{(H-1)W}$$

$$\phi_{\text{dir}} = \frac{|\bar C_H - \bar C_V|}{\bar C_H + \bar C_V + \epsilon_0}$$

其中 $C_H = \sum$ 所有水平相邻对代价，$C_V = \sum$ 所有垂直相邻对代价。使用平均边代价 $\bar C_H, \bar C_V$ 而不是总和，是为了消除非方形画布上“水平边数与垂直边数不同”带来的偏置。$\phi_{\text{dir}} \approx 0$ 表示各向同性；$\phi_{\text{dir}}$ 显著偏离 0 表示自发的方向对称性破缺（如水平条纹或垂直条纹）。

**镜像序参量**（检测自发镜像对称的程度）：

$$\phi_{\text{mirror}} = 1 - \frac{1}{HW/2} \sum_{i,\, j < W/2} \frac{\|a(i,j) - a(i, W\!-\!1\!-\!j)\|}{L-1}$$

$\phi_{\text{mirror}} = 1$ 时完全镜像对称；$\phi_{\text{mirror}} \approx 0.5$ 时无自发对称；$\phi_{\text{mirror}} > 0.7$（经验阈值）可认为出现了自发对称性。

> **自发对称与显式对称的区别**：显式对称通过约束消元**强制**实现（§4.4.2），$\phi_{\text{mirror}} \equiv 1$。自发对称无强制，但涌现使系统"倾向于"对称解——类似物理中铁磁体在居里温度以下的自发磁化。

---

## 3 系统架构

### 3.1 总体架构

```
┌─────────────────────────────────────────────┐
│                Browser (前端)                │
│  ┌─────────┐  ┌────────┐  ┌──────────────┐  │
│  │ 参数面板 │  │ 画布区 │  │ 评分仪表盘  │  │
│  │ (旋钮)  │  │(Canvas)│  │ (各层评分)   │  │
│  └────┬────┘  └───┬────┘  └──────┬───────┘  │
│       │           │              │           │
│       └───────────┼──────────────┘           │
│                   │ WebSocket / HTTP         │
└───────────────────┼─────────────────────────┘
                    │
┌───────────────────┼─────────────────────────┐
│            Python Backend (后端)              │
│  ┌────────────────┴──────────────────────┐   │
│  │           API Layer (FastAPI)         │   │
│  ├───────────────────────────────────────┤   │
│  │         Engine Layer                  │   │
│  │  ┌─────────┐ ┌──────┐ ┌───────────┐  │   │
│  │  │ Fibers  │ │Score │ │  Search   │  │   │
│  │  │ Module  │ │Pipe  │ │  Engine   │  │   │
│  │  └─────────┘ └──────┘ └───────────┘  │   │
│  ├───────────────────────────────────────┤   │
│  │       Constraint Definitions          │   │
│  └───────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

### 3.2 技术栈

| 组件 | 技术 | 理由 |
|------|------|------|
| 后端框架 | FastAPI | 异步支持好，自动 OpenAPI 文档 |
| 数值计算 | NumPy | 向量化评分计算 |
| 前端 | 原生 HTML + CSS + JS | 依赖少，单文件可部署 |
| 前端 UI | range input + Canvas API | 旋钮用原生 range，图像用 Canvas |
| 通信 | HTTP POST + SSE | 单次生成用 HTTP；相图扫描用 SSE 推送进度和最终结果 |

### 3.3 文件结构

```
image_gen/
├── docs/
│   └── spec.md                 ← 本文件
├── server.py                   ← FastAPI 入口，API 路由
├── engine/
│   ├── __init__.py
│   ├── fibers.py               ← 纤维定义、f*/f_! 函子
│   ├── constraints.py          ← 三层约束定义
│   ├── scoring.py              ← 评分流水线 S1–S4
│   ├── search.py               ← 搜索引擎（模拟退火）
│   ├── order_params.py         ← 序参量计算（§2.8）
│   └── phase_scan.py           ← 相图扫描引擎（§4.6）
├── static/
│   ├── index.html              ← 主页面
│   ├── style.css               ← 样式
│   └── app.js                  ← 前端逻辑
└── requirements.txt
```

---

## 4 模块详细规范

### 4.1 `engine/fibers.py` — 纤维与层间函子

#### 4.1.1 数据结构

```python
@dataclass
class FiberConfig:
    """一根纤维的完整配置。"""
    name: str                  # "pixel" | "region" | "sym"
    bot: float                 # 底元素值
    top: float                 # 顶元素值
    # otimes 和 oplus 在各自层的评分函数中内联实现，不抽象为通用运算
```

#### 4.1.2 函子接口

```python
def f1_star(c: float, alpha: float, K: float = 255.0) -> float:
    """区域层代价 → 像素层偏好。f_1^*(c) = exp(-(c/K)^alpha)"""

def f1_shriek(p: float, alpha: float, K: float = 255.0) -> float:
    """像素层偏好 → 区域层代价。(f_1)_!(p) = K * (ln(1/p))^(1/alpha)"""

def f2_star(b: int) -> float:
    """对称层布尔 → 区域层代价。f_2^*(1)=0, f_2^*(0)=INF"""

def f2_shriek(c: float) -> int:
    """区域层代价 → 对称层布尔。(f_2)_!(c) = 1 if c < INF else 0"""
```

**所有函子必须接受向量化输入**（NumPy 数组），以支持批量评分。

#### 4.1.3 数值约定

| 常数 | 值 | 说明 |
|------|---|------|
| `COST_INF` | `1e12` | 代价域的 $\infty$ 替代值 |
| `PROB_EPS` | `1e-15` | 概率域的最小正值（防止 `log(0)`） |
| `LN_PROB_FLOOR` | `-35.0` | 对数概率域的下界（对应 `PROB_EPS`） |

### 4.2 `engine/constraints.py` — 约束定义

#### 4.2.1 像素层约束

```python
def pixel_preferences(
    image: np.ndarray,          # shape (H, W) 或 (H, W, 3)，当前赋值
    targets: np.ndarray,        # shape 同 image，目标色
    sigma: float                # 偏好强度
) -> np.ndarray:
    """返回 shape (H, W) 的逐像素偏好值 ∈ [0, 1]。"""
```

**向量化实现**（注意输入先归一化到 $[0,1]$）：

```python
channels = image.shape[-1] if image.ndim == 3 else 1
norm = (levels - 1) * np.sqrt(channels)
d_sq = np.sum(((image - targets) / norm) ** 2, axis=-1)  # 归一化距离的平方
return np.exp(-d_sq / (2 * sigma ** 2))
```

#### 4.2.2 区域层约束（边缘感知 Potts）

```python
def region_costs(
    image: np.ndarray,          # shape (H, W) 或 (H, W, 3)
    tau: float,                 # 边缘阈值
    beta: float,                # 跨边缘惩罚
    gamma: float,               # 区域内惩罚
  levels: int,
    dir_strength: float = 0.0,  # 方向各向异性强度 δ_dir
  dir_angle: float = 0.0,     # 偏好方向 θ_0（度）
  mu: float = 0.0,
) -> tuple[float, np.ndarray, float, float]:
  """返回 (区域层总代价标量, (H,W) 代价热力图, C_H, C_V)。"""
```

**实现要求**：
1. 计算所有水平相邻对的差异 `dh = |image[:, 1:] - image[:, :-1]|`（归一化）。
2. 计算所有垂直相邻对的差异 `dv = |image[1:, :] - image[:-1, :]|`（归一化）。
3. 对每对应用 Potts 代价函数。
4. 若 `dir_strength != 0`，乘以方向权重。
5. 返回所有对的代价之和。

**应当**同时返回一个 `(H, W)` 的代价热力图（每像素 = 其邻域对代价的平均值），用于前端可视化。

#### 4.2.3 对称性层约束

```python
class SymmetryType(Enum):
    NONE = "none"
    LEFT_RIGHT = "lr"
    UP_DOWN = "ud"
    QUAD = "quad"               # lr + ud
    ROTATE_C4 = "c4"            # 90° 旋转（要求 H == W）
    TRANSLATE_H = "trans_h"     # 水平平移周期

def symmetry_check(
    image: np.ndarray,          # shape (H, W) 或 (H, W, 3)
    sym_types: list[SymmetryType],  # 启用的对称类型
    epsilon: float,             # 容差
    translate_period: int = 0   # 平移周期（仅 TRANSLATE_H）
) -> bool:
    """返回布尔值：是否满足所有启用的对称约束。"""
```

### 4.3 `engine/scoring.py` — 评分流水线

```python
@dataclass
class LayerScores:
    """一次评分的完整结果。"""
    # 直接评分
    dir_pixel: float            # log 域
    dir_region: float           # 代价域（自然值）
    dir_sym: bool

    # 涌现贡献
    em_region: float            # (f_1)_!(Dir_pixel)

    # 总评分
    score_pixel: float          # log 域
    score_region: float
    score_sym: bool

    # 截面化闭包后评分
    cl_pixel: float             # log 域
    cl_region: float
    cl_sym: bool

    # 诊断
    closure_correction_pixel: float   # cl_pixel - score_pixel（log 域）
    closure_correction_region: float  # cl_region - score_region
    is_collapsed: bool                # 任一层 = bot

    # 附加数据（前端可视化用）
    region_heatmap: np.ndarray | None = None
    pixel_prefs: np.ndarray | None = None
    closure_map: np.ndarray | None = None
    C_H: float = 0.0
    C_V: float = 0.0


def compute_scores(
    image: np.ndarray,
    targets: np.ndarray,
    params: dict,               # 所有参数的字典
) -> LayerScores:
    """执行完整的 S1–S4 评分流水线。"""
```

**实现步骤**（伪代码）：

```
# S1: 直接评分
dir_pixel_log = sum(log(pixel_preferences(image, targets, sigma)))
dir_region = region_costs(image, tau, beta, gamma, ...)
dir_sym = symmetry_check(image, sym_types, epsilon, ...)

# S2: 涌现（直接在对数域计算，避免 exp 下溢）
# f1_shriek(exp(x)) = K * (-x)^(1/alpha)，其中 x = dir_pixel_log < 0
em_region = K * max(-dir_pixel_log, 0.0) ** (1.0 / alpha)  # 对数域直接计算
# em_sym 通常为 top，略

# S3: 总评分
score_pixel_log = dir_pixel_log  # Em_pixel = top, 不变
score_region = dir_region + em_region
score_sym = dir_sym  # Em_sym 通常为 top

# S4: 截面化闭包（逆拓扑序：sym → region → pixel）
cl_sym = score_sym

if cl_sym == False (bot):
    cl_region = COST_INF  # 坍缩
else:
    cl_region = max(score_region, f2_star(cl_sym))  # = score_region（因 f2*(1)=0）

cl_pixel_log = min(score_pixel_log, log(f1_star(cl_region, alpha, K)))

# closure_map（工程近似可视化）
# 将总闭包修正量按逐像素负对数偏好的占比分配到各像素，用于前端热力图展示
```

> **关于 `closure_map` 的说明**：`closure_map` 是当前工程实现中的**可视化辅助量**，不是论文中单独定义的理论不变量。它通过将总闭包修正量按逐像素负对数偏好占比进行分配，展示“哪些区域更受闭包挤压”。这对界面观察有用，但不应被误读为严格的局部理论量。

### 4.4 `engine/search.py` — 搜索引擎

#### 4.4.1 搜索算法：模拟退火

选择模拟退火的理由：(1) 对非凸、非连续目标通用；(2) 实现简单；(3) 天然支持对称约束消元。

```python
def simulated_annealing(
    H: int, W: int,
    targets: np.ndarray,
    params: dict,
    levels: int = 8,            # 灰度级数（域大小）
    max_iter: int = 50000,
    T_init: float = 10.0,
    T_min: float = 0.01,
    cooling: float = 0.9995,
    seed: int | None = None,
    callback: Callable | None = None,  # 每 N 步回调，用于中间结果推送
) -> tuple[np.ndarray, LayerScores]:
    """返回最优图像和对应评分。"""
```

#### 4.4.2 对称约束消元

对称层的硬约束**不参与评分优化**，而是通过缩减自由变量实现：

| 对称类型 | 基本域 | 自由像素数 | 填充规则 |
|---|---|---|---|
| 无 | 全图 | $H \times W$ | — |
| 左右 | 左半 $\{(i,j): j \leq (W-1)/2\}$ | $H \times \lceil W/2 \rceil$ | $a(i,W-1-j) := a(i,j)$ |
| 上下 | 上半 | $\lceil H/2 \rceil \times W$ | $a(H-1-i,j) := a(i,j)$ |
| 四重 | 左上象限 | $\lceil H/2 \rceil \times \lceil W/2 \rceil$ | 先左右填充，再上下填充 |
| $C_4$ 旋转 | 轨道枚举（见下文） | $\approx N^2/4$（$N\!=\!H\!=\!W$） | 依次旋转 90° 填充 |
| 水平平移 | 第一个周期 $\{(i,j): j < T\}$ | $H \times T$ | $a(i,j+kT) := a(i,j)$ |

> **$C_4$ 基本域说明**：$C_4$ 旋转将 $(i,j) \mapsto (j, N\!-\!1\!-\!i)$，每个轨道包含 1 或 4 个像素（$N$ 为奇数时中心像素 $((N\!-\!1)/2, (N\!-\!1)/2)$ 为不动点，轨道大小 1）。闭合公式 $\{(i,j): j \leq i,\, i+j < N-1\}$（偶数 $N$）或加上中心点（奇数 $N$）可作为基本域，但实现中**推荐直接枚举轨道**：对每个 $(i,j)$，计算其在 $\{\mathrm{id}, R_{90}, R_{180}, R_{270}\}$ 下的 4 个坐标，取字典序最小者作为代表元。基本域 = 所有代表元的集合。此方法避免公式边界条件错误，实现为启动时一次性预计算 $O(N^2)$。

搜索仅在**基本域**上操作。每次状态变更后，通过填充规则生成完整图像，再送入评分流水线。

**$\epsilon > 0$ 时的容差对称**：精确消元对应 $\epsilon = 0$。当 $\epsilon > 0$ 时，基本域填充后对镜像像素添加均匀噪声 $\sim U[-\epsilon/2, \epsilon/2]$（离散域中取整），模拟"近似对称"。

#### 4.4.3 邻域操作（提议函数）

每步模拟退火的提议：

1. 随机选一个**基本域内**的像素 $(i,j)$。
2. 将其灰度/色值随机偏移 $\pm 1$ 到 $\pm k$ 级（$k$ 随温度自适应：$k = \max(1, \lfloor T \rfloor)$）。
3. 按填充规则更新对称位置。
4. **增量评分**（关键优化）：仅重新计算受影响的约束项，而非全图重算。
   - 像素层：仅 1 个像素偏好变化（对称填充后最多 4 个）。
   - 区域层：仅该像素及其邻居的 ≤8 对约束变化（对称填充后按倍数增长）。
   - 对称层：消元后自动满足，无需检查。

5. **closure-aware 标量更新**：虽然 $\mathrm{Em}_{\text{region}} = (f_1)_!(\mathrm{Dir}_{\text{pixel}})$ 具有全局性，但它只依赖单个标量 `dir_pixel_log`。因此每次提议后只需：
  - 用增量公式更新 `dir_pixel_log`
  - 重新计算一次 `em_region = K * (-dir_pixel_log)^(1/alpha)`
  - 再用常数个标量步骤更新 `score_region`, `cl_region`, `cl_pixel_log`

  因而即使搜索目标使用最终的 `Score/cl`，每步仍保持 $O(1)$。

增量评分使每步从 $O(H \times W)$ 降为 $O(1)$（常数取决于对称倍数）。

> **边界情形：镜像像素互为邻居**。在 LR 对称且 $W$ 为偶数时，中轴两侧像素 $(i, W/2\!-\!1)$ 和 $(i, W/2)$ 互为镜像且互为 4-邻居。修改基本域像素 $(i, W/2\!-\!1)$ 时，其镜像 $(i, W/2)$ 也被修改，二者之间的约束对**两端同时变化**。增量公式需特殊处理：$\Delta = \varphi_R(v_{\text{new}}, v'_{\text{new}}) - \varphi_R(v_{\text{old}}, v'_{\text{old}})$（不能拆为两次单端变更）。类似情形出现在 UD 对称的中轴行和 QUAD 对称的中心区域。实现中应检测"受影响像素集合中是否存在互为邻居的对"并走双端更新路径。

#### 4.4.4 目标色生成策略

用户可选的 `target_mode`：

| 模式 | 说明 | 实现 |
|------|------|------|
| `random_uniform` | 每像素独立均匀随机 | `np.random.randint(0, L, (H,W))` |
| `random_smooth` | 平滑随机场（低频噪声） | 小尺寸随机 → 双线性插值放大 |
| `gradient_h` | 水平渐变 | `np.linspace(0, L-1, W)` 广播 |
| `gradient_v` | 垂直渐变 | `np.linspace(0, L-1, H)` 广播 |
| `checkerboard` | 棋盘格 | $(i+j) \% 2 \times (L-1)$ |
| `center_blob` | 中心高斯斑 | 二维高斯，中心=255 |

**`random_smooth` 是默认且最推荐的**——它提供了空间相关的偏好，使涌现效应更明显（纯随机偏好在涌现后仍是噪声；平滑偏好在涌现后会强化大尺度结构）。

### 4.5 `server.py` — API 层

#### 4.5.1 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 返回 `static/index.html` |
| GET | `/static/{path}` | 静态文件 |
| POST | `/api/generate` | 主生成接口（单次） |
| POST | `/api/score` | 仅评分（给定图像） |
| POST | `/api/sweep` | 相图扫描（SSE 流式进度 + 最终结果） |
| GET | `/api/defaults` | 返回所有参数的默认值和范围 |

#### 4.5.2 `/api/generate` 请求/响应

**请求体** (`application/json`)：

```json
{
  "width": 16,
  "height": 16,
  "color_mode": "grayscale",
  "levels": 8,
  "seed": 42,
  "target_mode": "random_smooth",
  "max_iter": 30000,

  "alpha": 0.5,
  "K": 255,

  "sigma": 0.3,

  "tau": 0.3,
  "beta": 5.0,
  "gamma": 10.0,
  "mu": 0.0,
  "dir_strength": 0.0,
  "dir_angle": 0,

  "symmetry": ["lr"],
  "epsilon": 0,
  "translate_period": 4
}
```

所有参数均可选，缺失时使用默认值。

**响应体** (`application/json`)：

```json
{
  "image": [[128, 64, ...], ...],
  "targets": [[200, 100, ...], ...],
  "scores": {
    "dir_pixel_log": -45.2,
    "dir_region": 120.5,
    "dir_sym": true,
    "em_region": 89.3,
    "score_pixel_log": -45.2,
    "score_region": 209.8,
    "score_sym": true,
    "cl_pixel_log": -48.1,
    "cl_region": 209.8,
    "cl_sym": true,
    "closure_correction_pixel": -2.9,
    "closure_correction_region": 0.0,
    "is_collapsed": false
  },
  "region_heatmap": [[0.5, 1.2, ...], ...],
  "closure_map": [[0.1, 0.0, ...], ...],
  "metadata": {
    "iterations_used": 30000,
    "time_seconds": 2.3,
    "free_pixels": 128,
    "total_pixels": 256
  }
}
```

`image` 和 `targets` 以整数二维数组传递（灰度）或三维数组（RGB）。`closure_map` 是前端“闭包修正图”的数据源。前端负责渲染为 Canvas 像素。

> **参数校验**：当前后端会对基础参数做 400 校验，包括尺寸范围、`alpha/tau` 合法性、`translate_period` 范围，以及 `c4` 对称要求 `width == height`。

#### 4.5.3 `/api/sweep` 请求/响应

**请求体** (`application/json`)：

```json
{
  "base_params": {
    "width": 16, "height": 16, "levels": 8,
    "color_mode": "grayscale", "target_mode": "random_smooth",
    "seed": 42, "max_iter": 30000,
    "sigma": 0.3, "tau": 0.3, "beta": 5.0, "gamma": 10.0,
    "K": 255, "symmetry": ["lr"], "epsilon": 0
  },
  "stream": true,
  "sweep": {
    "axis_x": { "param": "alpha", "min": 0.05, "max": 1.0, "steps": 20 },
    "axis_y": { "param": "tau",   "min": 0.1,  "max": 0.8, "steps": 10 }
  },
  "order_params": ["phi_em", "phi_cl", "xi", "phi_dir", "phi_mirror"]
}
```

**字段说明**：
- `base_params`：基线参数，与 `/api/generate` 相同的键。
- `stream`：布尔值。`true` 时返回 SSE 流；省略或 `false` 时返回一次性 JSON（用于测试、脚本调用和兼容性回退）。
- `sweep.axis_x`：X 轴扫描参数名和范围。`steps` 个等距取值。
- `sweep.axis_y`（可选）：Y 轴扫描参数。省略时为 1D 扫描（仅 X 轴）。
- `order_params`：需要计算的序参量列表（见下表）。

可用序参量标识符：

| 标识符 | 序参量 | 定义 |
|--------|--------|------|
| `phi_em` | 归一化涌现强度 | §2.8.1 $\phi_{\text{em}}$ |
| `phi_cl` | 闭包修正比率（%） | §2.8.1 $\phi_{\text{cl}}$ |
| `xi` | 空间相关长度（像素） | §2.8.1 $\xi$ |
| `phi_dir` | 方向序参量 | §2.8.2 $\phi_{\text{dir}}$ |
| `phi_mirror` | 镜像序参量 | §2.8.2 $\phi_{\text{mirror}}$ |
| `dir_region` | 区域层直接代价 | §2.6 S1 |
| `score_region` | 区域层总评分 | §2.6 S3 |
| `is_collapsed` | 是否坍缩（0/1） | §2.6 S4 |

**JSON 回退响应体** (`application/json`)：

```json
{
  "axis_x": { "param": "alpha", "values": [0.05, 0.1, ..., 1.0] },
  "axis_y": { "param": "tau",   "values": [0.1, 0.178, ..., 0.8] },
  "results": {
    "phi_em":     [[0.82, 0.75, ...], ...],
    "phi_cl":     [[35.2, 28.1, ...], ...],
    "xi":         [[6.3,  4.1, ...], ...],
    "phi_dir":    [[0.12, 0.08, ...], ...],
    "phi_mirror": [[0.71, 0.65, ...], ...]
  },
  "thumbnails": [
    [{"image": [[...]], "alpha": 0.05, "tau": 0.1}, ...],
    ...
  ],
  "metadata": {
    "total_runs": 200,
    "time_seconds": 145.3,
    "estimated_alpha_c": 0.35
  }
}
```

`results` 中每个序参量是 `[steps_y][steps_x]` 的二维数组（1D 扫描时为 `[1][steps_x]`）。`thumbnails` 是可选的采样缩略图（每个 cell 的图像数组），`thumbnail_stride` 控制间隔（默认每 4 个点取一张）。

`metadata.estimated_alpha_c` 仅在 X 轴包含 `alpha` 时返回——取 $|d\phi_{\text{em}}/d\alpha|$ 最大处的 $\alpha$ 值。

**SSE 流模式**：当 `stream=true` 时，`/api/sweep` 返回 `text/event-stream`，事件格式为：

- `event: progress`，`data: {"completed": ..., "total": ..., "last_order_params": ...}`
- `event: done`，`data: <完整最终 JSON>`
- `event: error`，`data: {"message": ...}`

### 4.6 `engine/order_params.py` — 序参量计算

```python
def compute_order_params(
    image: np.ndarray,          # shape (H, W) 或 (H, W, 3)
    scores: LayerScores,        # compute_scores 的输出
    params: dict,
    requested: list[str]        # 序参量标识符列表
) -> dict[str, float]:
    """计算请求的序参量，返回 {标识符: 值} 字典。"""
```

#### 4.6.1 $\phi_{\text{em}}$（归一化涌现强度）

```python
phi_em = scores.em_region / (H * W)
```

#### 4.6.2 $\phi_{\text{cl}}$（闭包修正比率）

```python
EPS0 = 1e-10
phi_cl = abs(scores.cl_pixel - scores.score_pixel) / max(abs(scores.score_pixel), EPS0) * 100
```

值域 $[0, \infty)$。工程上 clamp 到 $[0, 100]$ 以便可视化。

#### 4.6.3 $\xi$（空间相关长度）

```python
def spatial_correlation_length(image: np.ndarray) -> float:
    """通过径向自相关函数估计相关长度。"""
```

**实现**：
1. 将图像归一化到 $[0,1]$。
2. 计算 2D 自相关函数（FFT 加速）：`acf = ifft2(|fft2(image - mean)|^2)`。
3. 将 2D ACF 径向平均为 1D 函数 $C(r)$。
4. 找到 $C(r) < C(0) \cdot e^{-1}$ 的最小 $r$。
5. 若 $C(r)$ 在整个范围内未降到阈值以下，取 $\xi = \min(H, W) / 2$。

#### 4.6.4 $\phi_{\text{dir}}$（方向序参量）

```python
# C_H, C_V 在 region_costs 中已计算（水平对和垂直对的代价分别求和）
avg_h = C_H / max(H * (W - 1), 1)
avg_v = C_V / max((H - 1) * W, 1)
phi_dir = abs(avg_h - avg_v) / (avg_h + avg_v + EPS0)
```

**需要** `region_costs` 额外返回 `(C_H, C_V)` 分量（或由此函数内部重新计算）。

#### 4.6.5 $\phi_{\text{mirror}}$（镜像序参量）

```python
def mirror_order_param(image: np.ndarray) -> float:
    norm = (image.max() - image.min()) or 1.0  # 防除零
    left = image[:, :W//2]
    right = image[:, -1:W-W//2-1:-1]  # 镜像翻转右半
    return 1.0 - np.mean(np.abs(left - right) / norm)
```

### 4.7 `engine/phase_scan.py` — 相图扫描引擎

```python
def run_sweep(
    base_params: dict,
    axis_x: dict,                # {"param": str, "min": float, "max": float, "steps": int}
    axis_y: dict | None,         # None → 1D 扫描
    order_param_ids: list[str],
    thumbnail_stride: int = 4,
    callback: Callable | None = None,  # 进度回调 (completed, total)
) -> SweepResult:
    """执行相图扫描。"""
```

**实现要点**：

1. **参数网格生成**：`np.linspace(axis.min, axis.max, axis.steps)` 生成等距数组。2D 时做外积。
2. **循环生成**：对网格中的每个 $(x, y)$ 点，合并到 `base_params` 中调用 `simulated_annealing`。
3. **序参量计算**：每次生成后调用 `compute_order_params`。
4. **缩略图采样**：每 `thumbnail_stride` 个点保存图像。
5. **$\alpha_c$ 估计**：若 X 轴为 `alpha`，计算 $\phi_{\text{em}}$ 的数值梯度，取绝对值最大处。
6. **种子策略**：**每个网格点使用相同的 `seed`**，确保目标色 $t_p$ 跨扫描一致（仅观察参数变化的效果，排除随机性）。

**性能预估**（16×16, 30000 iter）：
- 单次生成 ~2s → 20 步 1D 扫描 ~40s → 20×10 2D 扫描 ~400s（约 7 分钟）。
- 应当在后端用 `asyncio.to_thread` 包裹以避免阻塞事件循环。
- **可选加速**：2D 扫描可用 `concurrent.futures.ProcessPoolExecutor` 并行。

```python
@dataclass
class SweepResult:
    axis_x_values: list[float]
    axis_y_values: list[float]      # 1D 扫描时为 [0.0]
    order_params: dict[str, list[list[float]]]  # {id: [[y0_x0, y0_x1, ...], [y1_x0, ...]]}
    thumbnails: list[list[dict]]    # 采样的 {image, params} 列表
    estimated_alpha_c: float | None
    total_time: float

---

## 5 前端规范

### 5.1 页面布局

```
┌──────────────────────────────────────────────────┐
│  Fibered CSP Image Generator           [Generate]│
├────────────┬─────────────────────┬───────────────┤
│            │                     │               │
│  参数面板   │    图像展示区        │  评分仪表盘   │
│  (左侧栏)  │    (中央)           │  (右侧栏)     │
│            │                     │               │
│  ┌───────┐ │  ┌───────┐ ┌─────┐ │  Dir_pixel:   │
│  │ 画布  │ │  │ 生成  │ │目标 │ │  -45.2 (log) │
│  │ 尺寸  │ │  │ 结果  │ │偏好 │ │               │
│  ├───────┤ │  └───────┘ └─────┘ │  Dir_region:  │
│  │ 涌现  │ │                     │  120.5        │
│  │ 参数  │ │  ┌───────┐ ┌─────┐ │               │
│  ├───────┤ │  │ 区域  │ │闭包 │ │  Em_region:   │
│  │ 边缘  │ │  │ 热力图│ │修正 │ │  89.3         │
│  │ 参数  │ │  └───────┘ └─────┘ │               │
│  ├───────┤ │                     │  cl_pixel:    │
│  │ 对称  │ │                     │  -48.1 (log)  │
│  │ 参数  │ │                     │               │
│  ├───────┤ │                     │  Collapsed:   │
│  │ 搜索  │ │                     │  No ✓         │
│  │ 参数  │ │                     │               │
│  └───────┘ │                     │               │
└────────────┴─────────────────────┴───────────────┘
```

### 5.2 参数面板分组和控件

#### 画布参数组

| 参数 | 控件 | 范围 | 默认 | 步长 |
|------|------|------|------|------|
| Width | number input | 4–64 | 16 | 1 |
| Height | number input | 4–64 | 16 | 1 |
| Color mode | select | grayscale / rgb | grayscale | — |
| Levels | select | 4 / 8 / 16 / 32 | 8 | — |
| Seed | number input | 0–999999 | 42 | 1 |
| Target mode | select | 见 §4.4.4 | random_smooth | — |

#### 涌现参数组（标红突出——核心旋钮）

| 参数 | 控件 | 范围 | 默认 | 步长 | 说明 |
|------|------|------|------|------|------|
| **α (emergence)** | **range slider** | **0.05–1.0** | **0.5** | **0.05** | **最核心旋钮，大字体显示当前值** |
| K | range slider | 10–1000 | 255 | 5 | 归一化常数 |

#### 像素层参数组

| 参数 | 控件 | 范围 | 默认 | 步长 |
|------|------|------|------|------|
| σ (preference strength) | range slider | 0.05–2.0 | 0.3 | 0.05 |

#### 边缘区域层参数组

| 参数 | 控件 | 范围 | 默认 | 步长 |
|------|------|------|------|------|
| τ (edge threshold) | range slider | 0.05–0.95 | 0.3 | 0.05 |
| β (cross-edge penalty) | range slider | 0.1–20.0 | 5.0 | 0.1 |
| γ (intra-region penalty) | range slider | 0.1–30.0 | 10.0 | 0.1 |
| Direction strength | range slider | -1.0–1.0 | 0.0 | 0.1 |
| Direction angle | range slider | 0–180 | 0 | 5 |

#### 对称性层参数组

| 参数 | 控件 | 范围 | 默认 |
|------|------|------|------|
| Symmetry types | **multi-checkbox** | none/lr/ud/quad/c4/trans_h | none |
| ε (tolerance) | range slider | 0–(L-1)/2 | 0 |
| Translate period | number input | 2–W | 4 |

**交互约束**：选择 `c4` 时自动强制 $H = W$。选择 `quad` 时自动勾选 `lr` 和 `ud`。选择 `none` 时禁用 `ε` 和 `translate_period`。

#### 搜索参数组（默认折叠）

| 参数 | 控件 | 范围 | 默认 |
|------|------|------|------|
| Max iterations | number input | 1000–500000 | 30000 |
| T_init | number input | 0.1–100 | 10.0 |
| T_min | number input | 0.001–1.0 | 0.01 |
| Cooling rate | range slider | 0.990–0.9999 | 0.9995 |

### 5.3 图像展示区

显示 4 张图像（Canvas 渲染，自动放大到可见尺寸——像素数小时每像素放大为 $\lfloor 512/W \rfloor$ 的方块）：

| 位置 | 内容 | 说明 |
|------|------|------|
| 左上 | **生成结果** | 最终图像，主画面 |
| 右上 | **目标偏好图** | $t_p$ 的可视化 |
| 左下 | **区域代价热力图** | 每像素邻域代价均值，冷色=低代价/热色=高代价 |
| 右下 | **闭包修正图** | $\|\Delta_{\text{pixel}}(i,j)\|$ 的可视化，显示闭包对每像素的修正幅度 |

### 5.4 评分仪表盘

右侧固定宽度面板，实时显示最终图像的评分分解：

- 三层各自的 Dir / Em / Score / cl 值
- 闭包修正量（百分比）
- 坍缩状态指示灯（绿=正常 / 红=坍缩）
- 搜索耗时

### 5.5 前端交互流程

```
用户调整参数 → 点击 [Generate] →
  前端收集所有参数值 → POST /api/generate →
  后端执行搜索 → 返回 JSON →
  前端渲染 4 张图 + 更新仪表盘
```

**不实现自动触发**（即滑动 slider 不自动生成）。原因：每次生成需要数秒，自动触发会造成请求堆积。由用户主动点击。

### 5.6 相图扫描面板（Phase Diagram Tab）

页面顶部增加 **Tab 切换**：`[单次生成] | [相图扫描]`。切换到"相图扫描"时，中央区域替换为相图扫描面板。

#### 5.6.1 布局

```
┌──────────────────────────────────────────────────────┐
│  [单次生成]  [相图扫描]                                │
├────────────┬─────────────────────────────────────────┤
│  扫描设置   │                                         │
│  ┌───────┐ │   ┌─────────────────────┐ ┌──────────┐ │
│  │X 轴参数│ │   │   相图热力图        │ │ 序参量    │ │
│  │Y 轴参数│ │   │   (Canvas)          │ │ 选择器   │ │
│  │步数    │ │   │   悬停显示缩略图    │ │          │ │
│  │序参量  │ │   │                     │ │ ○ φ_em   │ │
│  │选择    │ │   │                     │ │ ○ φ_cl   │ │
│  │        │ │   │                     │ │ ○ ξ      │ │
│  ├───────┤ │   └─────────────────────┘ │ ○ φ_dir  │ │
│  │[Sweep]│ │                           │ ○ φ_mirror│ │
│  │进度条  │ │   ┌─────────────────────┐ └──────────┘ │
│  │估计时间│ │   │  1D 曲线图 / 切片   │              │
│  └───────┘ │   │  (SVG 或 Canvas)     │              │
│            │   └─────────────────────┘              │
└────────────┴─────────────────────────────────────────┘
```

#### 5.6.2 控件

**扫描设置面板**：

| 控件 | 说明 |
|------|------|
| X 轴参数 | select：alpha / tau / beta / gamma / sigma / K |
| X 范围 | min + max + steps（默认 0.05, 1.0, 20） |
| Y 轴参数 | select（含"无"选项 → 1D 扫描） |
| Y 范围 | min + max + steps（仅 Y 非"无"时显示） |
| 序参量选择 | multi-checkbox（默认全选 φ_em + φ_cl） |
| [Sweep] 按钮 | 浏览器模式下以 `stream=true` 触发 SSE 扫描；再次点击则取消 |
| 进度条 | 实时显示 `completed / total` |

**基线参数**：继承"单次生成" Tab 中当前设定的所有参数（X/Y 轴参数除外）。

#### 5.6.3 可视化

**2D 相图热力图**（Canvas 渲染）：
- X 轴 = axis_x 参数，Y 轴 = axis_y 参数，颜色 = 当前选中的序参量值。
- 色标：viridis 色阶（可配置），右侧显示色标条。
- 鼠标悬停某个 cell 时，在 tooltip 中显示该点的缩略图 + 所有序参量数值。
- 点击某个 cell 时，自动将参数填入"单次生成" Tab 并切换过去（方便精细调查）。

**1D 曲线图**（2D 模式下也可用——选择 Y 轴某行做切片）：
- X 轴 = 扫描参数，Y 轴 = 序参量值。
- 支持多序参量叠加绘制（左右双 Y 轴）。
- 用竖虚线标注 $\alpha_c$ 估计位置（若有）。
- 缩略图画廊横排显示在曲线下方。

#### 5.6.4 进度与取消

- 扫描开始后 [Sweep] 按钮变为 **[Cancel]**。
- 后端以 **SSE (Server-Sent Events)** 推送进度：每完成一个网格点发送 `{completed, total, last_order_params}`。
- 前端增量更新热力图（已完成的 cell 实时着色，未完成的 cell 显示灰色）。
- 取消时前端关闭 SSE 连接，后端捕获到断开后中止计算。

> **实现变更**：浏览器前端默认以 `stream=true` 使用 `/api/sweep` 的 **SSE 流**模式；同时，后端保留一次性 JSON 回退模式，便于测试与脚本调用。SSE 模式下，最终结果在最后一条 `event: done` 事件中以完整 JSON 发出，前端收到后再统一解析展示。

---

## 6 关键实现细节

### 6.1 增量评分

模拟退火每步仅修改 1 个基本域像素（+ 对称镜像像素）。增量评分避免全图重算：

**像素层增量**：设修改像素 $p$ 的值从 $v_{\text{old}}$ 变为 $v_{\text{new}}$：

$$\Delta_{\text{pixel}} = \ln \varphi(v_{\text{new}}) - \ln \varphi(v_{\text{old}})$$

对对称镜像像素同理累加。总变化 $\Delta_{\text{pixel,total}}$ 直接加到 `dir_pixel_log` 上。

**区域层增量**：设修改像素 $p$ 的 4-邻居为 $N(p)$。受影响的约束对为 $\{(p, q) : q \in N(p)\}$。

$$\Delta_{\text{region}} = \sum_{q \in N(p)} \big[\varphi_R(v_{\text{new}}, a(q)) - \varphi_R(v_{\text{old}}, a(q))\big]$$

对对称镜像像素同理。

**涌现增量**：涌现贡献 $\mathrm{Em}_{\text{region}} = (f_1)_!(\mathrm{Dir}_{\text{pixel}})$ 取决于**全局**像素层评分，无法局部增量——但 $(f_1)_!$ 是单变量函数，仅需更新 `dir_pixel_log`（已增量完成）后重新调用一次 $(f_1)_!(\exp(\text{dir\_pixel\_log}))$。这是 $O(1)$ 操作。

**截面化闭包增量**：同理，仅 3 步标量运算（§2.6 S4），$O(1)$。

**总计**：每步 $O(|N(p)| \times \text{对称倍数})$，即 $O(1)$。

### 6.2 对数域像素层的完整性

所有像素层运算在对数域进行：

| 原域操作 | 对数域等价 |
|------|------|
| $\prod_p \varphi_p(v)$ | $\sum_p \ln \varphi_p(v)$ |
| $s_1 \times s_2$ | $\ln s_1 + \ln s_2$ |
| $\min(s_1, s_2)$ | $\min(\ln s_1, \ln s_2)$ |
| $f_1^*(c) = e^{-(c/K)^\alpha}$ | $\ln f_1^*(c) = -(c/K)^\alpha$ |
| $(f_1)_!(e^x) = K \cdot (-x)^{1/\alpha}$ | 接受 $\ln p = x$ 作为输入 |

### 6.3 搜索中的退火调度

线性乘法冷却：$T_{n+1} = T_n \times r$，$r$ 为冷却率。

Metropolis 接受概率：$P(\text{accept}) = \min(1, \exp(-\Delta \mathrm{Obj} / T))$，其中 $\Delta \mathrm{Obj}$ 为目标函数变化量（越小越好）。

目标函数的加权（推荐使用 **closure-aware** 版本）：

$$\mathrm{Obj}(a) = w_{\text{region}} \cdot cl_{\text{region}} - w_{\text{pixel}} \cdot cl_{\text{pixel,log}}$$

其中 $cl_{\text{pixel,log}} = \ln(s_{\text{pixel}}) \le 0$。对称层在精确消元下恒满足，不参与 $\mathrm{Obj}$。取 $w_{\text{region}} = 1.0$、$w_{\text{pixel}} = 0.01$（区域优先）。

> 若工程上为了调试先使用 `Dir` 级代理目标，也应在文档和实验结论中明确标注其为“搜索代理目标”，避免与理论层定义的最终评分混淆。

### 6.4 随机种子的确定性

**必须**：给定相同的种子和参数，生成结果完全相同。实现方法：`np.random.default_rng(seed)` 贯穿目标色生成和搜索过程。

---

## 7 参数推荐与预期效果

### 7.1 $\alpha$ 扫描的推荐参数组

固定以下参数，仅扫描 $\alpha$：

```
width=height=16, levels=8, target_mode=random_smooth, seed=42
sigma=0.3, tau=0.3, beta=5.0, gamma=10.0
symmetry=["lr"], epsilon=0, max_iter=50000
```

$\alpha$ 取 `[1.0, 0.8, 0.5, 0.3, 0.1]`。

### 7.2 预期效果对照表

| $\alpha$ | $f_!$ 性质 | 预期视觉 | 关键指标 |
|---|---|---|---|
| 1.0 | 幺半（无涌现） | 柔和的对称云雾 | $\mathrm{Em}_{\text{region}}$ 可分解 |
| 0.8 | 弱 oplax | 开始出现模糊色块 | 闭包修正量 < 5% |
| 0.5 | 中等 oplax | 明确的色块边界 | 闭包修正量 5–15% |
| 0.3 | 强 oplax | 锐利的色块 + 对称图案 | 闭包修正量 15–40% |
| 0.1 | 极端 oplax | 高对比度色块或闭包性坍缩 | 可能整图坍缩 |

### 7.3 对称组合推荐实验

| 实验名 | 设置 | 预期 |
|---|---|---|
| 蝴蝶 | lr, $\alpha=0.3$ | 对称色块，类似蝴蝶翅膀 |
| 万花筒 | quad, $\alpha=0.3$ | 四重对称花纹 |
| 瓷砖 | c4, $\alpha=0.3$, $H=W=16$ | 旋转对称花纹 |
| 壁纸 | trans_h, T=4, $\alpha=0.5$ | 水平重复条纹 |
| 相变线 | lr, $\alpha$ 扫 0.05–1.0 步长 0.05 | 涌现相变点（闭包修正量突变处） |

### 7.4 涌现相变实验

#### 7.4.1 $\alpha$ 相变曲线（1D 扫描）

**目标**：定位 $\alpha_c$ 并验证相变的存在性。

**设置**：
```
axis_x: alpha, min=0.05, max=1.0, steps=20
base: 16×16, levels=8, random_smooth, seed=42, lr对称
sigma=0.3, tau=0.3, beta=5.0, gamma=10.0, K=255
序参量: phi_em, phi_cl, xi
```

**预期结果**：
- $\phi_{\text{em}}$ 曲线在 $\alpha \approx 0.3$–$0.5$ 出现拐点（二阶导变号）。
- $\xi$ 从 $\approx 1$（$\alpha = 1.0$）跳跃到 $> 4$（$\alpha < \alpha_c$）。
- $\phi_{\text{cl}}$ 在相变点附近从 < 5% 跳到 > 15%。
- 缩略图画廊直观展示从"模糊噪声"到"清晰色块"的视觉相变。

#### 7.4.2 $\alpha$ – $\tau$ 相图（2D 扫描）

**目标**：探索涌现强度与边缘阈值的联合效应，绘制相边界。

**设置**：
```
axis_x: alpha, min=0.05, max=1.0, steps=20
axis_y: tau,   min=0.1,  max=0.8, steps=10
base: 16×16, levels=8, random_smooth, seed=42, 无对称
序参量: xi（空间相关长度）
```

**预期结果**：
- 相图右上角（高 $\alpha$，高 $\tau$）：$\xi \approx 1$（无结构相）。
- 相图左下角（低 $\alpha$，低 $\tau$）：$\xi$ 大（大色块结构相），但可能坍缩。
- 相边界呈现从右上到左下的斜线趋势——$\alpha$ 降低时，即使 $\tau$ 较大也能形成结构。
- 用 $\xi = 3$ 等高线作为"有序相 / 无序相"的边界线。

#### 7.4.3 $\alpha$ – $\sigma$ 相图

**目标**：观察偏好强度如何影响相变点。

**设置**：
```
axis_x: alpha, min=0.05, max=1.0, steps=20
axis_y: sigma, min=0.1,  max=1.5, steps=10
```

**预期**：$\sigma$ 大（弱偏好）时相变点 $\alpha_c$ 更低（需要更强的涌现才能产出结构）；$\sigma$ 小（强偏好）时 $\alpha_c$ 更高（即使弱涌现也足以形成结构）。

### 7.5 对称性自发破缺实验

#### 7.5.1 无约束下的自发对称

**设置**：
```
axis_x: alpha, min=0.05, max=1.0, steps=20
base: 16×16, levels=8, random_smooth, seed=42, **无对称约束**
序参量: phi_mirror, phi_dir
```

**预期**：
- $\alpha = 1.0$：$\phi_{\text{mirror}} \approx 0.5$（无自发对称），$\phi_{\text{dir}} \approx 0$（各向同性）。
- $\alpha < 0.3$：$\phi_{\text{mirror}}$ 偶尔 > 0.7（某些种子下系统自发选择了近似镜像对称的解）。
- $\phi_{\text{dir}}$ 在低 $\alpha$ 下偶发性偏离 0（自发选择水平或垂直条纹方向）——不同种子的 $\phi_{\text{dir}}$ 符号随机翻转（典型的对称性破缺特征：系统选择一个方向但选哪个是随机的）。

#### 7.5.2 多种子统计

**设置**：固定 $\alpha = 0.3$，扫描 `seed` 从 0 到 49（50 次独立运行）。计算 $\phi_{\text{mirror}}$ 和 $\phi_{\text{dir}}$ 的分布。

**预期**：
- $\phi_{\text{mirror}}$ 分布应为双峰（一部分运行自发对称，一部分不对称）。
- $\phi_{\text{dir}}$ 分布应关于 0 对称（正负各半），但每次运行的绝对值显著。

> 多种子统计可复用 `/api/sweep`——将 `seed` 作为扫描参数（需小幅扩展：允许整数参数步进）。

---

## 8 验收标准

### 8.1 功能验收

- [ ] 8×8 灰度 + 无对称 + $\alpha=1.0$ 可在 1 秒内生成。
- [ ] 16×16 灰度 + 左右对称 + $\alpha=0.5$ 可在 5 秒内生成。
- [ ] 32×32 灰度 + 四重对称 + $\alpha=0.3$ 可在 30 秒内生成。
- [ ] 所有 6 种对称类型均可正确消元和填充。
- [ ] 坍缩传播正确：对称层 $\bot$ → 区域层 $\infty$ → 像素层 0。
- [ ] 固定种子 + 参数的输出完全可复现。
- [ ] 前端 4 张图均正确渲染。
- [ ] 评分仪表盘所有数值与后端返回一致。
- [ ] 1D 扫描（20 步）可在 60 秒内完成（16×16, 30000 iter）。
- [ ] 2D 扫描（20×10）热力图正确渲染，鼠标悬停显示缩略图。
- [ ] 序参量 $\phi_{\text{em}}, \phi_{\text{cl}}, \xi$ 计算正确（对 $\alpha=1.0$ 的已知 baseline 回归）。
- [ ] 1D 曲线图正确标注 $\alpha_c$ 估计位置。
- [ ] 相图扫描 Tab 与单次生成 Tab 可正常切换，参数互通。
- [ ] 扫描进度实时显示，可中途取消。

### 8.2 数值验收

使用 §6.1（论文）的微型实例 ($2 \times 1$, $a=(128,200)$, $\alpha=1.0$) 作为回归测试：

| 指标 | 期望值 | 容差 |
|------|--------|------|
| $\mathrm{Dir}_{\text{pixel}}$ | $\approx 0.394$ | $\pm 0.001$ |
| $\mathrm{Dir}_{\text{region}}$ | 72 | 精确 |
| $f_!(0.394)$（$\alpha=1.0$，$K=255$） | $\approx 237.6$ | $\pm 0.5$ |
| $\mathrm{cl}_{\text{pixel}}$ | $\approx 0.296$ | $\pm 0.001$ |

使用 §6.2（论文）的非幺半实例 ($\alpha=0.5$) 作为第二组回归测试：

| 指标 | 期望值 | 容差 |
|------|--------|------|
| $f_!(0.394)$（$\alpha=0.5$，$K=255$） | $\approx 221.5$ | $\pm 0.5$ |
| $\mathrm{cl}_{\text{pixel}}$ | $\approx 0.342$ | $\pm 0.001$ |
| 涌现偏差 $\delta$（$p_1=0.8, p_2=0.6$） | $\approx 58.2$ | $\pm 0.5$ |

### 8.3 非功能验收

- [ ] 后端无第三方 AI/ML 依赖（仅 FastAPI + NumPy + uvicorn）。
- [ ] 前端无构建步骤（原生 HTML/CSS/JS）。
- [ ] `python server.py` 一条命令启动。
- [ ] 所有 API 返回有意义的错误信息（参数越界时返回 400 + 具体字段）。
