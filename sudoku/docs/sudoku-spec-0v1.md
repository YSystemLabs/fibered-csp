# Fibered-CSP（路线 A）DSL + 最小可运行求解流程（FAC/传播 + 搜索）
## Sudoku 9×9 参考规格 v0.1（工程落地版）

> 目标：用户只写“自然层”（行/列/宫）的 all-different + givens；编译器按“路线 A（派生式构造）”自动生成细层（二元不等）约束，从而默认满足层间一致性；运行时用传播（FAC 的可执行子集）+ 回溯搜索得到完整解。

---

## 0. 目标与非目标

### 0.1 目标
- **建模**：提供一套 DSL，能声明 Sudoku 变量、域、作用域（Row/Col/Box）、约束（all-different）与 givens。
- **编译**：把 Unit 层 `all_different(U)` **自动派生**为 Pair 层所有 `neq(x,y)`（去重）。
- **求解**：实现最小求解器
  - 传播：二元 neq 剪枝 + unit 层 hidden single（可选再加 naked single）
  - 搜索：MRV 回溯 + 传播驱动

### 0.2 实现语言与环境
- **语言**：Python 3.10+（快速原型优先）。
- **测试**：pytest；无第三方求解器依赖。
- **域表示**：`int` 位掩码（9 bit，bit $k$ 表示 digit $k+1$ 在域中），兼顾紧凑性与集合操作效率。
- **递归限制**：程序入口处须显式设置 `sys.setrecursionlimit(2000)`（ASSIGN ↔ ELIMINATE 交替递归最坏栈深约 800+）。

### 0.3 非目标（v0.1 先不做）
- 通用富集值域（软代价/半环）与一般 \(f^*, f_!\) 的全泛化实现（先做硬约束版本）。
- all-different 的最强 GAC（如 Régin matching）；v0.1 先用低成本规则跑通。
- 自动推断层级指派（\(\Sigma\) 学习）；v0.1 固定两层链：`Pair < Unit`。

---

## 1) DSL：声明式模型

### 1.1 基础概念
- **levels**：层级（偏序/链）
  - `Pair < Unit`
- **domains**：值域
  - `Digit = {1..9}`
- **vars**：变量
  - `Cell[r=1..9, c=1..9] : Digit`
- **scopes**：作用域模板（生成实例）
  - `Row[r]`：第 r 行 9 格
  - `Col[c]`：第 c 列 9 格
  - `Box[br,bc]`：第 (br,bc) 宫 9 格（br,bc∈{0,1,2}）
- **constraints**：约束（用户只写 Unit 层）
- **givens**：初始赋值（初始化域为单点）

### 1.2 Sudoku DSL 示例（YAML 风格）
```yaml
levels:
  - Pair < Unit

domains:
  Digit: 1..9

vars:
  Cell[r=1..9,c=1..9]: Digit

scopes:
  Row[r=1..9]:  { Cell[r,c] for c in 1..9 }
  Col[c=1..9]:  { Cell[r,c] for r in 1..9 }
  Box[br=0..2,bc=0..2]:  # br/bc 从 0 起（整除映射：br=⌊(r-1)/3⌋），其余索引从 1 起
    { Cell[3*br+i,3*bc+j] for i in 1..3, j in 1..3 }

constraints:
  - name: RowAllDiff
    level: Unit
    scope: Row[*]
    body: all_different(scope)
    derive:
      down: pairwise_neq  # 路线A：自动派生到 Pair 层

  - name: ColAllDiff
    level: Unit
    scope: Col[*]
    body: all_different(scope)
    derive:
      down: pairwise_neq

  - name: BoxAllDiff
    level: Unit
    scope: Box[*]
    body: all_different(scope)
    derive:
      down: pairwise_neq

givens:
  - Cell[1,1]=5
  - Cell[1,2]=3
  # ...
```

---

## 2) 路线 A：编译期派生式构造（保证一致性）

> 原则：**用户不直接写细层（Pair）约束**；细层约束统一由粗层（Unit）约束通过标准构造派生，避免手工不一致。

