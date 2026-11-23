#!/usr/bin/env python3
"""Recover 104 Hübner chapters from the complete Zürich c.1775 public-domain OCR.

Edition distinction:
de = uncorrected Zürich c.1775 historical German OCR, with inferred chapter boundaries;
en/ru = NEW machine translations of that German witness, not historical English or Russian.
The translation source is always saved verbatim and public-domain edition cited.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
import difflib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.request
import urllib.parse
import urllib.error

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"public"/"data"
OUTPUT=ROOT/"public"/"texts"
ORIGINAL=(DATA/"german-ocr.txt").read_text(encoding="utf-8")
SOURCE_URL="https://www.e-rara.ch/zuz/doi/10.3931/e-rara-85573"
HEADERS={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0 Safari/537.36"}
TRANSLATION="https://clients5.google.com/translate_a/t"

def parse_numeral(s):
    if s.isdigit():
        n=int(s)
        return n if 1<=n<=52 else 0
    s=s.upper().replace("L", "L").replace(" ", "")
    # Fraktur OCR commonly reads uppercase Roman I as lowercase l.
    # Preserve L before V/X in XL etc; tolerate the book's numeration.
    for v in (("XlV","XIV"),("XVlll","XVIII"),("Xil","XII")):
        s=s.replace(v[0].upper(),v[1])
    if not re.fullmatch(r"[IVXLCDM]+",s):return 0
    d={"I":1,"V":5,"X":10,"L":50,"C":100,"D":500,"M":1000}
    total=0;prior=0
    for c in s[::-1]:
        val=d[c];total+=-val if val<prior else val;prior=val
    return total if 1<=total<=52 else 0

def candidates(text,start,end):
    # Restrict matching to actual bibliographic heading shapes.
    # OCR page headers create duplicates; the global alignment below
    # filters them against other chapters and local source structure.
    rx=re.compile(r"\bDie\s+([IVXLCDMivxlcdm\d]{1,7})\s*[.\-:]?\s+Historie\b",re.I)
    hits={}
    for m in rx.finditer(text,start,end):
        numeral=m.group(1)
        n=parse_numeral(numeral)
        if not n:continue
        hits.setdefault(n,[]).append({
            "pos":m.start(),
            "roman":not numeral.isdigit(),
            "context":text[m.end():m.end()+110],
            "raw":m.group(0)
        })
    return hits

def boundaries(text,start,end,book):
    matches=candidates(text,start,end)
    print(f"INDEX {book}: {sum(map(len,matches.values()))} heading candidates, "+
          f"{len(matches)}/52 distinct numbers",flush=True)
    # Approximate positions are only a tie-breaker for multiple numbered page headers.
    # Prefer the earliest heading for a chapter, unless it would precede chapter n-1.
    anchors={1:start}
    for n in range(2,53):
        earlier=anchors[max(anchors)]
        pool=[m for m in matches.get(n,[]) if m["pos"]>earlier+650]
        if pool:
            romans=[m for m in pool if m["roman"] and
                    m["pos"] < earlier+18000]
            choose=(romans or pool)[0]
            anchors[n]=choose["pos"]
    # OCR may misread "49" as "42" in a running page header.
    # Discard anchors that leave implausibly little space for several missing
    # stories and that follow an unusually large preceding gap.
    known=sorted(anchors)
    for n in known[1:-1]:
        below=max(k for k in known if k<n)
        above=min(k for k in known if k>n)
        before=(anchors[n]-anchors[below])/(n-below)
        after=(anchors[above]-anchors[n])/(above-n)
        if before>9000 and after<900 and above-n>=2:
            print("REJECT FALSE OCR HEADING",book,n,anchors[n],
                  "previous-per-chapter",round(before),"next-per-chapter",round(after),flush=True)
            del anchors[n]
    # Fill missing numbers by interpolation between surviving source headings.
    # The OCR text is partitioned without creating or omitting content.
    found=sorted(anchors)
    missing=[i for i in range(1,53) if i not in anchors]
    for i in missing:
        low=max(n for n in found if n<i)
        high=min((n for n in found if n>i),default=53)
        l=anchors[low]
        h=anchors.get(high,end)
        anchors[i]=int(l+(h-l)*(i-low)/(high-low))
    ordered=[anchors[i] for i in range(1,53)]+[end]
    if any(ordered[i]>=ordered[i+1] for i in range(52)):
        raise AssertionError(f"Nonmonotonic {book} story partition: "+
                             str([(i,ordered[i],ordered[i+1]) for i in range(52) if ordered[i]>=ordered[i+1]]))
    lengths=[ordered[i+1]-ordered[i] for i in range(52)]
    if min(lengths)<350:
        raise AssertionError(f"{book}: unnaturally short chapter partition: "+str(sorted(lengths)[:8]))
    print(f"PARTITION {book}: 52 chapters, {len(missing)} inferred starts; "+
          f"length range {min(lengths)}..{max(lengths)}; first/last {ordered[0]}..{ordered[-1]}",flush=True)
    return [{"text":text[ordered[i]:ordered[i+1]].strip(),
             "inferred_boundary":i+1 in missing,
             "char_range":[ordered[i],ordered[i+1]],
             "chapter":i+1} for i in range(52)]

def source_104():
    text=ORIGINAL
    old=text.index("Die 1. Historie.")
    new=text.index("Die I. Historie.",old+1000)
    # An advertisement for other books follows the 52nd New Testament history.
    # It is not part of Hübner's 104 biblical histories.
    end=text.find("NB. ES sind des Hm.",new)
    if end<0:end=text.find("WagnerS Biblische Historien",new)
    if end<0:end=len(text)-1800
    # The last story ends before the bookseller's advertisement (see source).
    if end<new+100000:raise AssertionError("Unexpected New Testament section")
    result=boundaries(text,old,new,"OT")+boundaries(text,new,end,"NT")
    assert len(result)==104
    # Preserve full text of each section, including questions, lessons, poetry.
    assert "".join(x["text"] for x in result).replace("\n","").replace(" ","")[:150] in \
           text[old:end].replace("\n","").replace(" ","")
    return result

def clean_for_translation(value):
    s=value.replace("\u00ad","").replace("ſ","s")
    s=re.sub(r"(?<=\w)-\s*\n\s*(?=\w)","",s)
    s=re.sub(r"\n{3,}","\n\n",s)
    return s.strip()

def translate_segment(body, lang):
    encoded=urllib.parse.urlencode({"client":"dict-chrome-ex","sl":"de","tl":lang,"q":body})
    if len(encoded)>12000:raise AssertionError("Oversized translation request")
    url=TRANSLATION+"?"+encoded
    last=None
    for i in range(7):
        try:
            req=urllib.request.Request(url,headers=HEADERS)
            with urllib.request.urlopen(req,timeout=38) as r: data=json.load(r)
            if isinstance(data,list) and data and isinstance(data[0],str):
                value=data[0].strip()
            elif isinstance(data,list):
                value="".join(str(x[0]) for x in data[0] if x and x[0]).strip()
            else:raise ValueError("Unexpected translation response")
            if len(value)<max(20,len(body)*.13):raise ValueError("Truncated translated text")
            return value
        except (urllib.error.URLError,ValueError,IndexError,KeyError,TimeoutError) as e:
            last=e
            time.sleep(min(20,2.2*(i+1))+(i%3)*.25)
    raise RuntimeError(f"Cannot translate {lang}: {last}")

def chunks(s, cap=2500):
    s=clean_for_translation(s)
    result=[]
    while len(s)>cap:
        x=s[:cap]
        pos=max([x.rfind(c) for c in ("\n\n","\n",". ","? ","! ","; ",", "," ")]
                or [-1])
        if pos<cap*.5:pos=cap-1
        result.append(s[:pos+1].strip());s=s[pos+1:].lstrip()
    if s:result.append(s)
    return result

def translation(s,lang):
    parts=chunks(s)
    translated=[]
    for part in parts: translated.append(translate_segment(part,lang))
    return "\n\n".join(translated)

def produce(item):
    i,source=item
    path=OUTPUT/f"{i:03d}.json"
    if path.exists():
        try:
            record=json.loads(path.read_text("utf-8"))
            if record.get("id")==i and all(len(record.get(k,{}).get("text",""))>120
                                         for k in ("de","en","ru")):
                return i,record,"cached"
        except (ValueError,KeyError,TypeError):pass
    record={"id":i,
            "de":{"text":source["text"],
                  "kind":"uncorrected-original-german-OCR",
                  "edition":"Zürich ca. 1775",
                  "source":SOURCE_URL},
            "en":{"text":"","kind":"modern-machine-translation-of-Zürich-German-OCR","source":SOURCE_URL},
            "ru":{"text":"","kind":"modern-machine-translation-of-Zürich-German-OCR","source":SOURCE_URL},
            "editorial":{"source_character_range":source["char_range"],
                         "source_heading_inferred":source["inferred_boundary"],
                         "proofread":False}}
    for lang in ("en","ru"):
        record[lang]["text"]=translation(source["text"],lang)
    if any(len(record[k]["text"])<120 for k in ("de","en","ru")):
        raise AssertionError(f"Story {i} has a too-short language version")
    path.write_text(json.dumps(record,ensure_ascii=False,separators=(",",":")),"utf-8")
    return i,record,"new"

def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    segments=source_104()
    (DATA/"zurich-segmentation.json").write_text(
      json.dumps({"edition":"Zürich ca. 1775","source":SOURCE_URL,
                  "chapters":[{"id":i+1,"char_range":z["char_range"],
                               "source_heading_inferred":z["inferred_boundary"]}
                              for i,z in enumerate(segments)]},indent=2),encoding="utf-8")
    if os.environ.get("SEGMENT_ONLY"):
        print("SEGMENTS VALID: 104 public domain chapters, total chars",sum(len(s["text"]) for s in segments),flush=True)
        for i in [1,2,7,8,25,50,51,52,53,54,100,103,104]:
            x=segments[i-1]
            print("SEGMENT",i,len(x["text"]),"inferred",x["inferred_boundary"],
                  repr(x["text"][:160]),flush=True)
        return
    completed=[];failed=[]
    print("START TRANSLATION",len(segments),"full German chapters",flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs={pool.submit(produce,(i+1,x)):i+1 for i,x in enumerate(segments)}
        for task in as_completed(jobs):
            i=jobs[task]
            try:
                n,record,status=task.result()
                completed.append(n)
                print("COMPLETE",n,status,"chars",
                      *(len(record[k]["text"]) for k in ("de","en","ru")),flush=True)
            except Exception as e:
                failed.append((i,str(e)))
                print("FAILED",i,str(e),flush=True)
    coverage={"total":104,"complete":len(completed),
              "source":"Zürich ca.1775 OCR (NOT the Giessen 1768 edition)",
              "english":"Modern machine translation from uncorrected German OCR",
              "russian":"Modern machine translation from uncorrected German OCR",
              "proofread":False,"failed":failed}
    (DATA/"text-coverage.json").write_text(json.dumps(coverage,indent=2),"utf-8")
    print("COVERAGE",len(completed),"/104; errors",len(failed),flush=True)
    if failed:raise RuntimeError("Translations incomplete: "+str(failed)[:1000])
    assert sorted(completed)==list(range(1,105))
    print("PASS 104 complete OCR chapters in DE + translated EN/RU",flush=True)

if __name__=="__main__":main()
