#!/usr/bin/env python3
"""Page OCR of acquired historical Russian facsimiles, NOT publishable text."""
import argparse, hashlib, json, os, subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument("--book",choices=["ot","nt"],required=True)
p.add_argument("--model",required=True,type=Path)
p.add_argument("--workers",type=int,default=3)
a=p.parse_args()
model=a.model.resolve()
model_sha=hashlib.sha256(model.read_bytes()).hexdigest()
lang=model.stem
source=ROOT/"public"/"russian-1825-pages"/a.book
out=ROOT/"sources"/"russian-1825-ocr"/a.book
out.mkdir(parents=True,exist_ok=True)
pages=sorted(source.glob("*.webp"))
assert pages,"No archived pages"
env=dict(os.environ,OMP_THREAD_LIMIT="1")
def job(page):
    name=page.stem
    receipt=out/(name+".json")
    txt=out/(name+".txt")
    tsv=out/(name+".tsv")
    sha=hashlib.sha256(page.read_bytes()).hexdigest()
    if receipt.exists() and txt.exists() and tsv.exists():
        r=json.loads(receipt.read_text("utf8"))
        if r["image_sha256"]==sha and r["model_sha256"]==model_sha and r["text_sha256"]==hashlib.sha256(txt.read_bytes()).hexdigest():return r
    base=out/(name+".pending")
    subprocess.run(["tesseract",str(page),str(base),"--tessdata-dir",str(model.parent),"-l",lang,"--psm","3","txt","tsv"],check=True,timeout=180,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    (out/(name+".pending.txt")).replace(txt)
    (out/(name+".pending.tsv")).replace(tsv)
    r={"page":int(name),"image":str(page.relative_to(ROOT)),"image_sha256":sha,"model_sha256":model_sha,
       "model":"https://github.com/AButon-8/iskra_ocr (Apache-2.0; pre-reform Russian; trained on Iskra 1900–1905)",
       "text_sha256":hashlib.sha256(txt.read_bytes()).hexdigest(),"characters":len(txt.read_text("utf8")),"status":"unreviewed historical OCR"}
    receipt.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n","utf8")
    return r
records=[];errors=[]
with ThreadPoolExecutor(max_workers=a.workers) as pool:
    tasks={pool.submit(job,page):page for page in pages}
    for f in as_completed(tasks):
        try:records.append(f.result())
        except Exception as e:errors.append({"page":tasks[f].stem,"error":str(e)})
        if (len(records)+len(errors))%20==0:print(a.book,len(records),"/",len(pages),"OCR pages",flush=True)
(out/"manifest.json").write_text(json.dumps({"book":a.book,"source_pages":len(pages),"ocr_pages":len(records),"status":"unreviewed","records":sorted(records,key=lambda r:r["page"]),"errors":errors},indent=2)+"\n","utf8")
print(a.book,"OCR",len(records),"/",len(pages),"pages; not proofread")
if errors:raise SystemExit(2)