### 2.1 标准派生规则：`all_different(U)` ⇒ `pairwise_neq`

对任意 Unit scope (U={x_1,\dots,x_9})：

* 生成所有二元不等约束：对所有 (1\le i<j\le 9)，生成 `neq(x_i, x_j)`。
* 全局去重：若同一对变量在多处派生到同一 `neq`，只保留一条实例。去重使用**规范化无序对** `(min(x,y), max(x,y))`（按行优先线性索引排序），用 `set` 或 `frozenset` 实现。

> 说明：这相当于把 coarse 的约束通过固定的“下推/拉回”机制变成 finer 的二元约束族（硬约束语义下 sound）。

### 2.2 禁止手写 Pair（默认）

* v0.1 默认：`constraints` 中 `level: Pair` 的项 **拒绝加载**，除非标注 `kind: local_patch`。

### 2.3 受控扩展：`local_patch`（可选）

允许表达“细层额外信息/启发式”但必须受控：

```yaml
- name: PatchExample
  level: Pair
  scope: Pair(Cell[2,3],Cell[2,7])
  body: forbid_equal
  kind: local_patch
```

**合法性检查（v0.1 编译期静态检查）**

* **作用域合法性**：patch 的变量对 `(x, y)` 必须属于 `Peers` 关系（即同行/同列/同宫）。对非 peer 变量对的 patch 在编译期**直接拒绝**——这些变量之间不存在已派生的 neq 约束，额外施加约束超出了路线 A 的"收紧已有约束"语义。
* **方向合法性**：patch 的效果只能**收紧**细层域（如额外禁止某些值对），不能松弛已派生的 neq（如"允许相等"）。v0.1 `body` **仅允许** `forbid_equal`（与已有 neq 语义一致或冗余）。`forbid_pair(v1, v2)`（禁止特定值对，严格强于 neq）需额外的表约束传播逻辑，延后至 v0.1.5。
* **冗余检测**（可选警告）：若 patch 等价于已派生的 neq（如 `forbid_equal` 作用于已有 peer 对），编译器发出 `REDUNDANT_PATCH` 警告但不拒绝。

> **v0.1 定位**：`local_patch` 在 v0.1 中为**保留接口**——由于 `body` 仅允许 `forbid_equal`（与已派生 neq 语义冗余），它在当前版本不会带来额外推理能力。真正有意义的 patch（如 `forbid_pair(v1,v2)` 值对约束）需 v0.1.5 引入表约束传播后方能实质生效。

---

## 3) 编译产物（运行时输入）

### 3.0 CellId 与索引约定

* **CellId**（内部表示）：行优先线性索引 `idx = r * 9 + c`，其中 `r, c ∈ {0, ..., 8}`（0-based），`idx ∈ {0, ..., 80}`，对应 81 字符输入串的位置。
* **DSL / 用户输出**（日志、诊断、网格打印）：`Cell[r, c]`，`r, c ∈ {1, ..., 9}`（1-based）。转换关系：`r_user = r_internal + 1`，`c_user = c_internal + 1`。
* **位掩码域**：`D[idx]` 为 `int`，`bit k`（$k \in \{0,...,8\}$）表示 digit `k+1` 在域中。检查 digit `d`：`D[idx] & (1 << (d - 1))`。域大小：`popcount(D[idx])`。
* **UnitId**：27 个 unit 按 Row 0..8 → Col 0..8 → Box 0..8 编号（0-based，共 27 个），内部整数索引。面向用户的输出使用名称（如 `Row 1`、`Col 3`、`Box(1,2)`，1-based）。

### 3.1 变量与域

* `D[x]`：变量 x 的当前域（位掩码），初始 `D[x] = 0x1FF`（9 bit 全 1，即 {1..9}）；givens 设为单点。

### 3.2 约束实例

* `PairConstraints`：`neq(x,y)` 列表（由派生生成）——**仅用于编译期断言**（验证去重后恰好 810 条），运行时不参与传播。
* `UnitConstraints`：`all_different(U)` 列表（用户定义的 27 个 unit）

