# Contributing to VisionAI

Thank you for considering contributing to VisionAI! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/visionai-databricks.git
   cd visionai-databricks
   ```
3. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📝 Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Description |
|--------|-------------|
| `feat:` | A new feature |
| `fix:` | A bug fix |
| `docs:` | Documentation changes |
| `style:` | Code formatting (no logic change) |
| `refactor:` | Code restructuring |
| `test:` | Adding or updating tests |
| `perf:` | Performance improvements |
| `chore:` | Build process or tooling changes |

**Example:**
```bash
git commit -m "feat: add emotion detection endpoint"
git commit -m "fix: resolve timezone offset in detection timestamp"
```

## 🔀 Pull Request Process

1. Ensure your code passes all tests: `pytest tests/ -v`
2. Update documentation if you changed any APIs or features
3. Open a Pull Request with a clear title and description
4. Link any related issues in the PR description

## 🧪 Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
PYTHONPATH=. pytest tests/ -v
```

## 📐 Code Style

- Follow PEP 8 for Python code
- Use type hints where applicable
- Add docstrings to all public functions
- Keep functions focused and under 50 lines when possible

## 🐛 Reporting Bugs

Open an issue with:
- A clear and descriptive title
- Steps to reproduce the behavior
- Expected behavior vs actual behavior
- Screenshots if applicable
- Environment details (OS, Python version, browser)

## 💡 Feature Requests

Open an issue with:
- A clear description of the feature
- The motivation / use case
- Any alternatives you've considered

---

Thank you for helping make VisionAI better! 🎉
