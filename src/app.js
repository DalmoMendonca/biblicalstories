import { stories } from "./catalog.js";
import { english1765 } from "./english1765.js";
import { german1768 } from "./german1768.js";
import { englishFromGerman } from "./englishFromGerman.js";
import { russianHistorical } from "./russianHistorical.js";

const main = document.querySelector("#main");
const lightbox = document.querySelector("#lightbox");
const lightboxImage = document.querySelector("#lightbox-image");
const languages = ["en","de","ru"];
const siteBase=new URL("../",import.meta.url).pathname.replace(/\/$/,"");
const origin="https://biblicalstories.dalmo.ai";
function route(){
 const p=location.pathname.slice(siteBase.length).replace(/^\/+|\/+$/g,"").split("/");
 const q=new URLSearchParams(location.search);
 if(!p[0]&&q.has("view"))return {view:q.get("view"),lang:null,id:Number(q.get("id"))||null};
 if(languages.includes(p[0]))return {view:p[1]==="stories"?"story":p[1]==="edition"?"about":"collection",lang:p[0],id:p[1]==="stories"?Number(p[2]):Number(q.get("id"))||null};
 return {view:"collection",lang:"en",id:null};
}
const collectionPath=lang=>siteBase+(lang==="en"?"/":"/"+lang+"/");
const storyPath=(lang,id)=>siteBase+"/"+lang+"/stories/"+String(id).padStart(3,"0")+"/";
const editionPath=(lang,id=null)=>siteBase+"/"+lang+"/edition/"+(id?"?id="+id:"");
const text = {
  en:{all:"All 104",old:"Old Testament",new:"New Testament",search:"Search",back:"All stories",folio:"German source pages · 1768",none:"The historical English text for this story has not yet been transcribed.",edition:"English · Hamburg, 1765",book:"1765 historical edition",original:"Original scan",about:"Edition"},
  de:{all:"Alle 104",old:"Altes Testament",new:"Neues Testament",search:"Suchen",back:"Alle Historien",folio:"Originalseiten",none:"Der historische Text ist noch nicht geprüft und transkribiert.",edition:"Deutsch · Gießen, 1768 · unkorrigierte OCR",book:"Originalausgabe",original:"Originalscan",about:"Edition"},
  ru:{all:"Все 104",old:"Ветхий Завет",new:"Новый Завет",search:"Поиск",back:"Все истории",folio:"Немецкие страницы · 1768",none:"Подлинный русский текст пока не проверен и не расшифрован.",edition:"Русский · Москва, 1825",book:"Цифровая копия · 1825",original:"Оригинальный скан",about:"Издание"}
};
const sourceEnglish = "https://books.google.com/books?id=5elUAAAAcAAJ";
const sourceRussian1815 = "https://search.rsl.ru/ru/search#q=%D0%93%D0%B8%D0%B1%D0%BD%D0%B5%D1%80%201815";
const sourceRussian1825 = [
  "https://kp.rusneb.ru/item/material/5fcf8bb3991f3b91423439b5",
  "https://kp.rusneb.ru/item/material/sto-chetyre-svyashchennyya-istorii-pyatdesyat-dve-svyashchennyya-istorii-iz-novago-zaveta--ch2"
];
const sourceGerman = "https://digi.ub.uni-heidelberg.de/diglit/huebner1768";
const stored = (key, fallback) => { try{return localStorage.getItem(key) ?? fallback;}catch{return fallback;} };
const save = (key, value) => { try{localStorage.setItem(key,value);}catch{} };
const s = {
  lang: route().lang||(languages.includes(stored("huebner-language","en")) ? stored("huebner-language","en") : "en"),
  filter: "all", search: "", plates: [], byId: new Map()
};
const esc = (value) => String(value ?? "").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const item = id => s.byId.get(id);
const story = id => stories[id-1];
const title = id => story(id)?.[s.lang] || "";
const messages = () => text[s.lang];
const number = n => String(n).padStart(3,"0");
const url = id => storyPath(s.lang,id);
const view = () => route().view;
const idParam = () => Math.min(104,Math.max(1,route().id||1));