> **运行时权威来源**：传播引擎通过 `Peers[x]`（§3.3）进行 neq 传播，它是 PairConstraints 的邻接表视图。PairConstraints 本身在编译期验证完毕后即可丢弃（或仅保留用于调试输出）。

### 3.3 辅助结构（预计算）

* `Peers[x]`：与 x 同行/同列/同宫的所有变量集合（通常 20 个）
* `UnitsOf[x]`：包含 x 的 unit 列表（行、列、宫各 1 个）
* `Count[U][d]`：digit d 在 unit U 中的候选位置计数（用于增量 Hidden Single 检测）。当 `Count[U][d]` 降至 1 时需查找唯一候选 cell，此操作为 unit 内线性扫描（至多 9 次检查），代价可接受。
* `CellsOf[U]`：unit U 包含的 cell 列表（长度 9），用于上述线性扫描

### 3.4 初始化流程（严格顺序）

```
1. 对所有 x: D[x] = 0x1FF（9 bit 全 1，即 {1..9}）
2. 对所有 (U, d): Count[U][d] = 9
3. 对每个 given (x, d)，按 81 字符串的位置顺序（行优先，idx = 0, 1, ..., 80）逐个处理：
   调用 ASSIGN(x, d)  // 在 ASSIGN 内部完成删值、Count 更新、Hidden Single 级联
   若 Contradiction: 报错退出（given 自相矛盾）
4. 初始化完成后即为首轮传播不动点（ASSIGN 内含完整传播）
```

> **注**：步骤 3 中 ASSIGN 已包含入队与传播逻辑（见 §4.0），无需额外初始化队列。givens 处理顺序已固定（行优先），保证日志输出的确定性与可重放性。givens 之间的冲突会在 ASSIGN 的级联传播中自然检出（域变空 → Contradiction）。§8 的 givens 静态冲突检测是**编译期的提前检查**，与运行时检测互为双保险。

---

## 4) 传播引擎：FAC 的最小可执行子集（sound）

> v0.1 将 FAC 具体化为两条原子操作 + 递归级联传播，迭代到不动点（等价于一个"闭包/坍缩"的计算过程）。所有传播（Pair 层 neq AC + Unit 层 Hidden Single + Naked Single）统一由这两条原子操作内部触发，无需主循环区分层级。

### 4.0 原子操作定义

传播引擎的全部行为由以下两条互相递归的原子操作构成：

```
class Contradiction(Exception):
    """传播过程中检测到矛盾（域空或 unit 中 digit 无候选位置）。"""
    pass


ELIMINATE(x, d):
  """从 D[x] 中移除 digit d。级联触发 Count 更新、Hidden Single、Naked Single。"""
  if d not in D[x]: return        # 幂等：已删则跳过
  D[x].remove(d)
  trail.push(TrailEntry(var=x, digit=d))     # 记录删值，用于回溯恢复
  if |D[x]| == 0: raise Contradiction(cell=x)  # 域空 → 矛盾

  # --- Unit 层：增量 Hidden Single 检测 ---
  # Phase 1：先递减所有 unit 的 Count（保证 Count 与域同步）
  for each U in UnitsOf[x]:
    Count[U][d] -= 1

  # Phase 2：检查矛盾与 Hidden Single（此时 Count 已准确反映 d 从 D[x] 移除）
  for each U in UnitsOf[x]:
    if Count[U][d] == 0: raise Contradiction(unit=U, digit=d)  # unit U 无法放置 digit d
    if Count[U][d] == 1:
      candidates = [y for y in CellsOf[U] if d in D[y]]
      assert len(candidates) == 1, f"Count desync: Count[{U}][{d}]==1 but found {len(candidates)} candidates"  # 内部错误（非 Contradiction）
      y = candidates[0]
      ASSIGN(y, d)                            # Hidden Single：y 必须取 d

  # --- Naked Single 检测 ---
  if |D[x]| == 1:
    d_last = D[x] 中唯一值
    ASSIGN(x, d_last)                         # 域缩为单点 → 确定赋值


ASSIGN(x, d):
  """确定 x 的值为 d。通过 ELIMINATE 移除 D[x] 中除 d 外的所有值，然后对所有 peer 传播 neq。"""
  if d not in D[x]: raise Contradiction(cell=x, digit=d)  # 入口 guard

  # --- 缩域到单点（委托给 ELIMINATE，利用其幂等性 + trail + Count 更新）---
  for d' in 1..9:
    if d' != d and d' in D[x]:    # 实时检查当前域（非快照），自动跳过已被级联移除的值
      ELIMINATE(x, d')

  # --- Pair 层：neq 传播（向所有 peer 删 d）---
  for each y in Peers[x]:
    ELIMINATE(y, d)
```

