"""LABS-1.063: prove that src/ changed only in docstrings and comments since a base commit.

    uv run python -I probes/src_semantics_unchanged.py [BASE]     (default BASE: main)

Every Python module under src/ is parsed at BASE and in the working tree. Docstrings (the first string expression of a
module, class or function) are removed, and the abstract syntax trees are compared: comments never reach the tree.
Exit 0 when every module's executable code is identical. A module only on one side is a failure. Schema (.tql) files
must be byte-identical.
"""

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = sys.argv[1] if len(sys.argv) > 1 else "main"


def strip(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant) \
                    and isinstance(first.value.value, str):
                node.body = node.body[1:] or [ast.Pass()]
    return ast.dump(tree, include_attributes=False)


def at_base(path):
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"{BASE}:{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def tracked(prefix, suffix):
    out = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", BASE, prefix], capture_output=True,
                         text=True).stdout.split()
    here = [str(p.relative_to(ROOT)) for p in (ROOT / prefix).rglob(f"*{suffix}")]
    return sorted({p for p in out + here if p.endswith(suffix)})


bad, changed_docs = [], []
for path in tracked("src", ".py"):
    old, new_file = at_base(path), ROOT / path
    if old is None or not new_file.exists():
        bad.append(f"{path}: only on one side")
        continue
    new = new_file.read_text()
    if old == new:
        continue
    if strip(ast.parse(old)) != strip(ast.parse(new)):
        bad.append(f"{path}: executable code differs")
    else:
        changed_docs.append(path)
for path in tracked("schema", ".tql"):
    old, new_file = at_base(path), ROOT / path
    if old is None or not new_file.exists() or old != new_file.read_text():
        bad.append(f"{path}: schema differs")
print(f"base {BASE}: modules with docstring/comment-only changes: {changed_docs or 'none'}")
print(f"executable or schema differences: {bad or 'none'}")
sys.exit(1 if bad else 0)
