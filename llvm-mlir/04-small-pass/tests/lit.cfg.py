import os
import shlex
import lit.formats

config.name = "MLIR-small-pass"
config.test_format = lit.formats.ShTest(execute_external=False)
config.suffixes = [".mlir", ".test"]
config.test_source_root = os.path.dirname(__file__)
workspace = os.path.abspath(os.path.join(config.test_source_root, "../../../.."))
build = lit_config.params.get("build", os.path.join(workspace, "artifacts/builds/mlir-small-pass"))
llvm_bin = lit_config.params.get("llvm_bin", os.path.join(workspace, "artifacts/builds/mlir-20.1.8/bin"))
config.test_exec_root = os.path.join(build, "tests")
config.substitutions.extend([
    ("%lab-opt", shlex.quote(os.path.join(build, "lab-opt"))),
    ("%FileCheck", shlex.quote(os.path.join(llvm_bin, "FileCheck"))),
])