> **重入安全说明**：旧版 ASSIGN 预计算快照 `others = D[x] \ {d}` 后逐项手动删值，但循环体内的 Hidden Single 级联可间接调用 `ELIMINATE(x, d'')`，提前移除尚未处理的 `d''`，导致重复删值、Count 双重递减和 trail 重复条目。新版改为在循环中**实时检查当前域**（`d' in D[x]`），并将删值操作委托给 `ELIMINATE`（利用其幂等性），从根本上消除重入问题。
>
> **Count 两阶段分离（实现修正）**：ELIMINATE 中 Hidden Single 检测必须将 Count 递减（Phase 1）与级联触发（Phase 2）**分为两趟循环**。原因：若交错执行（递减后立即检查并级联），处理 `UnitsOf[x]` 中第一个 unit U1 的 Hidden Single 级联可间接调用 `ELIMINATE(z, d)` 修改第二个 unit U2 的 Count，而此时 U2 尚未为 x 做递减，导致 Count 与实际域不同步（断言 `len(candidates)==1` 失败）。两阶段分离保证：Phase 1 完成后 Count 准确反映 d 从 D[x] 移除的事实，Phase 2 的级联检查基于准确的 Count 值，消除了跨 unit 级联的 Count desync 问题。
>
> **循环不变量**：ASSIGN 入口处 `d ∈ D[x]`（由 guard 保证）；ELIMINATE 入口处 `d` 可能在也可能不在 `D[x]`（幂等处理）。ASSIGN 结束后 `D[x] = {d}` 且所有 peer 的域中不含 `d`。
>
> **性能提示（可选优化——v0.1 不采用）**：级联传播下同一 cell 可能被多次触发 ASSIGN（如 Naked Single 触发 ASSIGN(x,d) 时 D[x] 已是 {d}）。此时 ASSIGN 内循环无值可删，但仍会对 20 个 peer 调用幂等 ELIMINATE。曾建议在 ASSIGN 入口 guard 后加 `if D[x] == {d}: return`，但**实现验证表明此优化不安全**：当 Naked Single 从 **peer 的传播链**（而非 ASSIGN 自身内循环）首次触发某 cell 的 ASSIGN 时，D[x] 已是 {d}（ELIMINATE 刚缩到单点），但 peers 从未被告知删除 d——早返回会跳过 peer 传播，违反 ASSIGN 后置条件。仅当存在**外层 ASSIGN(x, d)**（如 ASSIGN 自身内循环触发的 Naked Single）时早返回才安全，但运行时无法廉价区分这两种情况。v0.1 原型阶段此开销可忽略（最坏 ~1620 次 O(1) 幂等检查），故**不实施此优化**。若后续需要，安全替代方案是为每个 cell 追加 `_propagated[x]` 标记，仅在确认 peer 传播已完成后才允许跳过。
>
> **递归深度**：ASSIGN ↔ ELIMINATE 交替递归，最坏约 81 个 cell 各触发一次 ASSIGN，每次内部至多 8 次 ELIMINATE，总栈深约 800+。§0.2 已要求入口处设置 `sys.setrecursionlimit(2000)`。

### 4.1 Pair 层传播：neq 弧一致性

由 `ASSIGN(x, d)` 内部的 `for each y in Peers[x]: ELIMINATE(y, d)` 自动实现。

