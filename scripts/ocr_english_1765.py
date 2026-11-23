#!/usr/bin/env python3
"""Produce UNPROOFREAD OCR of the original 1765 printed English columns.

Printed source: British Library 1765 polyglot, accessed as authenticated
page images through Google Books. This is not a critical edition.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from PIL import Image,ImageOps,ImageEnhance,ImageFilter
import subprocess,os, tempfile, json, statistics

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"public"/"english-1765-pages"
OUT=ROOT/"public"/"english-1765-ocr"
OUT.mkdir(parents=True,exist_ok=True)

def recognize(n):
    name=f"PA{n}"
    source=SOURCE/(name+".jpg")
    if not source.is_file(): raise RuntimeError("Missing primary source image "+str(source))
    with Image.open(source) as im:
        w,h=im.size
        # Three columns: French, German and English (right). Keep English only.
        crop=im.crop((round(w*.687),round(h*.055),round(w*.984),round(h*.94)))
        crop=ImageOps.grayscale(crop)
        crop=ImageOps.autocontrast(crop,cutoff=0.5)
        crop=crop.resize((crop.width*3,crop.height*3),Image.Resampling.LANCZOS)
        crop=ImageEnhance.Contrast(crop).enhance(1.4)
        with tempfile.TemporaryDirectory() as td:
            fp=Path(td)/(name+".png")
            crop.save(fp)
            cmd=["tesseract",str(fp),"stdout","-l","eng","--oem","1","--psm","6"]
            r=subprocess.run(cmd,capture_output=True,text=True,timeout=50,
                             env={**os.environ,"OMP_THREAD_LIMIT":"1","OMP_NUM_THREADS":"1"})
            if r.returncode: raise RuntimeError(name+": "+r.stderr[:500])
            content=r.stdout.strip()
    (OUT/(name+".txt")).write_text(content+"\n","utf8")
    return name,len(content)

with ThreadPoolExecutor(max_workers=4) as pool:
    futures=[pool.submit(recognize,n) for n in range(1,252)]
    results=[f.result() for f in as_completed(futures)]
lengths=[length for _,length in results]
assert len(results)==251
assert len([n for n,v in results if v>80])>=230, ("OCR too many blank pages",sorted(lengths)[:12])
metadata={
 'edition':'Hübner: Hubner\'s Historys of the Bible (Hamburg, 1765); trilingual English/French/German',
 'source_images':'public/english-1765-pages/PA{page}.jpg',
 'printed_language':'Original historical English wording from the RIGHT column',
 'method':'Tesseract English OCR on the rightmost third of each source scan',
 'page_count':251,
 'status':'UNCORRECTED OCR; NOT VERIFIED or manually proofread',
 'coverage_warning':'No automatic story segmentation or proofread historical accuracy is claimed.',
 'ocr_characters_total':sum(lengths),
 'ocr_page_nonempty':len([n for n,v in results if v>80]),
 'sample_characters':{str(k):dict(results)[f'PA{k}'] for k in (10,100,240)}
}
(ROOT/"public"/"data"/"english-1765-ocr-provenance.json").write_text(
    json.dumps(metadata,ensure_ascii=False,indent=2)+"\n","utf8")
print('PASS',len(results),'original English page drafts',sum(lengths),'characters',flush=True)
for k in [10,100,240]:
    print('== SOURCE PA'+str(k)+' ==',flush=True)
    print((OUT/(f'PA{k}.txt')).read_text('utf8')[:2000],flush=True)
