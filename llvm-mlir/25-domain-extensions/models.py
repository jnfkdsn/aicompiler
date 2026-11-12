"""Independent semantic models. These do not execute MLIR-generated code."""
import json

def observe():
    quant=[]
    for x,expected_q,expected_real in [(-.5,126,-.5),(0,128,0),(.75,131,.75),(.3,129,.25),(40,255,31.75),(.125,128,0),(.375,130,.5)]:
        q=max(0,min(255,round(x/.25)+128));real=(q-128)*.25
        assert q==expected_q and real==expected_real
        quant.append({'input':x,'q':q,'dequantized':real})
    sparse=[]
    for positions,coords,values,initial in [([0,2,3],[0,2,1],[2,3,4],[0,0]),([0,2,3],[0,2,1],[2,3,4],[1,2]),([0,2,2],[0,2],[2,3],[0,7]),([0,0,0],[],[],[1,2])]:
        x=[10,20,30];result=initial.copy();dense=[[0]*3 for _ in range(2)]
        for row in range(2):
            for entry in range(positions[row],positions[row+1]):
                col=coords[entry];result[row]+=values[entry]*x[col];dense[row][col]=values[entry]
        reference=[initial[i]+sum(dense[i][j]*x[j] for j in range(3)) for i in range(2)]
        assert result==reference
        sparse.append({'positions':positions,'result':result})
    assert sparse[0]['result']==[110,80] and sparse[1]['result']==[111,82]
    product=complex(1,2)*complex(3,4);assert product==complex(-5,10)
    print(json.dumps({'evidence':'independent Python models, not generated target execution','quant':quant,'csr':sparse,'complex':[product.real,product.imag]},indent=2))
if __name__=='__main__':observe()