> **为何这等价于完整弧一致性（AC）**：对 neq 约束，弧 `(x, y)` 不一致当且仅当 `D[x]={v}` 且 `v ∈ D[y]`（此时 y 的值 v 无法在 x 的域中找到不等的支撑）。因此，neq 约束的 AC 推理**仅在某一端缩为单点时才会产生删值**——对大于 1 的 `|D[x]|`，y 的任何值都能在 `D[x]` 中找到不相等的支撑。换言之，v0.1 的"单点触发删值"规则在 neq 约束上与完整 AC-3 等价，不是简化。

### 4.2 Unit 层传播：Hidden Single（增量检测）

由 `ELIMINATE(x, d)` 内部的 `Count[U][d]` 更新自动触发。当 `Count[U][d]` 降至 1 时，找到该唯一候选 y 并调用 `ASSIGN(y, d)`。

> Naked Single（域缩为单点）同样由 `ELIMINATE` 内部自动检测并触发 `ASSIGN`。
>
> Naked Pair/Triple 等可在 v0.1.5 增加（见 §10）。

### 4.3 主循环

原子操作 ASSIGN/ELIMINATE 已内含完整的级联传播逻辑。主循环退化为：

```
def propagate_and_solve():
  # 初始化阶段已对所有 givens 调用 ASSIGN（见 §3.4），传播至不动点
  # 若不动点后仍有未定变量 → 进入搜索（§5）
  # 若所有变量已定 → 返回解
  # 若 Contradiction → 报告矛盾
```

> **无显式队列**：v0.1 采用递归调用链（ASSIGN ↔ ELIMINATE 互相递归）替代显式队列。两者在语义上等价（均计算传播不动点），递归实现更简洁且自然地与 trail 机制配合。若后续版本需要更精细的传播调度（如优先级队列），可将递归改写为显式工作队列。

---

## 5) 搜索（回溯）与启发式（最小可运行）

当传播不动点后仍有未定变量：

1. 选取未定变量 `x = argmin_{|D[x]|>1} |D[x]|`（MRV）；平局时选**行优先线性索引最小**的 cell（即 `idx = r * 9 + c` 最小者）。
2. 按**升序**遍历 `v in D[x]`（1, 2, ..., 9 中属于 D[x] 的值）：

   * 记录 trail 分界点 `mark = trail.size()`
   * 调用 `ASSIGN(x, v)`，内部完成全部传播（级联 ELIMINATE → Hidden Single → Naked Single）
   * 若未抛出 `Contradiction`：递归调用 `solve()`
   * 回溯（无论是 `Contradiction` 还是递归 `solve()` 失败）：按 trail 从当前位置逆序恢复到 `mark`，对每条 `TrailEntry(var=y, digit=d')`：
     - `D[y].add(d')`
     - `for each U in UnitsOf[y]: Count[U][d'] += 1`
3. 若全部 v 均触发 `Contradiction`：向上层抛出 `Contradiction`（回溯到上一层）

**Trail 结构**

```
TrailEntry = (var: CellId, digit: int)   # 记录"从 var 的域中删除了 digit"
```

选择 trail 而非全量快照的理由：(a) 空间 $O(\text{传播删值数})$ 远小于 $O(81 \times 9)$ 的全量拷贝；(b) trail 条目可直接复用为 §6 日志条目，避免两套数据结构。

**多解处理**：v0.1 默认**找到第一个解即停**。可选 `--count` 模式枚举所有解（找到解后不停止，继续回溯；记录解的数量）。此模式同时可用于验证唯一解性。

**正确性（v0.1）**

* 传播规则 sound（不会删掉真实可行解）；回溯枚举保证 completeness（最终能找到解或证无解）。

---

## 6) 日志与可解释性（强烈建议 v0.1 就做）

每一次域变化记录一条 `LogEntry`：

