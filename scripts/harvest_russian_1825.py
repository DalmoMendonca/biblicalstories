#!/usr/bin/env python3
"""Archive public-domain 1825 Russian Hübner page facsimiles from rusneb.

Source is the National Electronic Library's open material-pages manifest;
this imports historical photographs, not purported proofread transcriptions.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
from io import BytesIO
from pathlib import Path
from PIL import Image,ImageOps
import argparse,hashlib,json,time,urllib.error,urllib.request

ROOT=Path(__file__).resolve().parents[1]
BASE='https://kp.rusneb.ru/'
BOOKS={'ot':'5fcf8bb3991f3b91423439b5',
       'nt':'5fcf8bb3991f3b91423439ad'}
COUNTS={'ot':260,'nt':196}
parser=argparse.ArgumentParser()
parser.add_argument('--book',choices=list(BOOKS),required=True)
parser.add_argument('--workers',type=int,default=6)
args=parser.parse_args()
book=args.book
identifier=BOOKS[book]
dest=ROOT/'public'/'russian-1825-pages'/book
dest.mkdir(parents=True,exist_ok=True)
def request(url):
    last=None
    for n in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; public-domain textual archive)',
                                                'Accept':'image/jpeg,application/json,*/*'})
            with urllib.request.urlopen(req,timeout=20) as r:
                body=r.read()
                if r.status!=200:raise RuntimeError(f'Status {r.status}')
                return body
        except Exception as e:
            last=e
            time.sleep(min(8,1.2*(n+1)))
    raise RuntimeError(f'Cannot fetch original public scan {url}: {last}')
# The archive's metadata endpoint is occasionally slow or unavailable, even while
# the public page-image URLs work. The established manifests identify the 1..N
# sequence; verify every image directly if manifest retrieval times out.
try:
    manifest=json.loads(request(BASE+f'api/v1/materials/{identifier}/pages').decode('utf8'))
    assert len(manifest)==COUNTS[book], (len(manifest),COUNTS[book])
    print('Retrieved original',book,'page manifest',flush=True)
except Exception as exc:
    print('Metadata timeout: checking the verified sequential image paths individually:',str(exc)[:120],flush=True)
    manifest=[{'original':f'attachments_new/attachment/{identifier}/preview-page-{i}.jpg'}
              for i in range(1,COUNTS[book]+1)]
def scan(page):
    number,data=page
    url=BASE+data['original']
    raw=request(url)
    if len(raw)<40000:raise RuntimeError(f'{book} page {number} unusually short: {len(raw)}')
    with Image.open(BytesIO(raw)) as im:
        im.load()
        w,h=im.size
        if min(w,h)<500:raise RuntimeError(f'{book} page {number}: image is too small {w} x {h}')
        im=ImageOps.exif_transpose(im).convert('RGB')
        output=dest/(f'{number:03d}.webp')
        im.save(output,'WEBP',quality=83,method=4)
    return {'page':number,'image':f'/russian-1825-pages/{book}/{number:03d}.webp',
            'source':url,'source_sha256':hashlib.sha256(raw).hexdigest(),'source_bytes':len(raw),
            'width':w,'height':h}
results=[]
with ThreadPoolExecutor(max_workers=args.workers) as pool:
    tasks={pool.submit(scan,(n,page)):n for n,page in enumerate(manifest,1)}
    for f in as_completed(tasks):
        result=f.result()
        results.append(result)
        if len(results)%20==0 or len(results)==len(manifest):
            print(f'{book} {len(results)}/{len(manifest)} source scans archived',flush=True)
assert len(results)==COUNTS[book]
results.sort(key=lambda item:item['page'])
record={'edition':'Сто четыре священныя истории, Москва, 1825; Hübner / Vasily Bogorodsky translation',
        'witness':'Old Testament, part 1' if book=='ot' else 'New Testament, part 2',
        'archive':'Национальная электронная библиотека — Книжные памятники',
        'document_id':identifier,
        'manifest':BASE+f'api/v1/materials/{identifier}/pages',
        'year':1825,
        'page_count':len(results),
        'status':'ORIGINAL PUBLIC-DOMAIN FACSIMILES, NOT PROOFREAD TEXT; DIFFERENT EDITION FROM 1815',
        'images':results}
index=ROOT/'public'/'data'/f'russian-1825-{book}-provenance.json'
index.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf8')
print(f'PASS {book}: {len(results)} full-resolution source page images archived with provenance',flush=True)
