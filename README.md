# Fibered-CSP 项目

基于纤维化富集范畴（Fibered Enriched Category）理论框架的约束满足问题研究与实现。

当前仓库主要包含两个可运行子工程和一组理论笔记：

- `sudoku/`：9×9 数独求解器，验证论文框架在离散布尔约束问题上的可执行特化。
- `image_gen/`：图像生成与相图扫描实验系统，研究像素层偏好、区域层代价和对称性硬约束之间的耦合行为。
- `thoughts/` 目录保存纤维化 CSP 的理论笔记、框架说明与相关推导草稿，用于支撑两个子工程的设计。

## 仓库结构

```text
.                                        # fibered-csp/ — 仓库根目录
├── README.md
├── __init__.py
├── sudoku/                              # 数独求解器与测试
│   ├── README.md
│   ├── docs/
│   ├── compiler.py
│   ├── parser.py
│   ├── solver.py
│   ├── main.py
│   ├── test_solver.py
│   ├── __init__.py
│   └── __main__.py
├── image_gen/                           # 图像生成 Web 应用 + 实验流水线
│   ├── README.md
│   ├── requirements.txt
│   ├── server.py
│   ├── docs/
│   ├── engine/
│   ├── experiments/
│   ├── static/
│   └── tests/
└── thoughts/                            # 理论笔记与论文草稿
```

## 子工程入口

### Sudoku

9×9 数独求解与唯一性验证。

- 文档：`sudoku/README.md`
- 规格：`sudoku/docs/sudoku-spec-0v1.md`

### Image Generator

图像生成、参数扫描与实验报告流水线。

- 文档：`image_gen/README.md`
- 规格：`image_gen/docs/image-gen-spec-0v1.md`

具体使用说明、安装方法、运行命令和测试入口均放在各自子工程的 README 中。

## 依赖

- Python 3.10+
- 具体依赖请查看各子工程 README 与依赖文件
