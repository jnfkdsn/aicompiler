import os
import shlex
import lit.formats
config.name='MLIR-diagnosis'
config.test_format=lit.formats.ShTest(execute_external=False)
config.suffixes=['.mlir']
config.test_source_root=os.path.dirname(__file__)
workspace=os.path.abspath(os.path.join(config.test_source_root,'../../../..'))
build=lit_config.params.get('build',os.path.join(workspace,'artifacts/builds/mlir-debug-testing'))
config.test_exec_root=os.path.join(build,'tests')
config.substitutions.extend([
 ('%my-opt',shlex.quote(os.path.join(build,'my-opt'))),
 ('%FileCheck',shlex.quote(os.path.join(workspace,'artifacts/builds/mlir-20.1.8/bin/FileCheck')))
])
