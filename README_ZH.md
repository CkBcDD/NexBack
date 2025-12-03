# NexBack

NexBack 是一款基于科学验证的 **Dual N-Back** 认知训练范式构建的现代化桌面应用程序。旨在帮助用户提升工作记忆（Working Memory）和流体智力（Fluid Intelligence）。

本项目深受经典的 [Brain Workshop](http://brainworkshop.sourceforge.net/) 启发，致力于使用现代技术栈（Python 3.13+, PySide6）重构并扩展这一经典的训练工具，提供更流畅的用户体验和更强的扩展性。

> Note: This README is the Chinese translation of [README.md](README.md).

## ✨ 核心特性

当前版本（MVP）包含以下功能：

- **Dual N-Back 训练**：同时追踪空间位置（3x3 网格）和听觉信号（字母朗读）。
- **可配置难度**：默认 N=2，支持自定义 N-Back 级别。
- **实时反馈系统**：
  - 清晰的视觉指示（正确、错误）。
  - 实时统计 Hit（命中）、Miss（漏选）、False Alarm（误报）。
- **评分与统计**：分别追踪视觉和听觉模态的表现。

未来计划：

- 多种训练模式（Single, Triple, Arithmetic 等）。
- 自适应难度调节（根据表现自动升降级）。
- 详细的历史数据统计与图表展示。
- 临床实验模式支持。

## 🛠️ 安装指南

本项目推荐使用 **[uv](https://github.com/astral-sh/uv)** 进行依赖管理和环境配置，以获得最佳的开发体验。

### 前置要求

- Python 3.13+

### 使用 uv 安装（推荐）

1. 克隆仓库：

   ```bash
   git clone https://github.com/CkBcDD/NexBack.git
   cd NexBack
   ```

2. 使用 `uv` 同步依赖并运行：

   ```bash
   uv sync
   uv run main.py
   ```

### 使用 pip 安装（传统方式）

1. 克隆仓库：

   ```bash
   git clone https://github.com/CkBcDD/NexBack.git
   cd NexBack
   ```

2. 创建并激活虚拟环境（可选但推荐）。

    ```bash
    python -m venv .venv
    # or in MacOS / Linux
    python3 -m venv .venv
    ```

3. 安装依赖：

   ```bash
   pip install .
   # 或者手动安装
   pip install PySide6
   ```

## 🚀 快速开始

运行以下命令启动应用程序：

```bash
# 如果使用 uv (推荐)
uv run main.py

# 如果使用标准 python
python main.py
```

## 🎮 操作说明

在训练会话中：

- **开始会话**：点击主界面上的 "Start Session" 按钮。
- **位置匹配 (Position Match)**：
  - 当**当前方块位置**与 **N 回合前**的位置相同时，按下键盘 **`A`** 键。
- **声音匹配 (Audio Match)**：
  - 当**当前朗读字母**与 **N 回合前**的字母相同时，按下键盘 **`L`** 键。

## 💻 开发指南

### 项目结构

```bash
NexBack/
├── main.py                 # 应用程序入口
├── pyproject.toml          # 项目配置与依赖 (uv/pip)
├── resources/              # 静态资源 (音频等)
├── scripts/                # 辅助脚本 (如音频生成)
└── src/
    └── nexback/
        ├── core/           # 核心逻辑 (引擎, 音频, 存储)
        ├── ui/             # 用户界面 (PySide6)
        └── utils/          # 工具函数
```

### 开发规范

- **包管理**：请优先使用 `uv add`, `uv run` 等命令管理依赖。
- **代码风格**：保持代码简洁、模块化，并添加清晰的注释。
- **进度记录**：重大更改请更新 `TODO/PROGRESS.md`。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！无论是修复 Bug、改进文档还是添加新功能，我们都非常感谢您的贡献。

## 📄 许可证

[MIT License](LICENSE)
