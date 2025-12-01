# NexBack

NexBack is a modern desktop application built on the science-backed Dual N-Back cognitive training paradigm. It's designed to help users improve Working Memory and Fluid Intelligence.

This project is inspired by the classic Brain Workshop (<http://brainworkshop.sourceforge.net/>) and aims to re-implement and extend that classic training tool using a modern tech stack (Python 3.13+, PyQt6) to provide a smoother user experience and better extensibility.

> 注：本README文件以英文撰写。中文译本请参见[README_ZH.md](README_ZH.md)。

## ✨ Core Features

The current version includes the following features:

- **Dual N-Back training**: Tracks both spatial positions (3x3 grid) and auditory stimuli (spoken letters).
- **Configurable difficulty**: Default is N=2, with support for custom N-back levels.
- **Real-time feedback system**:
  - Clear visual indicators for correct and incorrect.
  - Real-time statistics for Hits, Misses, and False Alarms.
- **Scoring and statistics**: Tracks performance separately for visual and auditory modalities.

Planned features (from the roadmap):

- Multiple training modes (Single, Triple, Arithmetic, etc.)
- Adaptive difficulty adjustment (automatically raise or lower N based on performance)
- Detailed history statistics and charts
- Support for clinical experiment mode

## 🛠️ Installation

This project recommends using [uv](https://github.com/astral-sh/uv) for dependency management and environment setup to achieve the best development experience.

### Prerequisites

- Python 3.13+

### Install with uv (recommended)

1. Clone the repo:

    ```bash
    git clone https://github.com/CkBcDD/NexBack.git
    cd NexBack
    ```

2. Sync dependencies and run:

    ```bash
    uv sync
    uv run main.py
    ```

### Install with pip (traditional)

1. Clone the repo:

    ```bash
    git clone https://github.com/CkBcDD/NexBack.git
    cd NexBack
    ```

2. Create and activate a virtual environment (optional but recommended).

    ```bash
    python -m venv .venv
    # or in MacOS / Linux
    python3 -m venv .venv
    ```

3. Install dependencies:

    ```bash
    pip install .
    # or install manually
    pip install PyQt6
    ```

## 🚀 Quick Start

Run the application with:

```bash
# If you're using uv (recommended)
uv run main.py

# Or using standard python
python main.py
```

## 🎮 How to Use

During a training session:

- **Start a session**: Click the "Start Session" button on the main screen.
- **Position match**:
  - Press the `A` key when the current square position matches the position N steps back.
- **Audio match**:
  - Press the `L` key when the current spoken letter matches the letter N steps back.

## 💻 Development

### Project structure

```bash
NexBack/
├── main.py                 # Entry point
├── pyproject.toml          # Project config and dependencies (uv/pip)
├── resources/              # Static resources (audio, etc.)
├── scripts/                # Utility scripts (e.g., audio generation)
└── src/
    └── nexback/
        ├── core/           # Core logic (engine, audio, storage)
        ├── ui/             # UI (PyQt6)
        └── utils/          # Utility functions
```

### Development guidelines

- **Package manager**: Prefer `uv add`, `uv run`, and related commands for dependency management.
- **Code style**: Keep code simple and modular, and include clear comments.
- **Progress**: Update `TODO/PROGRESS.md` for major changes.

## 🤝 Contributing

Issues and Pull Requests are very welcome! Whether you fix a bug, improve the docs, or add a new feature, we appreciate your contribution.

## 📄 License

[MIT License](LICENSE)
