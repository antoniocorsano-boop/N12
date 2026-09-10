#!/usr/bin/env python3
import csv, math, pathlib

TARGET_FWD=[4.70,4.05,1.20,5.80,2.90,1.20,4.05,4.70]
TARGET_REV=list(reversed(TARGET_FWD))
TOLERANCES=[0.25,0.35,0.50,0.75]
PARALLEL_TOL=18.0
OBLIQUE_MIN=7.0
OBLIQUE_MAX=65.0


def angle(a,b):
    return math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))

def signed_turn(a,b):
    return (b-a+180)%360-180

def dist(a,b):
    return math.hypot(b[0]-a[0], b[1]-a[1])/1000.0

def load_nodes(path):
    out={}
    with open(path,encoding='utf-8-sig',newline='') as f:
        sample=f.read(4096); f.seek(0)
        dialect=csv.Sniffer().sniff(sample,delimiters=';,')
        r=csv.DictReader(f,dialect=dialect)
        for row in r:
            out[row['nodo']] = (float(row['x_mm']),float(row['y_mm']))
    return out

def solve(nodes,target,tol):
    ids=list(nodes)
    neigh=[]
    for L in target:
        d={a:[] for a in ids}
        for a in ids:
            for b in ids:
                if a==b: continue
                ll=dist(nodes[a],nodes[b])
                if abs(ll-L)<=tol:
                    d[a].append((b,ll))
        neigh.append(d)
    sols=[]
    def dfs(path,lens,angs,k):
        if k==8:
            score=sum(abs(l-target[i]) for i,l in enumerate(lens))
            base=angs[0]
            penalty=sum(abs(signed_turn(base,a)) for i,a in enumerate(angs) if i in (2,4,5,6,7))/180.0
            sols.append((score+penalty,path[:],lens[:],angs[:]))
            return
        a=path[-1]
        for b,ll in neigh[k][a]:
            if b in path: continue
            ang=angle(nodes[a],nodes[b])
            cand_angs=angs+[ang]
            if k>=1:
                base=cand_angs[0]
                dev=signed_turn(base,ang)
                if k==1:
                    if not (OBLIQUE_MIN <= abs(dev) <= OBLIQUE_MAX): continue
                elif k==2:
                    if abs(dev)>PARALLEL_TOL: continue
                elif k==3:
                    d2=signed_turn(base,cand_angs[1])
                    if not (OBLIQUE_MIN <= abs(dev) <= OBLIQUE_MAX): continue
                    if d2*dev>=0: continue
                else:
                    if abs(dev)>PARALLEL_TOL: continue
            dfs(path+[b],lens+[ll],cand_angs,k+1)
    for s in ids: dfs([s],[],[],0)
    sols.sort(key=lambda x:x[0])
    return sols

def main():
    ext=pathlib.Path('out/tav5_extended_nodes_reconstructed.csv')
    src=ext if ext.exists() else pathlib.Path('out/tav5_topology_nodes_57.csv')
    nodes=load_nodes(src)
    print('node_source',src,'node_count',len(nodes))
    rows=[]
    for direction,target in [('FORWARD',TARGET_FWD),('REVERSED',TARGET_REV)]:
        for tol in TOLERANCES:
            sols=solve(nodes,target,tol)
            print(direction,'tol',tol,'candidate_count',len(sols))
            for rank,(score,path,lens,angs) in enumerate(sols[:50],1):
                rows.append([direction,tol,rank,score,*path,*lens,*angs])
            if sols:
                score,path,lens,angs=sols[0]
                print('best',direction,tol,score,' -> '.join(path))
                print('lengths',','.join(f'{x:.3f}' for x in lens))
                print('angles',','.join(f'{x:.1f}' for x in angs))
    with open('out/telaio5_signature_candidates.csv','w',newline='',encoding='utf-8') as f:
        w=csv.writer(f)
        w.writerow(['direction','tolerance_m','rank','score','P1','P2','P3','P4','P5','P6','P7','P8','P9','L1','L2','L3','L4','L5','L6','L7','L8','A1','A2','A3','A4','A5','A6','A7','A8'])
        w.writerows(rows)

if __name__=='__main__': main()
