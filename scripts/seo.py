"""Prerender all language editions and build social images from actual engravings."""
from pathlib import Path
import json,re,html,os,subprocess
from xml.etree import ElementTree as ET
from PIL import Image,ImageDraw,ImageFont,ImageOps

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/"dist"
BASE=os.environ.get("BASE_PATH","").rstrip("/")
ORIGIN="https://biblicalstories.dalmo.ai"
LANGS=("en","de","ru")
NAMES=dict(zip(LANGS,["104 Biblical Histories","104 Biblische Historien","104 Священные истории"]))
INTRO=dict(zip(LANGS,["Read Johann Hübner’s 104 illustrated Bible stories in English, German and Russian, with original 1768 engravings, questions, teachings and devotional reflections.","Johann Hübners 104 biblische Historien mit Originalkupferstichen von 1768, Fragen, Lehren und gottseligen Gedanken. Deutsch, Englisch und Russisch.","104 библейские истории Иоганна Гюбнера на русском, немецком и английском языках с гравюрами 1768 года, вопросами, нравоучениями и размышлениями."]))
LABELS={"en":["Comprehension Questions","Useful Teachings","Devotional Reflections","Latin","All stories","Edition"],"de":["Deutliche Fragen","Nützliche Lehren","Gottselige Gedancken","Lateinisch","Alle Historien","Edition"],"ru":["Вопросы","Полезныя нравоученія","Благочестивыя размышленія","Латинскій текстъ","Все истории","Издание"]}
def e(v):return html.escape(str(v),quote=True)
def route(l,i=None,edition=False):return f"/{l}/stories/{i:03d}/" if i else f"/{l}/edition/" if edition else "/" if l=="en" else f"/{l}/"
def href(l,i=None,edition=False):return BASE+route(l,i,edition)
def module(f,n):return json.loads((ROOT/"src"/f).read_text("utf-8").split("export const "+n+" = ",1)[1].strip().removesuffix(";"))
rows=[json.loads(line) for line in re.findall(r'^\s*(\[".*"\])(?:,|\];)\s*$',(ROOT/"src/catalog.js").read_text("utf-8"),re.M)]
assert len(rows)==104,len(rows)
records=dict(zip(LANGS,[module("englishFromGerman.js","englishFromGerman"),module("german1768.js","german1768"),module("russianHistorical.js","russianHistorical")]))
archive=json.loads((ROOT/"public/data/archive.json").read_text("utf-8"))["images"]
template=(DIST/"index.html").read_text("utf-8")
PAPER="#f4f2ec"; INK="#191916"; RED="#872f27"; MUTED="#5d6059"
def font(size,italic=False):
    for family in ("liberation2","liberation"):
        p=Path("/usr/share/fonts/truetype")/family/f"LiberationSerif-{'Italic' if italic else 'Regular'}.ttf"
        if p.exists():return ImageFont.truetype(str(p),size)
    p=Path("/usr/share/fonts/truetype/dejavu")/f"DejaVuSerif{'-Italic' if italic else ''}.ttf"
    if p.exists():return ImageFont.truetype(str(p),size)
    path=subprocess.check_output(["fc-match","-f","%{file}","serif:style="+("Italic" if italic else "Regular")],text=True).strip()
    return ImageFont.truetype(path,size)
def wrap(d,t,f,w):
    ls=[];line=""
    for word in t.split():
        c=(line+" "+word).strip()
        if line and d.textlength(c,font=f)>w:ls.append(line);line=word
        else:line=c
    return ls+[line]
def fit(d,t,w,n,size):
    for s in range(size,30,-1):
        f=font(s);ls=wrap(d,t,f,w)
        if len(ls)<=n and all(d.textlength(x,font=f)<=w for x in ls):return f,ls
    raise ValueError(t)
def plate(im,i,box):
    with Image.open(ROOT/"public/engravings"/f"{i:03d}.webp") as src:
        src=ImageOps.contain(src.convert("RGB"),(box[2],box[3]),Image.Resampling.LANCZOS)
        x=box[0]+(box[2]-src.width)//2;y=box[1]+(box[3]-src.height)//2
        im.paste(src,(x,y));ImageDraw.Draw(im).rectangle((x-1,y-1,x+src.width,y+src.height),outline="#777066")