```
LogEntry:
  step_id   : int          # 全局递增序号（从 1 起），用于重放
  depth     : int          # 搜索深度（0 = 初始传播 / given 阶段，k = 第 k 次猜测后的传播）
  reason    : ReasonType   # 见下
  cell      : CellId       # 受影响的变量
  digit     : int          # 涉及的 digit
  evidence  : dict         # 关联证据（因 reason 而异）

ReasonType ∈ {
  GIVEN,                # 初始赋值
  PAIR_ELIMINATE,       # neq 传播：peer x 确定为 d → 从 cell 删 d
  NAKED_SINGLE,         # 域缩为单点 → 确定赋值
  HIDDEN_SINGLE,        # unit U 中 digit d 只剩 cell 可放 → 确定赋值
  GUESS,                # 搜索分支：猜测 cell = d
  BACKTRACK             # 回溯：撤销 cell 的 digit d
}
```

**evidence 字段示例**：

| reason | evidence 内容 |
|---|---|
| `GIVEN` | `{}` |
| `PAIR_ELIMINATE` | `{trigger: CellId, trigger_digit: d}` — 哪个 peer 确定了 d 导致本次删值 |
| `NAKED_SINGLE` | `{remaining_digit: d}` |
| `HIDDEN_SINGLE` | `{unit: UnitId, digit: d}` — 在哪个 unit 中 digit d 只剩此 cell |
| `GUESS` | `{domain_size_before: n}` — 猜测前域大小 |
| `BACKTRACK` | `{failed_value: d, depth: k}` |

> **日志与 trail 的关系**：trail 记录原子删值操作（每次 `D[x].remove(d)` 产生一条 `TrailEntry`）。日志是 trail 的**超集**——每条 trail 条目对应一条 LogEntry（附加 reason 和 evidence），此外 `GUESS`、`BACKTRACK` 类型的 LogEntry **没有**对应的 trail 条目（它们是搜索事件，不涉及具体删值）。日志将对应论文的"坍缩传播路径"证据链（见 §9 对照表）。

**求解统计**（传播结束 / 搜索结束后输出）：

```
Stats:
  eliminations   : int   # ELIMINATE 调用总次数（含幂等跳过）
  assignments    : int   # ASSIGN 调用总次数
  guesses        : int   # 搜索猜测次数
  backtracks     : int   # 回溯次数
  max_depth      : int   # 搜索最大深度
```

---

## 7) 输入输出格式

### 7.1 输入格式

支持标准 81 字符字符串：每个字符为 `1`-`9`（given）或 `0` / `.`（空格），按行优先排列。

**输入校验**：
* 合法字符集：`[0-9.]`（共 11 个字符）。含其他字符（字母、特殊符号等）报 `PARSE_ERROR`。
* 长度必须恰好为 81，否则报 `PARSE_ERROR`。

```
示例：530070000600195000098000060800060003400803001700020006060000280000419005000080079
```

> **YAML DSL**：§1.2 的 YAML 格式作为概念展示保留在 spec 中。v0.1 **仅实现 81 字符串输入**（数独的标准交换格式），YAML DSL 解析推迟到 v0.2，以减少 v0.1 工作量。
>
> **v0.1 编译退化说明**：v0.1 的"路线 A 编译"在 Sudoku 特化下退化为**固定生成**——硬编码 27 个 unit（9 Row + 9 Col + 9 Box）、`Peers[x]`（每 cell 20 个 peer）、810 条 neq 断言。无需实现通用 DSL parser 或通用派生引擎；这些是 v0.2 引入 YAML DSL 后的工作。

### 7.2 输出格式

* **解**：81 字符字符串（同输入格式，0 替换为解值）+ 可选 9×9 网格打印。
* **FAIL**：输出矛盾点信息（`Contradiction` 异常携带的 cell/unit/digit）。
* **统计**：输出 `Stats` 结构（见 §6）。
* **日志**：可选 `--log` 参数输出完整 `LogEntry` 序列（JSON lines 格式）。

---

## 8) 验收标准（v0.1）

* DSL 解析 + 编译派生：

  * 对任意 Sudoku 输入，生成 PairConstraints 覆盖所有 peers 且无重复。
  * **派生数量硬断言**：去重后的 neq 数量必须恰好为 **810**（= 81 × 20 / 2，每个 cell 有 20 个 peer，无序对去重）。若不等于 810 则编译器存在 bug，直接 abort。
  * **givens 静态冲突检测**：若两个属于同一 unit 的 givens 变量被赋了相同值，编译期直接报错（`GIVEN_CONFLICT: Cell[r1,c1]=d == Cell[r2,c2]=d in Unit U`），不进入传播阶段。
