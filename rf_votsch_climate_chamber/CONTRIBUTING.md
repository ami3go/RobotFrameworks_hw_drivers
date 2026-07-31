# Contributing

1. Create a feature branch.
2. Install `python -m pip install -e ".[dev]"`.
3. Add tests for behavior changes.
4. Run `ruff check .`, `pytest`, Robot acceptance tests, Libdoc, and package build.
5. Do not run hardware-changing tests without operator approval.
6. Document protocol assumptions and chamber model/firmware used for validation.

Keep the Python package at repository root; do not introduce a `src/` layout.
