#!/usr/bin/env python3
"""Acquire library-provided text layers, without generating OCR or translations.

Sources are unreviewed archival witnesses. This runner never publishes them as
completed reader content. Downloaded bytes are hashed and retained for restart.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor
import gzip, hashlib, json, re, time, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"sources"/"library-text"
DEST.mkdir(parents=True,exist_ok=True)
MAX=35*1024*1024
UA="Mozilla/5.0 (compatible; historical public-domain text archive)"
SOURCES={
    "zurich-alto":"https://www.e-rara.ch/zuz/download/ftpack/alto/24283792",
    "tuebingen-tei":"https://opendigi.ub.uni-tuebingen.de/opendigi/Gi1824ab",
    "russian-1825-ot":"https://kp.rusneb.ru/item/reader/sto-chetyre-svyashchennyya-istorii-pyatdesyat-dve-svyashchennyya-istorii-iz-vethago-zaveta--ch1",
    "russian-1825-nt":"https://kp.rusneb.ru/item/reader/sto-chetyre-svyashchennyya-istorii-pyatdesyat-dve-svyashchennyya-istorii-iz-novago-zaveta--ch2",
    "russian-1812-ot":"https://search.rsl.ru/ru/record/01008044637",
    "russian-1835":"https://rusneb.ru/catalog/000199_000009_003570134/",
    "russian-1859":"https://rusneb.ru/catalog/000199_000009_003564451/",
}
def get(url):
    if urlparse(url).scheme!="https": raise ValueError("Only HTTPS public endpoints")
    last=None
    for n in range(2):
        try:
            with urlopen(Request(url,headers={"User-Agent":UA,"Accept":"*/*"}),timeout=22) as resp:
                data=resp.read(MAX+1)
                if len(data)>MAX: raise ValueError("Source exceeds maximum text package size")
                return data,resp.geturl(),resp.headers.get("Content-Type","")
        except Exception as exc:
            last=exc
            if n==0:time.sleep(1)
    raise RuntimeError(str(last))
class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.cur=None
    def handle_starttag(self,tag,attrs):
        if tag=="a":self.cur=[dict(attrs).get("href",""),""]
    def handle_data(self,data):
        if self.cur is not None:self.cur[1]+=data
    def handle_endtag(self,tag):
        if tag=="a" and self.cur is not None:
            self.links.append(self.cur);self.cur=None
def xml_payload(raw):
    try:
        root=ET.fromstring(raw)
        tags={x.tag.rsplit("}",1)[-1].lower() for x in root.iter()}
        if tags.intersection({"alto","tei","teicorpus","page","textline","string"}):
            if len(raw)<20000:raise ValueError("Too short for a full-volume witness")
            return sorted(tags.intersection({"alto","tei","teicorpus","page","textline","string"}))
    except ET.ParseError:pass
    return None
def acquire(item):
    key,url=item
    target=DEST/(key+".xml.gz")
    receipt=DEST/(key+".json")
    if target.exists() and receipt.exists():
        rec=json.loads(receipt.read_text("utf8"))
        raw=gzip.decompress(target.read_bytes())
        if rec.get("status")=="acquired" and hashlib.sha256(raw).hexdigest()==rec.get("sha256") and xml_payload(raw):
            return rec
    result={"source":url,"status":"unavailable","attempts":[]}
    try:
        data,final,mime=get(url)
        tags=xml_payload(data)
        if not tags:
            parser=Links();parser.feed(data.decode("utf8",errors="replace"))
            candidates=[]
            for href,label in parser.links:
                if not href:continue
                if re.search(r"\b(tei|alto|ocr|volltext|full.?text)\b",href+" "+label,re.I):
                    candidate=urljoin(final,href)
                    if urlparse(candidate).scheme=="https" and candidate not in candidates:candidates.append(candidate)
            result["discovered_links"]=candidates
            for candidate in candidates[:12]:
                try:
                    b,u,m=get(candidate);t=xml_payload(b)
                    result["attempts"].append({"url":candidate,"bytes":len(b),"type":m,"recognized":bool(t)})
                    if t:data,final,mime,tags=b,u,m,t;break
                except Exception as exc:result["attempts"].append({"url":candidate,"error":str(exc)})
        if tags:
            target.write_bytes(gzip.compress(data,mtime=0))
            result.update(status="acquired",download_url=final,content_type=mime,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),xml_types=tags)
        else:
            result.update(status="no_complete_xml_text_found",content_type=mime,bytes=len(data))
    except Exception as exc:result["error"]=str(exc)
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf8")
    return result
if __name__=="__main__":
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(acquire,SOURCES.items()))
    print(json.dumps(results,ensure_ascii=False,indent=2))