* 求解：

  * 能解标准数独题（传播+搜索）。
  * 对矛盾输入能检测 `Contradiction` 并给出矛盾点（域空的 cell 或 unit 中缺失的 digit）。
* 日志：

  * 能复盘每一步删值/定值来源。

### 8.1) 参考测试用例

| ID | 输入（81 字符串） | 类型 | 预期结果 |
|----|----------------|------|---------|
| T1 | `53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79` | Easy（纯传播可解） | 唯一解，`Stats.guesses == 0` |
| T2 | `..9748...7.........2.1.9.....7...24..64.1.59..98...3.....8.3.2.........6...2759..` | Medium（需搜索） | 唯一解，`Stats.guesses > 0` |
| T3 | `53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..71` | 矛盾（最后一位篡改为 1→与同列已有 1 冲突→无解） | `GIVEN_CONFLICT`：Cell[5,9]=1 与 Cell[9,9]=1 同属 Col 9（编译期静态检测即捕获；若绕过静态检测则传播阶段报 `Contradiction`） |
| T4 | `11.......................................................................` | Givens 冲突 | `GIVEN_CONFLICT`：Cell[1,1]=1 与 Cell[1,2]=1 同属 Row 1（1-based 输出） |

---

# 9) 规则与论文术语对照表（你要的映射）

> 说明：这里把 v0.1 的“硬约束 Sudoku 实现”映射回你论文的纤维化/富集术语。
> v0.1 实际上是你框架在 **(i) 两层链结构**、**(ii) Boolean 可行性值域**、**(iii) 选定标准构造（路线 A）** 下的一个可执行特化。
>
> **v0.1 中"纤维化"体现在哪里**：主要是**作用域细化**（Unit 层 9 元 all-different → Pair 层 2 元 neq 的派生构造）与**传播闭包 $\mathrm{cl}$ 的分层计算结构**（Pair 层 AC + Unit 层 Hidden Single 交替迭代至不动点）。真正的"层间推前 $f_!$ 非幺半（涌现）"需要 v0.2 引入非 Boolean 的富集值域——v0.1 中 $\delta=0$，不可能观测到涌现效应。