function updateLanguage(){
  document.documentElement.lang=s.lang;
  document.querySelectorAll("[data-lang]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.lang===s.lang)));
  const about=document.querySelector("#about-link");
  about.textContent=messages().about;
  const current=view()==="story"||view()==="about"&&route().id;
  about.href=editionPath(s.lang,current?idParam():null);
  document.querySelector(".identity").href=collectionPath(s.lang);
  if(current)about.dataset.editionStory=idParam();else delete about.dataset.editionStory;
}
function navigate(dest,id=null){
  const path=dest==="story"?url(id??1):dest==="about"?editionPath(s.lang,id):collectionPath(s.lang);
  history.pushState({},"",path);
  render();
  scrollTo({top:0,behavior:"instant"});
}
function setLanguage(lang) {
  if(!languages.includes(lang)) return;
  const current=route();
  s.lang=lang;
  save("huebner-language",lang);
  history.pushState({},"",current.view==="story"?storyPath(lang,idParam()):current.view==="about"?editionPath(lang,current.id):collectionPath(lang));
  render();
}
function imageURL(id,thumb=false) {
  return siteBase+"/engravings/"+(thumb?"thumb/":"")+number(id)+".webp";
}
function caption(id) {
  return `<span class="plate-number">${number(id)}</span><span class="plate-title">${esc(title(id))}</span>`;
}
function plate(id) {
  const src=imageURL(id,true);
  return `<figure class="plate"><a class="plate-link" href="${url(id)}" data-story="${id}" aria-label="${esc(title(id))}">
    <span class="plate-image"><img src="${src}" alt="${esc(title(id))}" loading="${id<9?"eager":"lazy"}" decoding="async" width="370" height="585"></span>
    <figcaption>${caption(id)}</figcaption></a></figure>`;
}
function filtered(){
  const search=s.search.trim().toLocaleLowerCase();
  return s.plates.filter(p=>{
    if(s.filter!=="all" && p.book!==s.filter)return false;
    if(search && ![story(p.id).en,story(p.id).de,story(p.id).ru,String(p.id),String(p.number)].some(x=>String(x).toLocaleLowerCase().includes(search)))return false;
    return true;
  });
}
function renderPlateGrid(){
  const root=document.querySelector("#plates");
  if(!root)return;
  const results=filtered();
  root.innerHTML=results.length?results.map(p=>plate(p.id)).join(""):`<p class="catalogue-empty">—</p>`;
  const counter=document.querySelector("#catalogue-count");
  if(counter)counter.textContent=String(results.length).padStart(3,"0")+" / 104";
}
function renderIndex(){
  const m=messages();
  main.innerHTML=`<section class="container catalogue">
    <div class="catalogue-head"><div><h1 class="catalogue-heading">104 Biblische Historien</h1><p class="catalogue-date">Johann Hübner · 1714</p></div><p class="index-count" id="catalogue-count">104 / 104</p></div>
    <div class="collection-bar">
      <nav class="testament-nav" aria-label="Testament">
        <button type="button" data-filter="all" aria-pressed="${s.filter==="all"}">${esc(m.all)}</button>
        <button type="button" data-filter="old" aria-pressed="${s.filter==="old"}">${esc(m.old)}</button>
        <button type="button" data-filter="new" aria-pressed="${s.filter==="new"}">${esc(m.new)}</button>
      </nav>
      <label class="searchbox"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.6" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"></circle><path d="M15 15l5.5 5.5"></path></svg><input type="search" id="plate-search" aria-label="${esc(m.search)}" placeholder="${esc(m.search)}" value="${esc(s.search)}" autocomplete="off"></label>
    </div>
    <div class="plates" id="plates"></div>
  </section>`;
  renderPlateGrid();
}
function folios(p){
  if(!p.folios?.length)return "";
  return '<section class="original-pages" aria-label="'+esc(messages().folio)+'"><div class="folios">'+
    p.folios.map((leaf,i)=>`<button type="button" class="folio-btn" data-folio="${p.id}:${i}" aria-label="${esc(messages().folio)} ${esc(leaf.label)}"><img src="${esc(leaf.image)}" alt="${esc(messages().folio)} ${esc(leaf.label)}" loading="lazy" decoding="async" width="500"></button>`).join("")+'</div></section>';
}
function textParagraphs(value){
  const blocks=String(value||"").trim().split(/\n\s*\n/).filter(Boolean);
  return blocks.map(p=>"<p>"+esc(p.replace(/\n/g," ").replace(/ {2,}/g," "))+"</p>").join("");
}
function questionList(w){
  return '<ol>'+w.questions.map((q,i)=>'<li'+(w.question_numbers?' value="'+esc(w.question_numbers[i])+'"':'')+'>'+esc(q)+'</li>').join("")+'</ol>';
}
const editions={de:german1768,en:englishFromGerman,ru:russianHistorical};
const sectionTitles={
  de:["Deutliche Fragen","Nützliche Lehren","Gottselige Gedancken","Lateinisch"],
  en:["Comprehension Questions","Useful Teachings","Devotional Reflections","Latin"],
  ru:["Вопросы","Полезныя нравоученія","Благочестивыя размышленія","Латинскій текстъ"]
};
const verses=v=>esc(v).replace(/\n/g,"<br>");
function chapterContent(p){
  const lang=s.lang,w=editions[lang][p.id],h=sectionTitles[lang];
  if(!w)return '<p class="source-absence">'+esc(messages().none)+'</p>';
  const german=german1768[p.id];
  const latin=w.latin||(lang==="ru"?german?.latin:"");
  const latinTitle=lang==="ru"&&!w.latin?"Latin · "+(german?.supplemental_witness?"Basel 1768":"Gießen 1768"):h[3];
  return '<div class="edition-prose" lang="'+lang+'">'
    +'<p class="scripture-reference">'+esc(w.reference)+'</p>'
    +'<div class="chapter-narrative">'+textParagraphs(w.narrative)+'</div>'
    +'<section class="reading-section"><h2>'+esc(h[0])+'</h2>'+questionList(w)+'</section>'
    +'<section class="reading-section"><h2>'+esc(h[1])+'</h2>'+textParagraphs(w.teaching_preamble)+w.teachings.map(t=>'<p>'+verses(t)+'</p>').join("")+'</section>'
    +'<section class="reading-section"><h2>'+esc(h[2])+'</h2>'+(lang==="ru"?textParagraphs(w.reflection):'<p class="verse">'+verses(w.reflection)+'</p>')+'</section>'
    +(latin?'<section class="reading-section"><h2>'+esc(latinTitle)+'</h2><p class="verse" lang="la">'+verses(latin)+'</p></section>':'')+'</div>';
}
function editionText(p){
  return '<div id="story-prose" aria-live="polite">'+chapterContent(p)+'</div>'+folios(p);
}
function storyEditionNotes(id){
  const p=item(id),w=editions[s.lang][id];
  if(!p||!w)return "";
  const g=german1768[id],alt=g?.supplemental_witness;
  const historic=english1765[id];
  const pages=w.pages||w.source_pages||[];
  const source=s.lang==="ru"?w.edition:s.lang==="en"?"New English translation from Gießen 1768":"Gießen 1768";
  const pageLinks=s.lang==="ru"?pages.map(n=>'<a href="https://kp.rusneb.ru/attachments_new/attachment/'+esc(w.document_id)+'/preview-page-'+n+'.jpg">'+n+'</a>'):pages.map(n=>'<a href="'+sourceGerman+'/'+String(n).padStart(4,"0")+'">'+String(n).padStart(4,"0")+'</a>');
  return '<section class="edition-record"><a class="back-link" href="'+url(id)+'" data-story="'+id+'">← '+esc(messages().back==="All stories"?"Return to story":s.lang==="de"?"Zur Geschichte":"К истории")+'</a><h2>'+esc(title(id))+'</h2><p><em>'+esc(w.title)+'</em></p>'
    +'<p class="short">'+esc(source)+' · '+esc(w.printed||"")+' · '+pageLinks.join(" · ")+'</p>'
    +(w.editorial_notes?'<p class="short">'+esc(w.editorial_notes)+'</p>':'')
    +(alt?'<p class="short">Basel 1768 · '+esc(alt.printed_page)+' · <a href="'+esc(alt.url)+'">'+esc(alt.institution)+'</a> · <a href="'+esc(alt.doi)+'">DOI</a></p>':'')
    +(!p.folios?.length?'<p class="short">The original text pages for this story have not been securely identified. <a href="'+sourceGerman+'">Heidelberg</a></p>':'')
    +(historic&&s.lang==="en"?'<details class="source-facsimile"><summary>Historical English narrative · Hamburg, 1765</summary><p class="short">The 1765 edition omits questions and reflections.</p><div class="edition-prose" lang="en">'+textParagraphs(historic.text)+'</div></details>':'')
    +'</section>';
}
function renderStory(id){
  const p=item(id),t=story(id),m=messages();
  if(!p||!t){main.innerHTML=`<section class="container error-view"><h1>404</h1></section>`;return}
  const prev=id>1?id-1:null,next=id<104?id+1:null;
  main.innerHTML=`<div class="story-shell container">
    <nav class="story-toolbar" aria-label="Story navigation">
     <a class="back-link" href="${collectionPath(s.lang)}" data-route="collection"><span aria-hidden="true">←</span>${esc(m.back)}</a>
     <span class="story-progress">${number(id)} / 104</span>
     <div class="story-nav">
      ${prev?`<a href="${url(prev)}" data-story="${prev}" aria-label="Previous">←</a>`:`<a aria-disabled="true">←</a>`}
      ${next?`<a href="${url(next)}" data-story="${next}" aria-label="Next">→</a>`:`<a aria-disabled="true">→</a>`}
     </div>
    </nav>
    <article class="reader">
     <div class="reader-art">
      <figure class="figure-art"><button type="button" class="figure-enlarge" data-zoom="${id}" aria-label="Enlarge engraving"><img src="${imageURL(id)}" alt="${esc(title(id))}" width="740" height="1130"></button></figure>
     </div>
     <div class="reader-text">
       <h1 class="chapter-title">${esc(title(id))}</h1>
       <div class="source-content" id="source-content">${editionText(p)}</div>
     </div>
    </article>
    <nav class="reader-bottom" aria-label="Adjacent stories">
      <span>${prev?`<a href="${url(prev)}" data-story="${prev}">← ${esc(title(prev))}</a>`:""}</span>
      <span>${next?`<a href="${url(next)}" data-story="${next}">${esc(title(next))} →</a>`:""}</span>
    </nav>
  </div>`;
}
function renderAbout() {
  main.innerHTML=`<section class="container about-page">
  <h1>Biblische Historien</h1>
  <p>Johann Hübner, <em>Zweymal zwey und fünfzig auserlesene Biblische Historien aus dem Alten und Neuen Testamente.</em> First published 1714.</p>
  ${route().id?storyEditionNotes(idParam()):""}
  <h2>Text witnesses</h2>
  <ul>
  <li><strong>Deutsch</strong><span>Gießen, 1768. Original printed pages and 104 engraved plates. <a href="https://digi.ub.uni-heidelberg.de/diglit/huebner1768" target="_blank" rel="noopener">Universitätsbibliothek Heidelberg ↗</a></span></li>
  <li><strong>Deutsch</strong><span>Zürich, ca. 1775. Complete facsimile and uncorrected OCR. <a href="/data/german-ocr.txt">OCR text</a> · <a href="/data/zurich-chapters.json">Chapter index</a>. <a href="https://www.e-rara.ch/zuz/doi/10.3931/e-rara-85573" target="_blank" rel="noopener">Zentralbibliothek Zürich ↗</a></span></li>
  <li><strong>English</strong><span>Hamburg, 1765. Historic English translation, narrative only. The complete English reader is a new translation, not a historical English witness. <a href="${sourceEnglish}" target="_blank" rel="noopener">British Library / Google Books ↗</a></span></li>
  <li><strong>Русский</strong><span>Saint Petersburg, 1815. Translation by Vasily Bogorodsky; edition associated with Dostoevsky. <a href="${sourceRussian1815}" target="_blank" rel="noopener">Library record ↗</a>. Moscow, 1825: <a href="${sourceRussian1825[0]}" target="_blank" rel="noopener">Old Testament ↗</a> · <a href="${sourceRussian1825[1]}" target="_blank" rel="noopener">New Testament ↗</a> digitized original-language volumes.</span></li>
  </ul>
  <p class="short">The illustrations come from Gießen 1768. Index titles are modern navigation labels. Full structured texts currently available: German ${Object.keys(german1768).length}/104, English ${Object.keys(englishFromGerman).length}/104 (new translations from transcribed German), Russian ${Object.keys(russianHistorical).length}/104 (historical Moscow 1825 text). These have not undergone independent proofreading. Story 104 uses Basel 1768, p. 512, for the final German and Latin verses. The Hamburg 1765 narrative-only witness is retained separately. Unkorrigierter Bibliotheks-OCR-Text: the individually indexed Zürich OCR is not a corrected reader edition. <a href="/data/corpus-audit.json">Measured coverage ↗</a></p>
  <p class="short"><a href="https://github.com/DalmoMendonca/biblicalstories" target="_blank" rel="noopener">Source code and crop provenance ↗</a></p>
  </section>`;
}
function render(){
  updateLanguage();
  const v=view();
  if(v==="story")renderStory(idParam());
  else if(v==="about")renderAbout();
  else renderIndex();
  const lang=s.lang,id=v==="story"?idParam():null;
  const names={en:"104 Biblical Histories",de:"104 Biblische Historien",ru:"104 Священные истории"};
  const intro={en:"Read Johann Hübner’s 104 illustrated Bible stories in English, German and Russian, with original 1768 engravings, questions, teachings and devotional reflections.",de:"Johann Hübners 104 biblische Historien mit Originalkupferstichen von 1768, Fragen, Lehren und gottseligen Gedanken. Deutsch, Englisch und Russisch.",ru:"104 библейские истории Иоганна Гюбнера на русском, немецком и английском языках с гравюрами 1768 года, вопросами, нравоучениями и размышлениями."};
  const w=id?editions[lang][id]:null;
  const name=id?title(id):v==="about"?messages().about:names[lang];
  const fullTitle=name+" — Johann Hübner";
  const description=w?name+". "+w.reference+{en:" Read Johann Hübner’s illustrated biblical history with comprehension questions, teachings and devotional reflection.",de:" Biblische Historie mit Originalkupferstich, Fragen, Lehren und gottseligen Gedanken.",ru:" Библейская история с гравюрой, вопросами, нравоучениями и размышлениями."}[lang]:intro[lang];
  const path=v==="story"?storyPath(lang,id):v==="about"?editionPath(lang):collectionPath(lang);
  const canonical=origin+path.slice(siteBase.length);
  const image=origin+"/social/"+lang+"/"+(id?number(id):"cover")+".jpg";
  document.title=fullTitle;
  for(const [key,val] of Object.entries({"description":description,"og:title":fullTitle,"og:description":description,"og:url":canonical,"og:image":image,"og:image:alt":name,"og:type":id?"article":"website","og:locale":{en:"en_US",de:"de_DE",ru:"ru_RU"}[lang],"twitter:title":fullTitle,"twitter:description":description,"twitter:image":image,"twitter:image:alt":name})){
    const node=document.querySelector('meta[name="'+key+'"],meta[property="'+key+'"]');if(node)node.content=val;
  }
  const link=document.querySelector('link[rel="canonical"]');if(link)link.href=canonical;
  for(const code of [...languages,"x-default"]){
    const target=code==="x-default"?"en":code;
    const a=document.querySelector('link[hreflang="'+code+'"]');
    if(a)a.href=origin+(id?storyPath(target,id):v==="about"?editionPath(target):collectionPath(target)).slice(siteBase.length);
  }
  const schema=document.querySelector("#structured-data");
  if(schema)schema.textContent=JSON.stringify({"@context":"https://schema.org","@type":id?"Chapter":v==="about"?"AboutPage":"CollectionPage","name":name,"url":canonical,"inLanguage":lang,"description":description,"image":image,...(id?{position:id,author:{"@type":"Person",name:"Johann Hübner"},isPartOf:{"@type":"Book",name:"Biblische Historien",author:{"@type":"Person",name:"Johann Hübner"},datePublished:"1714",url:origin+"/"}}:{mainEntity:{"@type":"Book",name:"Biblische Historien",author:{"@type":"Person",name:"Johann Hübner"},datePublished:"1714",inLanguage:languages}})});
}
function openImage(src,alt){
  lightboxImage.src=src;
  lightboxImage.alt=alt;
  lightbox.showModal();
}
document.addEventListener("click",e=>{
  const language=e.target.closest("[data-lang]");
  if(language){setLanguage(language.dataset.lang);return}
  const filter=e.target.closest("[data-filter]");
  if(filter){
    s.filter=filter.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach(b=>b.setAttribute("aria-pressed",String(b===filter)));
    renderPlateGrid();return;
  }
  const chapter=e.target.closest("[data-story]");
  if(chapter){e.preventDefault();navigate("story",Number(chapter.dataset.story));return}
  const route=e.target.closest("[data-route]");
  if(route){e.preventDefault();navigate(route.dataset.route,route.dataset.editionStory?Number(route.dataset.editionStory):null);return}
  const zoom=e.target.closest("[data-zoom]");
  if(zoom){const p=item(Number(zoom.dataset.zoom));openImage(imageURL(p.id),title(p.id));return}
  const leaf=e.target.closest("[data-folio]");
  if(leaf){
    const [id,index]=leaf.dataset.folio.split(":").map(Number);
    const p=item(id);const f=p.folios[index];if(f)openImage(f.image,`Hübner · printed page ${f.label}`);
  }
});
document.addEventListener("input",e=>{
  if(e.target.id==="plate-search"){s.search=e.target.value;renderPlateGrid()}
});
window.addEventListener("popstate",()=>{s.lang=route().lang||s.lang;render()});
document.querySelector("#lightbox-close").addEventListener("click",()=>lightbox.close());
lightbox.addEventListener("click",e=>{if(e.target===lightbox)lightbox.close()});
document.addEventListener("keydown",e=>{
  if(e.key==="Escape"&&lightbox.open){lightbox.close();return}
  if(lightbox.open||view()!=="story"||e.altKey||e.ctrlKey||e.metaKey||/^(INPUT|TEXTAREA|BUTTON)$/.test(document.activeElement?.tagName||""))return;
  const id=idParam();
  if(e.key==="ArrowLeft"&&id>1)navigate("story",id-1);
  if(e.key==="ArrowRight"&&id<104)navigate("story",id+1);
});
async function init(){
  try{
    const response=await fetch("/data/archive.json");
    if(!response.ok)throw Error("Missing original archive");
    const data=await response.json();
    if(!Array.isArray(data.images)||data.images.length!==104)throw Error("Incomplete historical sequence");
    for(let i=0;i<104;i++)if(data.images[i].id!==i+1)throw Error("Plate sequence mismatch");
    s.plates=data.images;s.byId=new Map(data.images.map(p=>[p.id,p]));
    const current=route();
    if(!current.lang&&current.view==="story")history.replaceState({},"",storyPath(s.lang,idParam()));
    else if(!current.lang&&current.view==="about")history.replaceState({},"",editionPath(s.lang,current.id));
    render();
  }catch(err){
    main.innerHTML=`<div class="container error-view"><h1>Archive unavailable</h1><p>The historical image archive could not be loaded.</p><a href="${sourceGerman}">Heidelberg source ↗</a></div>`;
    console.error(err);
  }
}
init();