# Contributing to AI Context Compression

Welcome! We're excited you're interested in contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/ai-context-compression.git`
3. Create a feature branch: `git checkout -b feature/your-feature`
4. Make changes and add tests
5. Run tests: `pytest tests/ -v --cov=src`
6. Push to your fork and submit a PR

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/

# Formatting
black src/ tests/
flake8 src/ tests/
```

## Code Standards

- **Tests:** 80%+ coverage required
- **Types:** Full type hints required
- **Docs:** Docstrings for all public functions
- **Commits:** Conventional commit messages

## Pull Request Process

1. Ensure all tests pass
2. Ensure coverage hasn't decreased
3. Update documentation if needed
4. Get at least one review approval

## Questions?

Open an issue for discussion.
