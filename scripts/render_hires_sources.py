from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path
import fitz
from PIL import Image

DEFAULT_COMMIT='d521f11a6989664a54409ab0df064903d8986564'
SOURCES={
 'TAV-01S':'archive/documentazione_originaria/tavola1-2.pdf',
 'TAV-01A':'archive/documentazione_originaria/tavola1-3.pdf',
 'TAV-05S':'archive/documentazione_originaria/tavola 5.pdf',
 'TAV-07A':'archive/documentazione_originaria/tavola7.pdf',
}

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def git_extract(commit: str, repo_path: str, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    data=subprocess.check_output(['git','show',f'{commit}:{repo_path}'])
    dst.write_bytes(data)

def extract_native(pdf_path: Path, out_png: Path):
    doc=fitz.open(pdf_path)
    if len(doc)!=1:
        raise RuntimeError(f'Expected 1 page, got {len(doc)}')
    page=doc[0]
    imgs=page.get_images(full=True)
    if not imgs:
        pix=page.get_pixmap(matrix=fitz.Matrix(4,4), alpha=False)
        pix.save(out_png)
        return {'method':'render_4x','width':pix.width,'height':pix.height,'image_count':0}
    best=max(imgs, key=lambda row: row[2]*row[3])
    xref=best[0]
    info=doc.extract_image(xref)
    native=out_png.with_suffix('.'+info['ext'])
    native.write_bytes(info['image'])
    im=Image.open(native).convert('RGB')
    im.save(out_png, format='PNG', compress_level=1)
    return {'method':'native_image','width':im.width,'height':im.height,'image_count':len(imgs),'xref':xref,'native_ext':info['ext']}

def tile_image(img_path: Path, out_dir: Path, source_id: str, tile_size=2400, overlap=0.125):
    im=Image.open(img_path).convert('RGB')
    w,h=im.size
    step=max(1,int(tile_size*(1-overlap)))
    xs=list(range(0,max(1,w-tile_size+1),step))
    ys=list(range(0,max(1,h-tile_size+1),step))
    if not xs or xs[-1]+tile_size<w: xs.append(max(0,w-tile_size))
    if not ys or ys[-1]+tile_size<h: ys.append(max(0,h-tile_size))
    xs=sorted(set(xs)); ys=sorted(set(ys))
    rows=[]
    for r,y0 in enumerate(ys,1):
        for c,x0 in enumerate(xs,1):
            x1=min(w,x0+tile_size); y1=min(h,y0+tile_size)
            tile_id=f'{source_id}_L1_R{r:02d}C{c:02d}'
            p=out_dir/f'{tile_id}.png'
            im.crop((x0,y0,x1,y1)).save(p,compress_level=1)
            rows.append({'tile_id':tile_id,'u0':x0,'v0':y0,'u1':x1,'v1':y1,'width':x1-x0,'height':y1-y0})
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--commit',default=DEFAULT_COMMIT)
    ap.add_argument('--out',default='artifacts/hires')
    ap.add_argument('--tile-size',type=int,default=2400)
    ap.add_argument('--overlap',type=float,default=0.125)
    args=ap.parse_args()
    out=Path(args.out); srcdir=out/'sources'; rasterdir=out/'raster'; tiledir=out/'tiles'
    for d in (srcdir,rasterdir,tiledir): d.mkdir(parents=True,exist_ok=True)
    index={'commit':args.commit,'tile_size':args.tile_size,'overlap':args.overlap,'sources':[]}
    for sid,rpath in SOURCES.items():
        pdf=srcdir/f'{sid}.pdf'; git_extract(args.commit,rpath,pdf)
        raster=rasterdir/f'{sid}_native.png'
        meta=extract_native(pdf,raster)
        tiles=tile_image(raster,tiledir,sid,args.tile_size,args.overlap)
        entry={'source_id':sid,'repo_path':rpath,'pdf_sha256':sha256(pdf),'pdf_size':pdf.stat().st_size,
               'raster_sha256':sha256(raster),**meta,'tiles':tiles}
        index['sources'].append(entry)
    (out/'hires_index.json').write_text(json.dumps(index,indent=2),encoding='utf-8')
    print(json.dumps(index,indent=2))

if __name__=='__main__': main()
