#!/usr/bin/env python3
"""Deskew and isolate one historic engraving from each crooked scanned leaf.

Uses the inked copperplate's long border lines, not a single percentage crop.
A per-image projective homography straightens skew and keystone. It never
recreates missing artwork. Full unmodified Heidelberg images remain in /art.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"public"/"art"
OUT=ROOT/"public"/"engravings"
THUMBS=OUT/"thumb"
DATA=ROOT/"public"/"data"
PREVIEW=ROOT/"qa"
SAMPLES=[1,2,3,4,6,15,26,32,43,52,53,60,70,84,90,100,104]

# Fallback is evaluated per scan only when frame detection is underconstrained.
# It is always applied AFTER automatic deskew, never blindly on the raw photo.
FALLBACK=(.101,.086,.869,.728)
MAX_ANGLE=8.0

def scaled(image, max_dim=1500):
    h,w=image.shape[:2]
    factor=min(1.,float(max_dim)/max(h,w))
    return cv2.resize(image,(round(w*factor),round(h*factor)),interpolation=cv2.INTER_AREA) if factor<1 else image

def robust_estimate(rows, expected, tolerance, kind):
    """Aggregate multiple matching physical borders, not arbitrary ink strokes."""
    if not rows:return None
    # each tuple is (position, slope, length); choose plausible consensus.
    rows=[x for x in rows if abs(x[0]-expected)<=tolerance]
    if not rows:return None
    peaks={}
    for pos,slope,length in rows:
        bucket=round(pos/9)
        peaks[bucket]=peaks.get(bucket,0)+length/(1+abs(pos-expected)/max(tolerance,1))
    winning=max(peaks,key=peaks.get)
    cluster=[x for x in rows if abs(x[0]-winning*9)<17]
    if not cluster:return None
    weight=sum(c[2] for c in cluster)
    p=sum(c[0]*c[2] for c in cluster)/weight
    slope=sum(c[1]*c[2] for c in cluster)/weight
    return p,slope,len(cluster),weight

def find_border(image):
    h,w=image.shape[:2]
    gray=cv2.cvtColor(image,cv2.COLOR_RGB2GRAY)
    gray=cv2.createCLAHE(clipLimit=2.0,tileGridSize=(7,7)).apply(gray)
    edges=cv2.Canny(gray,72,180,apertureSize=3)
    seg=cv2.HoughLinesP(edges,rho=1,theta=np.pi/900,threshold=54,
                         minLineLength=int(w*.29),maxLineGap=24)
    vertical=[[],[]];horizontal=[[],[]]
    if seg is not None:
        for x1,y1,x2,y2 in seg.reshape(-1,4):
            dx=float(x2-x1);dy=float(y2-y1)
            length=math.hypot(dx,dy)
            if length<min(w,h)*.26:continue
            if abs(dy)>h*.21 and abs(dx/dy)<.20:
                center=(y1+y2)/2
                xpos=(x1+x2)/2+dx/dy*(h*.39-center)
                if .044*w<xpos<.31*w:vertical[0].append((xpos,dx/dy,length))
                elif .65*w<xpos<.96*w:vertical[1].append((xpos,dx/dy,length))
            if abs(dx)>w*.30 and abs(dy/dx)<.20:
                center=(x1+x2)/2
                ypos=(y1+y2)/2+dy/dx*(w*.5-center)
                if .038*h<ypos<.24*h:horizontal[0].append((ypos,dy/dx,length))
                elif .56*h<ypos<.85*h:horizontal[1].append((ypos,dy/dx,length))
    left=robust_estimate(vertical[0],w*.105,w*.18,"left")
    right=robust_estimate(vertical[1],w*.847,w*.18,"right")
    top=robust_estimate(horizontal[0],h*.093,h*.145,"top")
    bottom=robust_estimate(horizontal[1],h*.737,h*.16,"bottom")

    # If one frame edge is absent, determine its position from line continuity.
    # Long lines have much stronger support than the dense engraved crosshatching.
    if not left or not right or not top:
        angle=0.
        lines=[x for side in vertical for x in side]
        if lines:
            slopes=sorted((sl,len_) for _,sl,len_ in lines if abs(sl)<.17)
            if slopes:
                angle=-math.degrees(math.atan(sorted(slopes,key=lambda v:v[0])[len(slopes)//2][0]))
        angle=max(-MAX_ANGLE,min(MAX_ANGLE,angle))
        matrix=cv2.getRotationMatrix2D((w/2,h/2),angle,1.0)
        rotated=cv2.warpAffine(image,matrix,(w,h),
                              flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
        l,t,r,b=FALLBACK
        # Improve the fallback by maximizing continuous ink at approximate frame edges.
        g=cv2.cvtColor(rotated,cv2.COLOR_RGB2GRAY)
        ink=(g<78).astype(np.float32)
        y1=int(h*.14);y2=int(h*.67)
        def pick_col(a,b,prior):
            xs=np.arange(max(0,int(w*a)),min(w,int(w*b)))
            scores=ink[y1:y2,xs].mean(axis=0)
            scores-=.11*np.abs(xs-prior)/(w*.18)
            return int(xs[int(np.argmax(scores))])
        xl=pick_col(.06,.22,w*.105);xr=pick_col(.73,.94,w*.847)
        if xr-xl<.48*w:xl=int(l*w);xr=int(r*w)
        x1=max(0,xl+round(w*.006));x2=min(w,xr-round(w*.006))
        ytop=int(t*h);ybottom=int(min(.81*h,ytop+1.48*(x2-x1)))
        if ybottom-ytop<.40*h:ybottom=int(b*h)
        return rotated[ytop:ybottom,x1:x2],{
            "method":"rotation+per-page-ink-projection",
            "rotation_degrees":round(angle,3),
            "rect":[x1,ytop,x2,ybottom],
            "confidence":"fallback",
            "border_candidates":[len(x) for x in vertical+horizontal]
        }

    lx,ls,ln,lw=left;rx,rs,rn,rw=right
    ty,ts,tn,tw=top
    if rx-lx < w*.45:
        raise ValueError("Detected plate borders are implausibly narrow")

    # The bottom edge borders the engraved scene, before the letterpress caption.
    # A bottom line is accepted only near the historical 1.5:1 image proportion.
    by_expected=ty+1.49*(rx-lx)
    if bottom and abs(bottom[0]-by_expected)<.065*h:
        by,bs,bn,bw=bottom
        bottom_used=True
    else:
        by=float(by_expected);bs=ts
        bottom_used=False
    by=min(by,.83*h)
    if by-ty<.39*h:
        raise ValueError("Detected picture too short")

    def vline(x0,slope,y):return x0+slope*(y-h*.39)
    def hline(y0,slope,x):return y0+slope*(x-w*.5)
    def intersect(x0,xs,y0,ys):
        # Solve x=x0+xs*(y-h*.39), y=y0+ys*(x-w*.5).
        a=x0-xs*h*.39
        b=y0-ys*w*.5
        x=(a+xs*b)/(1-xs*ys)
        y=b+ys*x
        return x,y
    tl=intersect(lx,ls,ty,ts)
    tr=intersect(rx,rs,ty,ts)
    br=intersect(rx,rs,by,bs)
    bl=intersect(lx,ls,by,bs)
    corners=np.float32([tl,tr,br,bl])
    pad=max(3,round(w*.007))
    # Inset on all four sides excludes only copperplate's frame rule.
    insets=np.float32([[pad,pad],[-pad,pad],[-pad,-pad],[pad,-pad]])
    # Unit directional vectors give safe insets in the scanned quadrilateral.
    points=np.array(corners,dtype=np.float64)
    center=points.mean(axis=0)
    for i in range(4):
        toward=center-points[i]
        points[i]+=toward/max(np.linalg.norm(toward),1e-6)*(pad*1.3)
    src=np.float32(points)
    width=int(round((np.linalg.norm(src[1]-src[0])+np.linalg.norm(src[2]-src[3]))/2))
    height=int(round((np.linalg.norm(src[3]-src[0])+np.linalg.norm(src[2]-src[1]))/2))
    if width<w*.44 or height<h*.40 or width>w*.94 or height>h*.82:
        raise ValueError(f"Implausible rectified size {width}x{height} from {w}x{h}")
    dest=np.float32([[0,0],[width-1,0],[width-1,height-1],[0,height-1]])
    H=cv2.getPerspectiveTransform(src,dest)
    fixed=cv2.warpPerspective(image,H,(width,height),flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_REPLICATE)
    angle=math.degrees(math.atan((ls+rs)/2))
    confidence="strong" if ln>=2 and rn>=2 and tn>=1 and bottom_used else "estimated-bottom"
    return fixed,{
        "method":"four-edge-perspective-rectification",
        "rotation_degrees":round(angle,3),
        "source_corners":src.round(2).tolist(),
        "rectified_size":[width,height],
        "confidence":confidence,
        "border_candidates":[len(x) for x in vertical+horizontal],
        "bottom_line_detected":bottom_used
    }

def image_quality(img):
    h,w=img.shape[:2]
    g=cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    ink=float(np.mean(g<122))
    return {"ink_fraction":round(ink,4),"aspect":round(w/h,4),"width":w,"height":h}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    THUMBS.mkdir(parents=True,exist_ok=True)
    DATA.mkdir(parents=True,exist_ok=True)
    PREVIEW.mkdir(parents=True,exist_ok=True)
    ledger={}
    thumbnails=[]
    failures=[]
    for n in range(1,105):
        name=f"{n:03d}"
        with Image.open(SOURCE/(name+".webp")) as f:
            raw=np.array(ImageOps.exif_transpose(f).convert("RGB"))
        # Work at original source resolution. Images do not need inferred content.
        try:
            result,stats=find_border(raw)
        except Exception as e:
            failures.append(f"{n}: {e}")
            raise
        metric=image_quality(result)
        if not .055<metric["ink_fraction"]<.90:
            raise AssertionError(f"Plate {n}: suspected blank or wrong crop: {metric}")
        if not .35<metric["aspect"]<.91:
            raise AssertionError(f"Plate {n}: unexpected aspect {metric}")
        pil=Image.fromarray(result)
        pil.save(OUT/(name+".webp"),"WEBP",quality=89,method=5)
        small=pil.copy();small.thumbnail((600,1000),Image.Resampling.LANCZOS)
        small.save(THUMBS/(name+".webp"),"WEBP",quality=84,method=5)
        ledger[str(n)]={
            "source_original":f"/art/{name}.webp",
            "source_pixels":[raw.shape[1],raw.shape[0]],
            **stats, **metric
        }
        preview=pil.copy();preview.thumbnail((195,275),Image.Resampling.LANCZOS)
        panel=Image.new("RGB",(216,314),"#eeeae1")
        panel.paste(preview,((216-preview.width)//2,7))
        ImageDraw.Draw(panel).text((9,288),f"{name}   {metric['aspect']:.2f}   {stats['confidence'][:5]}",fill="#242521")
        thumbnails.append(panel)
    # All 104 must be visually reviewable in a 13 x 8 sheet, with no omissions.
    cols=13;rows=8
    contact=Image.new("RGB",(cols*216,rows*314),"#eeeae1")
    for i,p in enumerate(thumbnails):
        contact.paste(p,((i%cols)*216,(i//cols)*314))
    contact.save(PREVIEW/"crop-audit-all-104.jpg",quality=85,optimize=True)
    (DATA/"crop-provenance.json").write_text(json.dumps({
        "edition":"Giessen 1768, Universitätsbibliothek Heidelberg",
        "method":"Per-image frame-line geometry; perspective or deskew with fallback; no synthesized image content.",
        "plates":ledger
    },ensure_ascii=False,indent=2))
    assert len(ledger)==104 and len(list(OUT.glob("*.webp")))==104
    print("CROP COMPLETE: 104 rectified original engravings",
          "method_counts", {kind:sum(v['method']==kind for v in ledger.values())
                            for kind in set(v['method'] for v in ledger.values())},flush=True)
    print("FALLBACK IDS",[i for i,v in ledger.items() if v["confidence"]=="fallback"],flush=True)

if __name__=="__main__":
    main()
