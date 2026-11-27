#!/usr/bin/env python3
"""Re-extract all scenes from the unchanged Heidelberg photographs.
Fit the four OUTER printed frame edges to ink/paper contrast, then locate the
picture/caption boundary after projective rectification. No guessed rotation
from scene content, no generated pixels, no forced plate aspect ratio.
"""
import json, math, hashlib, argparse
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"public/art"
OUT=ROOT/"public/engravings"
QA=ROOT/"qa/precision"
# Directly inspected source-image coordinates (displayed at 927 x 1630).
# Order: top left, top right, bottom right, bottom left of complete printed frame.
# Last entry is fraction to picture/caption rule, before letterpress title.
MANUAL={
 1:([[64,114],[784,103],[782,1313],[77,1314]],.909),
 13:([[66,154],[748,140],[765,1318],[85,1317]],.905),
 100:([[62,129],[738,123],[749,1303],[79,1294]],.893),
 104:([[60,125],[780,111],[783,1368],[70,1366]],.905)
}
def sample(g,xx,yy):
    return g[np.clip(np.rint(yy).astype(int),0,g.shape[0]-1),np.clip(np.rint(xx).astype(int),0,g.shape[1]-1)]
def fit_edge(g,edge):
    h,w=g.shape
    vert=edge in ("left","right")
    size=w if vert else h
    sign=-1 if edge in ("left","top") else 1
    if vert:
        lo,hi=(.035,.205) if edge=="left" else (.715,.965)
        along=np.linspace(.18*h,.69*h,130);mid=.435*h
        prior=.085*w if edge=="left" else .845*w
    else:
        lo,hi=(.045,.145) if edge=="top" else (.72,.88)
        along=np.linspace(.22*w,.71*w,130);mid=.465*w
        prior=.083*h if edge=="top" else .795*h
    def evaluate(pos,slopes):
        p,s=np.meshgrid(pos,slopes)
        p=p.ravel();s=s.ravel()
        center=p[:,None]+s[:,None]*(along-mid)
        def at(offset):
            perp=center+offset
            return sample(g,perp,along[None,:]) if vert else sample(g,along[None,:],perp)
        dark=np.minimum.reduce([at(i) for i in (-2,0,2)])
        outside=np.mean([at(sign*i) for i in (11,17,25)],axis=0)
        # An actual frame is a continuous dark rule bordering blank paper;
        # scene hatching and edges inside the scene lack the paper contrast.
        contrast=outside-dark
        score=.55*np.mean(contrast,axis=1)+.30*np.quantile(contrast,.25,axis=1)+.15*np.mean(outside,axis=1)
        score-=4*np.abs(p-prior)/(size*.1)
        k=int(np.argmax(score))
        return float(p[k]),float(s[k]),float(score[k]),float(np.mean(contrast[k]>25))
    p,s,_,_=evaluate(np.arange(lo*size,hi*size,3.),np.arange(-.09,.091,.006))
    p,s,score,support=evaluate(np.arange(p-4,p+4.1,.5),np.arange(s-.009,s+.0091,.00075))
    return p,s,mid,score,support
def intersection(v,h):
    a,vs,vm,*_=v;b,hs,hm,*_=h
    a-=vs*vm;b-=hs*hm
    x=(a+vs*b)/(1-vs*hs)
    return [x,b+hs*x]
