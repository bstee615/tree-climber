# Python Support Plan (2026-10-12)

Status: sketch only. No Python-support code has been written. Work is tracked as GitHub issues under the epic linked at the bottom.

## Baseline (measured 2026-10-12, before any Python work)

- Build: `uv sync --dev` succeeds once `graphviz` and `graphviz-dev` are installed (needed to compile `pygraphviz`). Frontend `bun install` and `bunx vite build` succeed.
- Tests: `uv run pytest` reports 75 passed but 2 collection errors in `test/dfg/` (stale `UseDefSolver` import from `def_use`, and `from test.dfg...` import that does not resolve). With the first import fixed in a scratch copy, 36 of 42 DFG tests still fail, so that suite has drifted from the implementation.
- `src/tree_climber/viz/test_api.py` is outside `testpaths` and needs a live server on port 8001; it fails when run directly.
- CLI smoke test: `tree-climber` produces CFG and CPG PNGs for C and Java.
- CI checks currently failing on main: `ruff check` (55 findings), `pyright` (22 errors), frontend `tsc -b` (2 errors in `Graph.tsx`). `ruff format --check` passes.
- Bug found while scoping: `CFGVisitor._passthrough_entry_exit_nodes` removes every node whose text contains the substring "else". In C, `int elsewhere = a;` is deleted from the CFG. Python's `a if b else c` and `for/while ... else` make this a hard prerequisite.

## Starting point

- `tree-sitter-languages` 1.10.2 already bundles the Python grammar; no new dependency is needed.
- Languages are registered by hand in several places: `cfg/builder.py:get_visitor`, `cli/visualizers/constants.py`, `cli/source.py`, `viz/app.py`, `viz/frontend/src/LanguageSelector.tsx`, and a hardcoded `CFGBuilder("java")` in `dataflow/main.py`. The Monaco editor already receives the language id directly, and `python` is a valid Monaco id.
- New visitors subclass `CFGVisitor` and implement `get_calls`, `get_definitions`, `get_uses` plus `visit_<node_type>` handlers (see `languages/c.py`, `languages/java.py`).

## Design decisions

1. Scope of the first milestone is intraprocedural CFG plus def-use/reaching-definitions on a single module, matching C and Java after commit 77acb86.
2. A module is modeled like a Java class body or C translation unit: top-level statements form an implicit entry-to-exit flow, and each `def` gets its own ENTRY/EXIT pair.
3. Python loops have `else` clauses that run when the loop ends without `break`. This needs a dedicated edge from the loop header's false branch to the `else` block, with `break` bypassing it.
4. `try/except/else/finally`, `with`, and `match` need new handling and should reuse `NodeType` values where possible. Add new `NodeType` members only if the visualizer needs to distinguish them.
5. Def/use for Python is name-based: assignment targets (including tuple/star unpacking, annotated assignment, augmented assignment, walrus, `for` targets, `with ... as`, `except ... as`, imports, `del`) define; `global`/`nonlocal` change which scope a name belongs to.
6. Out of scope for the first milestone: interprocedural dataflow, aliasing, decorators' runtime effects, dynamic features (`exec`, `eval`, `setattr`), and type narrowing.

## Issue breakdown

See the epic for the live list and ordering. Prerequisites (baseline health, the "else" bug, language registry) come before visitor work. Visitor work is split by construct family so each issue can ship with its own fixtures and tests under `test/python_cfg/`.

## Results

To be filled in when the work is done.
