"""Finite teaching models. These are not GPU execution or memory-model emulation."""
from itertools import permutations

def coverage(n,block):
    groups=(n+block-1)//block
    visits=[0]*n;inactive=[]
    for b in range(groups):
        for t in range(block):
            i=b*block+t
            if i<n:visits[i]+=1
            else:inactive.append(i)
    return {'n':n,'block':block,'groups':groups,'visits':visits,'inactive':inactive}

def interleavings():
    events=[(kind,t) for t in range(4) for kind in ['w','r']]
    valid=unsafe=barrier_valid=0;counterexample=None
    for order in permutations(events):
        pos={e:i for i,e in enumerate(order)}
        if any(pos['w',t]>pos['r',t] for t in range(4)):continue
        valid+=1
        bad=any(pos['r',t]<pos['w',(t+1)%4] for t in range(4))
        unsafe+=bad
        if bad and counterexample is None:counterexample=order
        if max(pos['w',t] for t in range(4))<min(pos['r',t] for t in range(4)):
            assert not bad
            barrier_valid+=1
    return {'thread_order_respecting':valid,'read_before_write':unsafe,
            'all_writes_before_reads':barrier_valid,'counterexample':counterexample}

def banks(stride,column=0):
    return [(t*stride+column)%32 for t in range(32)]

def double_buffer_trace():
    # k=0 still consumes slot0 when k=2 overwrites it: an explicit missing edge.
    slot0=[10,20];first=slot0[0];slot0[:]=[50,60];second=slot0[1]
    return {'broken_read':[first,second],'intended_read':[10,20],
            'missing_dependency':'K0 complete -> C2 overwrite slot0'}

def observations():
    return {'kind':'logical models; no GPU execution',
            'coverage':[coverage(n,b) for n in [0,1,3,4,10,17,1025] for b in [4,32,128]],
            'interleavings':interleavings(),'banks32':banks(32),'banks33':banks(33),
            'double_buffer':double_buffer_trace()}

if __name__=='__main__':
    import json
    print(json.dumps(observations(),ensure_ascii=False,indent=2))