def rectify(raw,i):
    h,w=raw.shape[:2]
    g=cv2.cvtColor(raw,cv2.COLOR_RGB2GRAY).astype(np.float32)
    edges={k:fit_edge(g,k) for k in ("left","right","top","bottom")}
    l,r,t,b=(edges[k] for k in ("left","right","top","bottom"))
    pts=np.array([intersection(l,t),intersection(r,t),intersection(r,b),intersection(l,b)],dtype=np.float32)
    cutoff=None
    if i in MANUAL:
        points,cutoff=MANUAL[i]
        pts=np.array(points,dtype=np.float32)*np.array([w/927,h/1630],dtype=np.float32)
    assert np.all(pts>=0) and np.all(pts[:,0]<w) and np.all(pts[:,1]<h), (i,pts)
    width=round((np.linalg.norm(pts[1]-pts[0])+np.linalg.norm(pts[2]-pts[3]))/2)
    height=round((np.linalg.norm(pts[3]-pts[0])+np.linalg.norm(pts[2]-pts[1]))/2)
    assert .55*w<width<.94*w and .58*h<height<.86*h,(i,width,height)
    dst=np.float32([[0,0],[width-1,0],[width-1,height-1],[0,height-1]])
    mat=cv2.getPerspectiveTransform(pts,dst)
    fixed=cv2.warpPerspective(raw,mat,(width,height),flags=cv2.INTER_CUBIC)
    gray=cv2.cvtColor(fixed,cv2.COLOR_RGB2GRAY).astype(np.float32)
    # Caption lies below the art and has white paper between the lines of text.
    # Score the actual transverse rule, not a constant width/height ratio.
    inner=gray[:,int(width*.055):int(width*.945)]
    if i==44:cutoff=.8995  # visually verified transverse rule, not the title lettering
    if cutoff is None:
        candidates=range(round(height*.852),round(height*.948))
        scores=[]
        for y in candidates:
            dark=255-np.mean(np.min(inner[y-1:y+2],axis=0))
            continuous=np.mean(np.min(inner[y-1:y+2],axis=0)<105)
            above=np.mean(inner[y-13:y-3])
            below=np.mean(inner[y+5:y+20])
            scores.append(.45*dark+45*continuous+.72*(below-above)-12*abs(y/height-.90)/.05)
        y=list(candidates)[int(np.argmax(scores))]
    else:y=round(height*cutoff)
    # Remove the outer printed double rules; leave all scene pixels inside.
    # Inset based on physical line width, not the former incorrect scene rectangle.
    inset=max(5,round(width*.010))
    scene=fixed[inset:y,inset:width-inset]
    assert .48<scene.shape[1]/scene.shape[0]<.85,(i,scene.shape)
    confidence=min(v[4] for v in edges.values())
    return scene,{"source_corners":pts.round(2).tolist(),"source_pixels":[w,h],
      "full_frame_size":[width,height],"scene_rect":[inset,inset,width-inset,y],
      "method":"visually-anchored-perspective" if i in MANUAL else "outer-ink-paper-frame-perspective",
      "edge_support":{k:round(v[4],3) for k,v in edges.items()},
      "confidence":round(confidence,3),"manual_coordinates":i in MANUAL,"manual_caption_boundary":i==44 or i in MANUAL,
      "width":scene.shape[1],"height":scene.shape[0],
      "source_original":f"/art/{i:03d}.webp"}
def main():
    OUT.mkdir(exist_ok=True);(OUT/"thumb").mkdir(exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    parser=argparse.ArgumentParser();parser.add_argument("--only",nargs="+",type=int);args=parser.parse_args()
    selected=set(args.only or range(1,105))
    ledger=json.loads((ROOT/"public/data/crop-provenance.json").read_text())["plates"] if args.only else {}
    panels=[]
    for i in range(1,105):
        name=f"{i:03d}";p=SOURCE/(name+".webp")
        with Image.open(p) as im:raw=np.array(ImageOps.exif_transpose(im).convert("RGB"))
        if i in selected:
            scene,rec=rectify(raw,i)
            pic=Image.fromarray(scene);pic.save(OUT/(name+".webp"),"WEBP",quality=94,method=4)
            thumb=pic.copy();thumb.thumbnail((600,1000),Image.Resampling.LANCZOS);thumb.save(OUT/"thumb"/(name+".webp"),"WEBP",quality=88,method=4)
            rec["source_sha256"]=hashlib.sha256(p.read_bytes()).hexdigest()
            rec["crop_sha256"]=hashlib.sha256((OUT/(name+".webp")).read_bytes()).hexdigest()
            ledger[str(i)]=rec
        else:
            rec=ledger[str(i)]
            with Image.open(OUT/(name+".webp")) as f:pic=f.convert("RGB")
        # Source geometry overlay and the corresponding crop side-by-side.
        rawview=Image.fromarray(raw);d=ImageDraw.Draw(rawview)
        pts=[tuple(v) for v in rec["source_corners"]];d.line(pts+[pts[0]],fill="#e24a30",width=5)
        rawview.thumbnail((145,250),Image.Resampling.LANCZOS)
        pic.thumbnail((170,250),Image.Resampling.LANCZOS)
        panel=Image.new("RGB",(334,282),"#f4f2ec")
        panel.paste(rawview,(5+(145-rawview.width)//2,6))
        panel.paste(pic,(155+(170-pic.width)//2,6))
        ImageDraw.Draw(panel).text((8,263),f"{name}  support={rec['confidence']:.2f}",fill="#191916")
        panels.append(panel)
        print(name,rec["source_corners"],rec["scene_rect"],rec["confidence"],flush=True)
    for start in range(0,104,8):
        sheet=Image.new("RGB",(334*4,282*2),"#f4f2ec")
        for j,panel in enumerate(panels[start:start+8]):sheet.paste(panel,((j%4)*334,(j//4)*282))
        sheet.save(QA/f"row-{start//8+1:02d}.jpg",quality=90)
    (ROOT/"public/data/crop-provenance.json").write_text(json.dumps({"edition":"Giessen 1768, Universitätsbibliothek Heidelberg","method":"Outer ink-paper contrast frame rectification; picture/caption separator; original source retained. Automatic proposals require visual review.","plates":ledger},indent=2)+"\n")
    print("CROP COMPLETE",len(ledger),"source-derived engravings; 13 review sheets")
if __name__=="__main__":main()
