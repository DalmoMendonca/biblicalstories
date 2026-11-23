#!/usr/bin/env python3
"""Generate source-linked draft Fraktur OCR, never a verified transcription.

Each output is a verbatim neural OCR prediction for one source page.
No guessed story boundaries, no machine translation and no claims of proofread accuracy.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "public" / "folios"
DEST = ROOT / "public" / "ocr-1768"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",required=True)
    p.add_argument("--shard",type=int,required=True)
    p.add_argument("--shards",type=int,default=8)
    p.add_argument("--workers",type=int,default=2)
    a=p.parse_args()
    assert 0<=a.shard<a.shards
    manifest=json.loads((ROOT/"public"/"data"/"archive.json").read_text("utf8"))
    expected=[(f"{item['id']:03d}-{i:02d}",folio)
              for item in manifest["images"] for i,folio in enumerate(item.get("folios",[]),1)]
    assert len(expected)==324,(len(expected),"unexpected archive count")
    targets=[x for i,x in enumerate(expected) if i%a.shards==a.shard]
    DEST.mkdir(parents=True,exist_ok=True)
    print(f"Shard {a.shard}/{a.shards} has {len(targets)} authentic German facsimiles",flush=True)
    def run(item):
        key,folio=item
        source=SOURCE/(key+".webp")
        dest=DEST/(key+".txt")
        assert source.exists(),source
        with __import__("tempfile").TemporaryDirectory() as td:
            tmp=Path(td)/(key+".txt")
            result=subprocess.run(["kraken","-i",str(source),str(tmp),"segment","-bl","ocr","-m",a.model],
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=200,
                env={**os.environ,"OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1","MKL_NUM_THREADS":"1"})
            if result.returncode:raise RuntimeError(f"{key}: {result.stdout[-1200:]}")
            text=tmp.read_text("utf8").strip()
            if len(text)<80:raise RuntimeError(f"{key}: suspiciously short OCR ({len(text)})")
            dest.write_text(text+"\n","utf8")
        return key,len(text)
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures=[pool.submit(run,x) for x in targets]
        for n,f in enumerate(as_completed(futures),1):
            key,length=f.result()
            print(f"{a.shard} {n}/{len(targets)}: {key} -> {length} characters",flush=True)
    print(f"SUCCESS shard {a.shard}: {len(targets)} source-linked, unproofread page drafts",flush=True)

if __name__=="__main__":
    main()
