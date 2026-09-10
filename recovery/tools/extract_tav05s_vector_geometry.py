#!/usr/bin/env python3
import fitz, csv, json, math, pathlib

PDF=pathlib.Path('out/TAV-05S.pdf')
OUT=pathlib.Path('out/vector')
OUT.mkdir(parents=True,exist_ok=True)

doc=fitz.open(PDF)
summary={'schema':'N12_TAV05S_VECTOR_EXTRACTION_v1','source':'TAV-05S','pages':[]}
all_segments=[]
all_words=[]

for pno,page in enumerate(doc):
    rect=page.rect
    drawings=page.get_drawings()
    words=page.get_text('words')
    segs=[]
    for di,d in enumerate(drawings):
        for ii,item in enumerate(d.get('items',[])):
            kind=item[0]
            if kind=='l':
                p1,p2=item[1],item[2]
                L=math.hypot(p2.x-p1.x,p2.y-p1.y)
                seg={
                    'page':pno+1,'drawing':di,'item':ii,'kind':'line',
                    'x1':p1.x,'y1':p1.y,'x2':p2.x,'y2':p2.y,
                    'length_pt':L,
                    'angle_deg':math.degrees(math.atan2(p2.y-p1.y,p2.x-p1.x)),
                    'width':d.get('width'), 'color':str(d.get('color')),
                    'fill':str(d.get('fill'))
                }
                segs.append(seg); all_segments.append(seg)
            elif kind=='re':
                r=item[1]
                pts=[(r.x0,r.y0,r.x1,r.y0),(r.x1,r.y0,r.x1,r.y1),(r.x1,r.y1,r.x0,r.y1),(r.x0,r.y1,r.x0,r.y0)]
                for jj,(x1,y1,x2,y2) in enumerate(pts):
                    L=math.hypot(x2-x1,y2-y1)
                    seg={'page':pno+1,'drawing':di,'item':f'{ii}.{jj}','kind':'rect-edge','x1':x1,'y1':y1,'x2':x2,'y2':y2,'length_pt':L,'angle_deg':math.degrees(math.atan2(y2-y1,x2-x1)),'width':d.get('width'),'color':str(d.get('color')),'fill':str(d.get('fill'))}
                    segs.append(seg); all_segments.append(seg)
    for w in words:
        rec={'page':pno+1,'x0':w[0],'y0':w[1],'x1':w[2],'y1':w[3],'text':w[4],'block':w[5],'line':w[6],'word':w[7]}
        all_words.append(rec)
    svg=page.get_svg_image(text_as_path=False)
    (OUT/f'page-{pno+1}.svg').write_text(svg,encoding='utf-8')
    summary['pages'].append({'page':pno+1,'width_pt':rect.width,'height_pt':rect.height,'drawing_objects':len(drawings),'line_segments':len(segs),'words':len(words)})

with (OUT/'tav05s_vector_segments.csv').open('w',newline='',encoding='utf-8') as f:
    fields=['page','drawing','item','kind','x1','y1','x2','y2','length_pt','angle_deg','width','color','fill']
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(all_segments)
with (OUT/'tav05s_words.csv').open('w',newline='',encoding='utf-8') as f:
    fields=['page','x0','y0','x1','y1','text','block','line','word']
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(all_words)
summary['total_segments']=len(all_segments); summary['total_words']=len(all_words)
(OUT/'tav05s_vector_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
