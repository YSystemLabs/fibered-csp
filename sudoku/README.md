# Fibered-CSP Sudoku

基于纤维化 CSP 框架实现的 9×9 数独求解器。这个子工程把论文中的两层链结构具体化为一个可执行求解器：

- Unit 层：`all_different` 约束。
- Pair 层：由 Unit 层自动派生出的 `neq` 二元约束。
- 求解流程：静态冲突检测 + 传播到不动点 + MRV 搜索 + trail 回溯。

## 目录结构

```text
sudoku/
├── README.md
├── docs/
│   └── sudoku-spec-0v1.md               # 工程规格文档
├── compiler.py                          # 编译 27 个 units、peers、units_of 与 neq 关系
├── parser.py                            # 解析 81 字符输入并检查 givens
├── solver.py                            # 传播引擎、搜索与回溯
├── main.py                              # CLI 入口
├── test_solver.py                       # pytest 测试
├── __init__.py
└── __main__.py
```

## 环境要求

- Python 3.10+
- `pytest`，仅在运行测试时需要

这个子工程没有额外第三方运行时依赖。

## 快速开始

在仓库根目录执行：

```bash
python3 -m sudoku '53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79'
```

输出包括：

- 一行 81 字符解串。
- 9×9 网格形式的解。
- 求解统计信息，例如 guesses、backtracks、最大搜索深度等。

## 输入格式

求解器接受一个长度为 81 的字符串：

- `1` 到 `9` 表示已知数。
- `.` 或 `0` 表示空格。
- `-` 表示从标准输入读取。

示例：

```bash
python3 -m sudoku '53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79'

echo '53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79' | python3 -m sudoku -
```

## CLI 用法

### 普通求解

```bash
python3 -m sudoku <puzzle>
```

### 输出日志

```bash
python3 -m sudoku --log <puzzle>
```

`--log` 会在统计信息后输出 JSON 行日志，包含：

- `step_id`
- `depth`
- `reason`
- `cell`
- `digit`
- `evidence`

适合调试传播链条和搜索过程。

### 枚举所有解

```bash
python3 -m sudoku --count <puzzle>
```

`--count` 会枚举全部解，并输出：

- 解的总数。
- 第一组解字符串。

这个模式主要用于验证唯一性，而不是高性能枚举。

## 失败场景

程序在以下情况下会返回失败并输出错误信息到标准错误：

- 输入长度不是 81。
- 输入包含非法字符。
- givens 在同一行、列或宫内发生静态冲突。
- 传播或搜索中检测到不可满足矛盾。

## 实现概要

### 1. 编译阶段

`compiler.py` 固定生成数独结构：

- 27 个 unit。
- 每个格子的 peers 集合。
- 每个格子所属的 3 个 units。
- 由 `all_different` 派生出的去重 `neq` 约束，共 810 条。

### 2. 解析与校验

`parser.py` 负责：

- 将 81 字符输入解析为 givens。
- 检查格式是否合法。
- 在求解前执行 givens 静态冲突检测。

### 3. 传播

`solver.py` 使用 `ASSIGN/ELIMINATE` 互递归推进到不动点，包含：

- Pair 层 `neq` 传播。
- Unit 层 Hidden Single。
- Naked Single 收缩。

### 4. 搜索

传播不能直接完成时，求解器会：

- 使用 MRV 选择分支变量。
- 记录 trail。
- 在失败时执行精确回溯恢复。

## 测试

在仓库根目录执行：

```bash
python3 -m pytest sudoku/test_solver.py -v
```

测试覆盖：

- 编译产物规模与结构。
- 输入解析和非法输入处理。
- givens 冲突检测。
- Easy / Medium / Contradiction 等参考案例。
- 解的有效性。
- trail 回溯恢复正确性。

## 相关文档

- 规格文档：`docs/sudoku-spec-0v1.md`
- 仓库总览：`../README.md`

如果你想看这个求解器如何对应论文中的层级、纤维和值域语义，优先阅读 `docs/sudoku-spec-0v1.md`。