def card(l,i=None):
    im=Image.new("RGB",(1200,630),PAPER);d=ImageDraw.Draw(im);d.rectangle((22,22,1177,607),outline="#b5aa98")
    x=70
    if i:
        plate(im,i,(722,43,435,544))
        title=rows[i-1][LANGS.index(l)]
        d.text((x,79),"Biblische Historien",font=font(29),fill=MUTED);d.line((x,137,x+58,137),fill=RED,width=3)
        f,ls=fit(d,title,595,4,74);y=177
        for line in ls:d.text((x,y),line,font=f,fill=INK);y+=int(f.size*1.06)
        d.text((x,515),"Johann Hübner",font=font(28,True),fill=MUTED)
    else:
        plate(im,13,(495,65,329,500));plate(im,100,(839,65,329,500))
        d.text((x,83),"Johann Hübner",font=font(30,True),fill=MUTED);d.text((x,141),"104",font=font(116),fill=RED)
        f,ls=fit(d,{"en":"Biblical Histories","de":"Biblische Historien","ru":"Священные истории"}[l],400,2,72);y=270
        for line in ls:d.text((x,y),line,font=f,fill=INK);y+=int(f.size*1.02)
        d.line((x,469,x+60,469),fill=RED,width=3)
        d.text((x,495),{"en":"Original engravings · 1768","de":"Originalkupferstiche · 1768","ru":"Гравюры · 1768"}[l],font=font(25),fill=MUTED)
        d.text((x,531),"EN  /  DE  /  RU",font=font(21),fill=MUTED)
    p=DIST/"social"/l/(f"{i:03d}.jpg" if i else "cover.jpg")
    p.parent.mkdir(parents=True,exist_ok=True);im.save(p,"JPEG",quality=88,optimize=True)
    with Image.open(p) as check:assert check.size==(1200,630)
def paras(v):return "".join("<p>"+e(re.sub(r"\s*\n\s*"," ",p))+"</p>" for p in re.split(r"\n\s*\n",v or "") if p.strip())
def verse(v):return e(v).replace("\n","<br>")
def story_body(l,i):
    w=records[l][str(i)];g=records["de"][str(i)];name=rows[i-1][LANGS.index(l)];ls=LABELS[l]
    q="".join('<li'+(f' value="{w["question_numbers"][j]}"' if "question_numbers" in w else "")+'>'+e(v)+"</li>" for j,v in enumerate(w["questions"]))
    latin=w.get("latin") or (g.get("latin") if l=="ru" else "")
    lt=("Latin · "+("Basel 1768" if g.get("supplemental_witness") else "Gießen 1768")) if l=="ru" and not w.get("latin") else ls[3]
    folios="".join(f'<button type="button" class="folio-btn" data-folio="{i}:{j}" aria-label="Page {e(v["label"])}"><img src="{e(BASE+v["image"])}" alt="Printed German page {e(v["label"])}" loading="lazy" width="500"></button>' for j,v in enumerate(archive[i-1].get("folios",[])))
    prev=f'<a href="{href(l,i-1)}" data-story="{i-1}" aria-label="Previous">←</a>' if i>1 else '<a aria-disabled="true">←</a>'
    nxt=f'<a href="{href(l,i+1)}" data-story="{i+1}" aria-label="Next">→</a>' if i<104 else '<a aria-disabled="true">→</a>'
    b=f'<div class="story-shell container"><nav class="story-toolbar" aria-label="Story navigation"><a class="back-link" href="{href(l)}" data-route="collection">← {ls[4]}</a><span class="story-progress">{i:03d} / 104</span><div class="story-nav">{prev}{nxt}</div></nav><article class="reader"><div class="reader-art"><figure class="figure-art"><button type="button" class="figure-enlarge" data-zoom="{i}" aria-label="Enlarge engraving"><img src="{BASE}/engravings/{i:03d}.webp?v=rectified-2" alt="{e(name)}" width="740" height="1130"></button></figure></div><div class="reader-text"><h1 class="chapter-title">{e(name)}</h1><div class="source-content" id="source-content"><div id="story-prose"><div class="edition-prose" lang="{l}"><p class="scripture-reference">{e(w["reference"])}</p><div class="chapter-narrative">{paras(w["narrative"])}</div><section class="reading-section"><h2>{ls[0]}</h2><ol>{q}</ol></section><section class="reading-section"><h2>{ls[1]}</h2>{paras(w.get("teaching_preamble"))}'+''.join("<p>"+verse(t)+"</p>" for t in w["teachings"])+'</section>'
    b+=f'<section class="reading-section"><h2>{ls[2]}</h2>'+(paras(w["reflection"]) if l=="ru" else '<p class="verse">'+verse(w["reflection"])+'</p>')+'</section>'
    if latin:b+=f'<section class="reading-section"><h2>{e(lt)}</h2><p class="verse" lang="la">{verse(latin)}</p></section>'
    b+='</div></div>'
    if folios:b+=f'<section class="original-pages"><div class="folios">{folios}</div></section>'
    b+='</div></div></article><nav class="reader-bottom" aria-label="Adjacent stories">'
    for other in (i-1,i+1):
        if 1<=other<=104:b+=f'<span><a href="{href(l,other)}" data-story="{other}">{e(rows[other-1][LANGS.index(l)])}</a></span>'
    return b+'</nav></div>'
def collection(l):
    plates="".join(f'<figure class="plate"><a class="plate-link" href="{href(l,i)}" data-story="{i}"><span class="plate-image"><img src="{BASE}/engravings/thumb/{i:03d}.webp?v=rectified-2" alt="{e(row[LANGS.index(l)])}" loading="{"eager" if i<9 else "lazy"}" width="370" height="585"></span><figcaption><span class="plate-number">{i:03d}</span><span class="plate-title">{e(row[LANGS.index(l)])}</span></figcaption></a></figure>' for i,row in enumerate(rows,1))
    return f'<section class="container catalogue"><div class="catalogue-head"><div><h1 class="catalogue-heading">104 Biblische Historien</h1><p class="catalogue-date">Johann Hübner · 1714</p></div></div><div class="plates" id="plates">{plates}</div></section>'
