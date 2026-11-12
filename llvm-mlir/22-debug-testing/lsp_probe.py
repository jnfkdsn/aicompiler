"""A minimal protocol handshake, not an IDE integration test."""
import json
from pathlib import Path
import subprocess
WORKSPACE=Path(__file__).resolve().parents[3]
def frame(message):
    body=json.dumps(message).encode();return f'Content-Length: {len(body)}\r\n\r\n'.encode()+body
messages=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'processId':None,'rootUri':None,'capabilities':{}}},{'jsonrpc':'2.0','id':2,'method':'shutdown','params':None},{'jsonrpc':'2.0','method':'exit','params':None}]
r=subprocess.run([str(WORKSPACE/'artifacts/builds/mlir-20.1.8/bin/mlir-lsp-server')],input=b''.join(map(frame,messages)),capture_output=True,timeout=20)
if r.returncode:raise SystemExit(r.stderr.decode())
data=r.stdout;responses=[]
while data:
    header,body=data.split(b'\r\n\r\n',1)
    length=int(header.split(b':',1)[1]);responses.append(json.loads(body[:length]));data=body[length:]
init=next(x for x in responses if x.get('id')==1)
assert 'capabilities' in init['result']
assert any(x.get('id')==2 and x.get('result','missing') is None for x in responses)
print(json.dumps(init['result'],ensure_ascii=False,indent=2))
