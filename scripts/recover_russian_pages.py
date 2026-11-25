#!/usr/bin/env python3
"""Recover public-domain Russian pages independently; retain partial success and exact provenance."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
from io import BytesIO
from PIL import Image, ImageOps
import argparse, hashlib, json, time
ROOT=Path(__file__).resolve().parents[1]
BASE="https://kp.rusneb.ru/"
BOOKS={"ot":("5fcf8bb3991f3b91423439b5",260),"nt":("5fcf8bb3991f3b91423439ad",196)}
p=argparse.ArgumentParser()
p.add_argument("--book",choices=BOOKS,required=True)
p.add_argument("--workers",type=int,default=4)
args=p.parse_args()
book=args.book
identifier,count=BOOKS[book]
dest=ROOT/"public"/"russian-1825-pages"/book
receipts=ROOT/"sources"/"russian-1825-pages"/book
dest.mkdir(parents=True,exist_ok=True)
receipts.mkdir(parents=True,exist_ok=True)
def write_json(p,x):
    tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n","utf8")
    tmp.replace(p)
def request(url,timeout=25,retries=3):
    last=None
    for i in range(retries):
        try:
            req=Request(url,headers={"User-Agent":"Mozilla/5.0 (historical public-domain archive)","Accept":"image/jpeg,application/json,*/*"})
            with urlopen(req,timeout=timeout) as response:
                return response.read()
        except Exception as e:
            last=e
            time.sleep(2*(i+1))
    raise RuntimeError(str(last))
manifest_url=BASE+f"api/v1/materials/{identifier}/pages"
manifest=None
try:
    manifest=json.loads(request(manifest_url,timeout=15,retries=1))
    if not isinstance(manifest,list) or len(manifest)!=count: raise ValueError("Unexpected manifest length")
except Exception as e:
    print("Manifest unavailable; testing the established direct original-page path:",str(e),flush=True)
    manifest=[{"original":f"attachments_new/attachment/{identifier}/preview-page-{i}.jpg"} for i in range(1,count+1)]
def acquire(n):
    path=dest/f"{n:03d}.webp"
    recpath=receipts/f"{n:03d}.json"
    if path.exists() and recpath.exists():
        r=json.loads(recpath.read_text("utf8"))
        if hashlib.sha256(path.read_bytes()).hexdigest()==r.get("archived_sha256"):return r
    url=BASE+manifest[n-1]["original"].lstrip("/")
    raw=request(url)
    if len(raw)<40000:raise ValueError("Unexpectedly small image")
    with Image.open(BytesIO(raw)) as im:
        im.load()
        w,h=im.size
        if min(w,h)<500:raise ValueError(f"Invalid image size {w}x{h}")
        tmp=path.with_suffix(".tmp.webp")
        ImageOps.exif_transpose(im).convert("RGB").save(tmp,"WEBP",quality=83,method=4)
        tmp.replace(path)
    r={"page":n,"image":f"/russian-1825-pages/{book}/{path.name}","source":url,
       "source_sha256":hashlib.sha256(raw).hexdigest(),"archived_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
       "source_bytes":len(raw),"width":w,"height":h}
    write_json(recpath,r)
    return r
results=[]; errors=[]
with ThreadPoolExecutor(max_workers=args.workers) as pool:
    tasks={pool.submit(acquire,n):n for n in range(1,count+1)}
    for f in as_completed(tasks):
        n=tasks[f]
        try:results.append(f.result())
        except Exception as e:errors.append({"page":n,"error":str(e)});print("FAILED PAGE",n,str(e),flush=True)
        if (len(results)+len(errors))%10==0:print(book,len(results),"/",count,"acquired;",len(errors),"failed",flush=True)
results.sort(key=lambda r:r["page"])
record={"edition":"Сто четыре священныя истории, Moscow, 1825; historical Russian witness; translator attribution requires title-page confirmation",
        "document_id":identifier,"manifest":manifest_url,"year":1825,"expected_pages":count,
        "page_count":len(results),"status":"facsimiles only, not a reviewed transcription",
        "images":results,"failed_pages":sorted(errors,key=lambda r:r["page"])}
write_json(ROOT/"public"/"data"/f"russian-1825-{book}-provenance.json",record)
print(book,len(results),"/",count,"archived; partial successes retained")
if errors:raise SystemExit(2)