| 工程/DSL 元素                   | v0.1 中的含义（Sudoku）           | 论文术语对应（概念层）                          | 备注（为何对应）                                  |
| --------------------------- | --------------------------- | ------------------------------------ | ----------------------------------------- |
| `levels: Pair < Unit`       | 两层链：二元约束层、9元 unit 约束层       | 层级范畴 (\mathcal L)（链/偏序）              | (\mathcal L) 取最简单的链，方便单趟/队列不动点            |
| `Digit={1..9}`              | 值域                          | 纤维值域对象族 (V_l)（富集结构的特化）               | v0.1 取 Boolean 可行性：域是“可能值集合”              |
| `Cell[r,c]`                 | 变量集合 X 中元素                  | 变量对象/索引对象（CSP 的变量集合）                 | 变量集仍是经典 CSP 的集合层                          |
| `Row/Col/Box` scopes        | 作用域 (S\subseteq X)          | 作用域族 + 层级指派 (\Sigma(S))              | v0.1 固定 (\Sigma(\text{unit})=\text{Unit}) |
| `all_different(U)` (Unit 层) | 行/列/宫约束                     | 粗层约束 (\varphi_S \in V_{\Sigma(S)})   | 这是 coarse constraint 的原始输入                |
| `derive.down: pairwise_neq` | 编译期派生 $\binom{9}{2}=36$ 个 neq/unit（全局去重后 810 条） | 路线 A 的派生式构造：将粗层 `all_different` 的逻辑蕴含展开为细层二元约束族。在 Boolean 纤维下 $f^* : \mathbf{2} \to \mathbf{2}$ 为恒等映射（拉回平凡），非平凡性在于**约束的作用域细化**（9 元→2 元） | 通过构造保证层间一致性（避免手工验证 lax）                   |
| 派生后的 `neq(x,y)`（Pair 层）     | 约束图边                        | 细层约束族（更细的作用域/更细层）                    | 相当于 coarse 约束在细层的“影子/展开”                  |
| Pair 层传播（若一端单点则删对端）         | neq 弧一致性（对 neq 等价于完整 AC，见 §4.1） | FAC 在细层上的局部一致性推理（(\mathrm{cl}) 的一部分）  | 是"坍缩/闭包"算子在细层的可执行实现                       |
| Unit 层 Hidden Single        | unit 约束推导出的确定性赋值            | 粗层约束 $\varphi_U$（`all_different`）在域收缩后的局部一致性推理——检测"$\varphi_U$ 要求每个 digit 至少出现一次，当候选位置唯一时推导出确定赋值"。结果通过 ASSIGN 的 neq 传播向 Pair 层传播，对应 $\mathrm{cl}$ 中"粗→细"方向 | 由 ELIMINATE 内 `Count[U][d]==1` 触发；**不是** $f_!$（推前/涌现）方向；v0.1 中 $f_!$ 幺半（Boolean 退化），无涌现效应 |
| 传播到不动点                      | 推理收敛                        | 闭包/坍缩算子 (\mathrm{cl}) 的不动点计算         | 这里的 (\mathrm{cl}) 由传播循环隐式实现               |
| `local_patch`               | 细层额外补丁                      | (\varphi^{local})（局部修补项）             | v0.1 强约束：不得破坏派生一致性                        |
| MRV 回溯搜索                    | 分支枚举                        | “传播/消元 + 搜索”的搜索部分                    | 与论文强调的三步法对齐：传播后再搜索                        |
| 日志 reason（PAIR/UNIT）        | 可解释诊断                       | "坍缩路径"的证据链                            | v0.1 全为坍缩传播；涌现路径需 v0.2 引入软代价后方有实质        |

> **关于 $f_!$（涌现）在 v0.1 中的缺位**。v0.1 的 Boolean 两层链中，$V_{\text{Pair}} = V_{\text{Unit}} = \mathbf{2}$（可行/不可行），$f^*$ 和 $f_!$ 均为恒等映射——$f_!$ 自动幺半，偏差 $\delta = 0$。因此 v0.1 **不存在涌现现象**：所有传播都是坍缩方向（粗→细，$f^*/\mathrm{cl}$）。涌现效应需在 v0.2 引入非 Boolean 富集值域（如 Unit 层使用代价语义 $[0,\infty]^{op}$、Pair 层使用概率语义 $[0,1]$）后，由 $f^*$ 的 oplax 幺半性导出非幺半 $f_!$，方能实质出现。

---

## 10) v0.2/v1.0 的自然升级方向（不改接口）

* **v0.1.5（仍为硬约束，验证 Unit 层传播强度）**：在 Pair 层 neq AC 基础上，添加 **Naked Pair / Naked Triple** 检测——仍是硬可行性推理，但利用了 unit 内部的组合结构。这一步不改变值域语义（仍是 Boolean），但能显著减少搜索节点数，同时为度量"Unit 层传播强度 vs 搜索工作量"提供最小对比实验。实现提示：对每个 unit，当某 $k$ 个 cell 的域并集恰好为 $k$ 个 digit 时，从 unit 内其余 cell 删去这些 digit。
* 把 Unit 层传播升级为 GAC(all-different)（Régin），更接近"真正 FAC"。
* 引入富集值域（软代价/半环）：

  * Pair 层可仍硬；Unit 层可软（启发式/代价），用于排序与剪枝解释。
  * 此时 (f_!) 不再幺半，(\delta > 0)，涌现效应首次出现——可对比 §8 映射表中的"涌现缺位"说明。
* 让 (\Sigma) 可配置甚至可推断（更一般 CSP 场景）。
* 把“派生 = 固定 (f^*)”升级为“可选 (f^*) 家族 + 自动生成 (f_!)”的更一般框架实现。

---
