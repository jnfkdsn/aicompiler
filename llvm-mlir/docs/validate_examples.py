#!/usr/bin/env python3
"""Validate complete MLIR modules embedded in the blog, without executing them."""

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


EXAMPLE = re.compile(
    r"<!-- mlir-(example|invalid): ([^\n]*?) -->\s*```text\n(.*?)\n```", re.S
)


def main():
    workspace = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mlir-opt", type=Path,
                        default=workspace / "artifacts/builds/mlir-20.1.8/bin/mlir-opt")
    parser.add_argument("--docs", type=Path,
                        default=workspace / "blog/docs/notes/compile/mlir")
    parser.add_argument("--output", type=Path,
                        default=workspace / "artifacts/logs/mlir-docs" /
                        datetime.now().strftime("%Y-%m-%d-reorganized"))
    args = parser.parse_args()
    opt, docs, output = (p.resolve() for p in (args.mlir_opt, args.docs, args.output))
    if not opt.is_file() or not docs.is_dir():
        parser.error("mlir-opt or documentation directory does not exist")
    output.mkdir(parents=True, exist_ok=True)
    version = subprocess.run([str(opt), "--version"], capture_output=True,
                             text=True, check=True, timeout=20).stdout.strip()
    entries, seen, failures = [], set(), []
    texts = {}
    for page in sorted(docs.rglob("*.md")):
        content = page.read_text()
        for match in EXAMPLE.finditer(content):
            kind, specification, code = match.groups()
            parts = specification.split("|", 1)
            name = parts[0].strip()
            expected_diagnostic = parts[1].strip() if len(parts) == 2 else None
            if not re.fullmatch(r"[a-z0-9-]+", name) or name in seen:
                parser.error(f"invalid or duplicate example ID: {name}")
            if kind == "invalid" and not expected_diagnostic:
                parser.error(f"missing diagnostic substring: {name}")
            seen.add(name)
            texts[name] = code
            directory = output / name
            directory.mkdir(exist_ok=True)
            source = directory / "input.mlir"
            source.write_text(code + "\n")
            record = {
                "id": name, "page": str(page.relative_to(docs)),
                "line": content[:match.start()].count("\n") + 1,
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "expect": kind, "expected_diagnostic": expected_diagnostic,
                "checks": [],
            }

            def run(label, input_file, flags=(), reject=False, diagnostic=None):
                command = [str(opt), str(input_file), *flags]
                try:
                    result = subprocess.run(command, text=True, capture_output=True,
                                            timeout=20)
                    stdout, stderr, returncode = result.stdout, result.stderr, result.returncode
                    # A signal/crash is not an expected parser/verifier rejection.
                    ok = (returncode > 0 and diagnostic in stderr) if reject else returncode == 0
                except subprocess.TimeoutExpired:
                    stdout, stderr, returncode, ok = "", "Command timed out", None, False
                result_path = directory / f"{label}.mlir"
                result_path.write_text(stdout)
                (directory / f"{label}.stderr.txt").write_text(stderr)
                record["checks"].append({"name": label, "command": command,
                                         "returncode": returncode, "passed": ok})
                if not ok:
                    failures.append(f"{name}: {label}: {stderr.strip()}")
                return result_path, ok

            if kind == "invalid":
                run("expected-error", source, reject=True, diagnostic=expected_diagnostic)
            else:
                _, parsed = run("parse-verify", source)
                if parsed:
                    generic, printed = run("generic", source, ["--mlir-print-op-generic"])
                    if printed:
                        run("generic-reparse", generic)
                    if re.search(r"\bscf\.", code):
                        lowered, lowered_ok = run("scf-to-cf", source, ["--convert-scf-to-cf"])
                        if lowered_ok:
                            run("cf-reparse", lowered)
                            no_scf = not re.search(r"\bscf\.", lowered.read_text())
                            record["checks"].append({"name": "no-scf-after-lowering",
                                                     "passed": no_scf})
                            if not no_scf:
                                failures.append(f"{name}: SCF remains after lowering")
                    if name in {"for-zero", "arith-signed-unsigned"}:
                        canonical, canonical_ok = run("canonical", source, ["--canonicalize"])
                        if canonical_ok:
                            result = canonical.read_text()
                            if name == "for-zero":
                                semantic_check = ("scf.for" not in result and
                                                  bool(re.search(r"return %arg0 : i32", result)))
                            else:
                                constants = dict(re.findall(
                                    r"(%[\w]+) = arith.constant (true|false)", result))
                                returned = re.search(r"return (%[\w]+), (%[\w]+) : i1, i1", result)
                                semantic_check = bool(returned and
                                    [constants.get(v) for v in returned.groups()] == ["true", "false"])
                            record["checks"].append({"name": "expected-canonical-structure",
                                                     "passed": semantic_check})
                            if not semantic_check:
                                failures.append(f"{name}: unexpected canonical result")
            entries.append(record)

    if not entries:
        parser.error("no marked MLIR examples found")
    # The tutorial labels this block as actual output, so check that claim too.
    output_check = None
    if "tutorial-sum-positive" in texts and "tutorial-sum-positive-cf" in texts:
        actual_file = output / "tutorial-sum-positive/scf-to-cf.mlir"
        actual = actual_file.read_text() if actual_file.exists() else ""
        output_check = actual.strip() == texts["tutorial-sum-positive-cf"].strip()
        if not output_check:
            failures.append("tutorial: displayed CF output differs from actual tool output")
    manifest = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "mlir_opt": str(opt), "version": version, "docs": str(docs),
        "machine_code_execution": False,
        "scope": "parser/verifier, generic roundtrip, SCF-to-CF, selected canonicalization, diagnostics",
        "example_count": len(entries),
        "valid_count": sum(e["expect"] == "example" for e in entries),
        "invalid_count": sum(e["expect"] == "invalid" for e in entries),
        "tutorial_output_matches": output_check,
        "passed": not failures, "examples": entries, "failures": failures,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(entries)} examples: {manifest['valid_count']} valid, "
          f"{manifest['invalid_count']} expected failures; "
          f"{'PASS' if not failures else 'FAIL'}")
    print(f"Manifest: {output / 'manifest.json'}")
    for failure in failures:
        print(failure, file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