def render(l,i=None,edition=False):
    w=records[l].get(str(i));name=rows[i-1][LANGS.index(l)] if i else LABELS[l][5] if edition else NAMES[l]
    title=name+" — Johann Hübner"
    description=name+". "+w["reference"]+{"en":" Read Johann Hübner’s illustrated biblical history with comprehension questions, teachings and devotional reflection.","de":" Biblische Historie mit Originalkupferstich, Fragen, Lehren und gottseligen Gedanken.","ru":" Библейская история с гравюрой, вопросами, нравоучениями и размышлениями."}[l] if i else INTRO[l]
    canonical=ORIGIN+route(l,i,edition);image=ORIGIN+f"/social/{l}/"+(f"{i:03d}.jpg" if i else "cover.jpg")+"?v=rectified-2"
    body=story_body(l,i) if i else f'<section class="container about-page"><h1>Biblische Historien</h1><p>Johann Hübner · 1714</p><p>{e(INTRO[l])}</p><p>Gießen 1768 · Moscow 1825 · Basel 1768</p><a href="{href(l)}">{LABELS[l][4]}</a></section>' if edition else collection(l)
    result=template.replace('<html lang="en">',f'<html lang="{l}">').replace('<main id="main" tabindex="-1"></main>',f'<main id="main" tabindex="-1">{body}</main>')
    result=re.sub(r"<title>.*?</title>","<title>"+e(title)+"</title>",result)
    attrs={"description":description,"og:title":title,"og:description":description,"og:type":"article" if i else "website","og:url":canonical,"og:locale":{"en":"en_US","de":"de_DE","ru":"ru_RU"}[l],"og:image":image,"og:image:alt":name,"twitter:title":title,"twitter:description":description,"twitter:image":image,"twitter:image:alt":name}
    for key,val in attrs.items():
        result,n=re.subn(r'(<meta (?:name|property)="'+re.escape(key)+r'" content=")[^"]*(">)',lambda m:m[1]+e(val)+m[2],result);assert n==1,(key,n)
    result=re.sub(r'(<link rel="canonical" href=")[^"]*(">)',lambda m:m[1]+canonical+m[2],result)
    for code in (*LANGS,"x-default"):
        result=re.sub(r'(<link rel="alternate" hreflang="'+code+r'" href=")[^"]*(">)',lambda m:m[1]+ORIGIN+route("en" if code=="x-default" else code,i,edition)+m[2],result)
    book={"@type":"Book","name":"Biblische Historien","author":{"@type":"Person","name":"Johann Hübner"},"datePublished":"1714","url":ORIGIN+"/"}
    schema={"@context":"https://schema.org","@type":"Chapter" if i else "AboutPage" if edition else "CollectionPage","name":name,"url":canonical,"inLanguage":l,"description":description,"image":image}
    if i:schema.update(position=i,author=book["author"],isPartOf=book)
    else:schema["mainEntity"]={**book,"inLanguage":list(LANGS)}
    result=result.replace('<script type="application/ld+json" id="structured-data">{}</script>','<script type="application/ld+json" id="structured-data">'+json.dumps(schema,ensure_ascii=False).replace("<","\\u003c")+'</script>')
    result=result.replace(f'href="{BASE}/" data-route="collection"',f'href="{href(l)}" data-route="collection"').replace(f'href="{BASE}/?view=about"',f'href="{href(l,edition=True)}"')
    for code in LANGS:result=result.replace(f'data-lang="{code}" lang="{code}"',f'data-lang="{code}" lang="{code}" aria-pressed="{str(code==l).lower()}"')
    p=DIST/route(l,i,edition).lstrip("/")/"index.html";p.parent.mkdir(parents=True,exist_ok=True);p.write_text(result,"utf-8")
    return canonical
def main():
    urls=[]
    for l in LANGS:
        card(l);urls.append(render(l));urls.append(render(l,edition=True))
        for i in range(1,105):card(l,i);urls.append(render(l,i))
    ns="http://www.sitemaps.org/schemas/sitemap/0.9";ET.register_namespace("",ns);root=ET.Element("{"+ns+"}urlset")
    for url in urls:ET.SubElement(ET.SubElement(root,"{"+ns+"}url"),"{"+ns+"}loc").text=url
    ET.ElementTree(root).write(DIST/"sitemap.xml",encoding="utf-8",xml_declaration=True)
    (DIST/"robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: "+ORIGIN+"/sitemap.xml\n","utf-8")
    assert len(urls)==318 and len(set(urls))==318
    assert len(list((DIST/"social").rglob("*.jpg")))==315
    print("SEO PASS: 318 localized crawlable HTML pages, 315 JPEG share cards, sitemap and robots.txt")
if __name__=="__main__":main()
