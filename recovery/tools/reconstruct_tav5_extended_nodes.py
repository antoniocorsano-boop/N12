#!/usr/bin/env python3
import csv, math, pathlib

TOL_MM=80.0
MIN_SUPPORT=2


def load_known(path):
    out={}
    with open(path,encoding='utf-8-sig') as f:
        r=csv.DictReader(f,delimiter=';')
        for row in r:
            out[row['nodo']] = (float(row['x_mm']),float(row['y_mm']))
    return out


def load_edges(path):
    out=[]
    with open(path,encoding='utf-8-sig') as f:
        r=csv.DictReader(f,delimiter=';')
        for row in r:
            out.append({
                'id':row['id'], 'a':row['nodo_1'], 'b':row['nodo_2'],
                'L':float(row['lunghezza_grafica_mm']), 'ori':row['orientamento']
            })
    return out


def cand_from(anchor, L, ori):
    x,y=anchor
    if ori=='H': return [(x-L,y),(x+L,y)]
    if ori=='V': return [(x,y-L),(x,y+L)]
    return []


def cluster(points,tol):
    clusters=[]
    for p,src in points:
        placed=False
        for c in clusters:
            cx=sum(q[0][0] for q in c)/len(c); cy=sum(q[0][1] for q in c)/len(c)
            if math.hypot(p[0]-cx,p[1]-cy)<=tol:
                c.append((p,src)); placed=True; break
        if not placed: clusters.append([(p,src)])
    clusters.sort(key=len,reverse=True)
    return clusters


def main():
    known=load_known(pathlib.Path('out/tav5_topology_nodes_57.csv'))
    edges=load_edges(pathlib.Path('out/tav5_topology_connections_v07.csv'))
    universe=sorted({e['a'] for e in edges}|{e['b'] for e in edges})
    inferred={}
    evidence={}

    for iteration in range(20):
        added=0
        resolved={**known,**inferred}
        for u in universe:
            if u in resolved: continue
            candidates=[]
            for e in edges:
                if e['a']==u and e['b'] in resolved:
                    for p in cand_from(resolved[e['b']],e['L'],e['ori']): candidates.append((p,e['id']))
                elif e['b']==u and e['a'] in resolved:
                    for p in cand_from(resolved[e['a']],e['L'],e['ori']): candidates.append((p,e['id']))
            cs=cluster(candidates,TOL_MM)
            if cs and len({src for _,src in cs[0]})>=MIN_SUPPORT:
                pts=cs[0]
                x=sum(p[0] for p,_ in pts)/len(pts); y=sum(p[1] for p,_ in pts)/len(pts)
                inferred[u]=(x,y)
                evidence[u]=sorted({src for _,src in pts})
                added+=1
        print('iteration',iteration+1,'added',added,'total_inferred',len(inferred))
        if added==0: break

    with open('out/tav5_extended_nodes_reconstructed.csv','w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['nodo','x_mm','y_mm','status','support_edges'])
        for n,p in sorted(known.items()): w.writerow([n,f'{p[0]:.1f}',f'{p[1]:.1f}','KNOWN_57',''])
        for n,p in sorted(inferred.items()): w.writerow([n,f'{p[0]:.1f}',f'{p[1]:.1f}','RIF_RECONSTRUCTED',';'.join(evidence[n])])
    unresolved=[u for u in universe if u not in known and u not in inferred]
    with open('out/tav5_extended_nodes_unresolved.txt','w',encoding='utf-8') as f:
        for u in unresolved: f.write(u+'\n')
    print('known',len(known),'inferred',len(inferred),'unresolved',len(unresolved),'universe',len(universe))

if __name__=='__main__': main()
