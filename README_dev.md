# 🚀 Publishing `agentdatashuttle_adspy` to PyPI with `pyproject.toml`

This guide shows how to convert your legacy `setup.py` into the modern `pyproject.toml` and publish your SDK to PyPI.

---

## 📁 Project Structure

```
python-sdk/
├── agentdatashuttle_adspy/  # your SDK code
│   └── __init__.py
├── README.md                # shown on PyPI
├── LICENSE                  # Apache-2.0
├── pyproject.toml           # 📦 modern build config
```

---

## 📝 `pyproject.toml`

Create a `pyproject.toml` file at the root:

```toml
[project]
name = "agentdatashuttle_adspy"
version = "1.0.0"
description = "Agent Data Shuttle - Python SDK"
authors = [
  { name="Knowyours", email="agentdatashuttle@knowyours.co" }
]
license = { text = "Apache-2.0" }
readme = "README.md"
requires-python = ">=3.7"
dependencies = [
    'langchain',
    'langchain-core',
    'langchain-community',
    'langgraph',
    'langgraph-prebuilt',
    'python-dotenv',
    'requests',
    'pydantic',
    'pika',
    'python-socketio[client]',
    'markdown',
    'yagmail',
    'slackify-markdown',
    'slack-sdk'
]

[project.urls]
Homepage = "https://agentdatashuttle.knowyours.co"
Repository = "https://github.com/agentdatashuttle/python-sdk"
Issues = "https://github.com/agentdatashuttle/python-sdk/issues"

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]
```

---

## 🛠️ Build the Package

In a `venv`, first, install the tools:

```bash
pip install build
```

Then build the distribution:

```bash
python -m build
```

Output will be in the `dist/` folder:

```
dist/
  agentdatashuttle_adspy-1.0.0.tar.gz
  agentdatashuttle_adspy-1.0.0-py3-none-any.whl
```

---

## 🚀 Publish to PyPI

Install `twine` if you haven't:

```bash
pip install twine
```

Then upload:

```bash
twine upload dist/*
```

If you don’t have an account, [create one here](https://pypi.org/account/register/).

---

## 🧪 Optional: Test on TestPyPI

```bash
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ agentdatashuttle_adspy
```

---

## ✅ Consumers will use:

```bash
pip install agentdatashuttle_adspy
```

```python
from ads import ADSClient

client = ADSClient()
```
