# Fibered-CSP 项目

基于纤维化富集范畴（Fibered Enriched Category）理论框架的约束满足问题（CSP）研究与实现。

## 目录结构

```
.                                        # fibered_csp/ — 项目根目录（同时也是 Python 包）
├── README.md
├── __init__.py
├── sudoku/                              # Sudoku 9×9 求解器（v0.1 参考实现）
│   ├── docs/
│   │   └── sudoku-spec-0v1.md           # 工程规格文档（路线 A 派生式构造 + FAC 传播 + 搜索）
│   ├── compiler.py                      # 编译模块：固定生成 27 units / Peers / CellsOf / UnitsOf / 810 neq 断言
│   ├── parser.py                        # 输入解析：81 字符串 → givens，含格式校验与静态冲突检测
│   ├── solver.py                        # 传播引擎：ASSIGN/ELIMINATE 互递归 + bitmask 域 + trail 回溯 + MRV 搜索
│   ├── main.py                          # CLI 入口（--log / --count）
│   ├── test_solver.py                   # pytest 测试套件（16 cases：编译 / 解析 / 求解 / 传播属性）
│   ├── __init__.py
│   └── __main__.py
└── thoughts/                            # 理论笔记与论文
    ├── 纤维化富集范畴视角下的CSP.md           # 核心论文：Grothendieck 双纤维化 CSP 框架
    ├── 传统 CSP 解法的纤维化重新理解.md       # 传统 CSP 算法的纤维化重新诠释
    ├── 纤维化CSP下的扩散模型理解.md           # 纤维化 CSP 与扩散模型的关联
    └── 从约束出发的扩散模型.md                # 从约束视角理解扩散模型
```

## 快速使用

```bash
# 求解数独
python3 -m sudoku '53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79'

# 带日志输出
python3 -m sudoku --log <puzzle>

# 枚举所有解（验证唯一性）
python3 -m sudoku --count <puzzle>

# 从 stdin 读取
echo "<puzzle>" | python3 -m sudoku -

# 运行测试
python3 -m pytest sudoku/test_solver.py -v
```

## 技术概要

求解器是论文框架在 **两层链（Pair < Unit）+ Boolean 可行性值域 + 路线 A 派生式构造** 下的可执行特化：

- **编译期**：Unit 层 `all_different` 自动派生为 Pair 层 `neq`（去重 810 条）
- **传播**：ASSIGN/ELIMINATE 互递归至不动点（Pair 层 neq AC + Unit 层 Hidden Single + Naked Single）
- **搜索**：MRV 启发式 + trail 回溯

依赖：Python 3.10+、pytest（仅测试）。
