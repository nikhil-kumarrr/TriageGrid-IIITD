# Contributing to TriageGrid 🏥

Thank you for your interest in contributing to **TriageGrid**! This document provides guidelines and instructions for contributing to this project.

---

## 📋 Code of Conduct

We are committed to providing a welcoming, inclusive, and harassment-free environment for everyone. Please be respectful and constructive in all interactions.

---

## 🛠️ Development Setup

### Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher (npm 9+)
- **Git**

### Local Clone & Branching
```bash
git clone https://github.com/nikhil-kumarrr/TriageGrid-IIITD.git
cd TriageGrid-IIITD
git checkout -b feature/your-feature-name
```

### Backend Setup
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r backend/requirements-dev.txt
```

### Frontend Setup
```bash
cd frontend
npm install
cd ..
```

---

## 🧪 Testing & Verification

Before submitting any Pull Request, ensure all tests pass:

```bash
# 1. Backend tests
PYTHONPATH=backend pytest backend/tests -v

# 2. Frontend type-check & production build
npm --prefix frontend run build
```

---

## 📝 Commit Convention

We follow conventional commits format:
- `feat: <description>` for new features
- `fix: <description>` for bug fixes
- `docs: <description>` for documentation updates
- `refactor: <description>` for code refactoring
- `test: <description>` for adding or updating tests

---

## 🚀 Submitting a Pull Request

1. Fork the repository and create your branch from `main`.
2. Ensure existing tests pass and add new tests where applicable.
3. Commit your changes with clear, descriptive commit messages.
4. Push to your fork and submit a Pull Request to `main`.
5. Provide a clear summary of changes in the PR description.
