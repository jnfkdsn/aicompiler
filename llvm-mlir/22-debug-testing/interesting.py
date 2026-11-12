#!/usr/bin/env python3
"""mlir-reduce convention: 1 is interesting, 0 is not. Never accept any failure."""
from pathlib import Path
import subprocess
import sys
WORKSPACE=Path(__file__).resolve().parents[3]
TOOL=WORKSPACE/'artifacts/builds/mlir-debug-testing/my-opt'
try:
    r=subprocess.run([str(TOOL),sys.argv[1],'--my-reject-marked-mul'],capture_output=True,text=True,timeout=10)
except (OSError,subprocess.TimeoutExpired):
    raise SystemExit(0)
# Parsing/verifying precedes the pass. Syntax errors and unrelated diagnostics
# do not reproduce the same teaching restriction.
raise SystemExit(1 if r.returncode==1 and 'teaching restriction: marked multiply is unsupported' in r.stderr else 0)
