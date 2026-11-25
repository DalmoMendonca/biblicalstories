#!/usr/bin/env python3
"""Extract existing ALTO layout, without running OCR or inventing words.

The raw library XML is authoritative for these draft records. Every line
retains its coordinates, block and page. This is an editorial workspace,
not an authenticated reader edition.
"""
from pathlib import Path
import gzip, hashlib, json, re, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
S=ROOT/"sources/library-text/zurich-alto.xml.gz"
D=ROOT/"sources/zurich-layout"
D.mkdir(parents=True,exist_ok=True)
raw=gzip.decompress(S.read_bytes())
receipt=json.loads(S.with_name("zurich-alto.json").read_text("utf8"))
assert hashlib.sha256(raw).hexdigest()==receipt["sha256"]
root=ET.fromstring(raw)
def tag(x):return x.tag.rsplit("}",1)[-1]
def box(x):
    return {k.lower():float(x.attrib[k]) for k in ("HPOS","VPOS","WIDTH","HEIGHT") if k in x.attrib}
def page_record(page,i):
    blocks=[]
    for b in page.iter():
        if tag(b)!="TextBlock":continue
        lines=[]
        for line in b.iter():
            if tag(line)!="TextLine":continue
            words=[w.attrib.get("CONTENT","") for w in line if tag(w)=="String"]
            if not words:continue
            lines.append({"id":line.get("ID"),**box(line),"text":" ".join(words)})
        if lines:blocks.append({"id":b.get("ID"),**box(b),"lines":lines})
    return {"page":i,"id":page.get("ID"),**box(page),"blocks":blocks}
pages=[page_record(p,i) for i,p in enumerate((p for p in root.iter() if tag(p)=="Page"),1)]
assert len(pages)>100, f"Unexpectedly small ALTO corpus: {len(pages)} pages"
total=sum(len(b["lines"]) for p in pages for b in p["blocks"])
assert total>1000,total
for p in pages:
    (D/f'{p["page"]:03d}.json').write_text(json.dumps(p,ensure_ascii=False,separators=(",",":"))+"\n","utf8")
# Preserve source order and layout; do not infer a reading order from font
# size or classify running headers as content automatically.
(D/"manifest.json").write_text(json.dumps({"source":receipt,"pages":len(pages),"lines":total,"nonempty_pages":sum(bool(p["blocks"]) for p in pages),"kind":"existing-library-ocr-layout-unreviewed","page_index":[{"page":p["page"],"id":p["id"],"blocks":len(p["blocks"]),"lines":sum(len(b["lines"]) for b in p["blocks"])} for p in pages]},indent=2)+"\n","utf8")
print("Extracted",len(pages),"pages and",total,"source OCR lines, preserving positions")
