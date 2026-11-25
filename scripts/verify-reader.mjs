import { chromium } from "playwright";
import fs from "node:fs";
import assert from "node:assert/strict";
import crypto from "node:crypto";
const base=process.env.BASE_URL||"http://127.0.0.1:4173";
const modules={de:"german1768",en:"englishFromGerman",ru:"russianHistorical"};
const readModule=(name)=>JSON.parse(fs.readFileSync("src/"+name+".js","utf8").split("export const "+name+" = ")[1].trim().replace(/;$/,""));
const texts=Object.fromEntries(Object.entries(modules).map(([l,n])=>[l,readModule(n)]));
const report=await fetch(base+"/data/corpus-audit.json").then(r=>{assert(r.ok);return r.json()});
const receipt=await fetch(base+"/data/build-receipt.json").then(r=>{assert(r.ok);return r.json()});
if(process.env.EXPECTED_COMMIT)assert.equal(receipt.commit,process.env.EXPECTED_COMMIT);
const browser=await chromium.launch({headless:true,args:["--no-sandbox"]});
const errors=[],results=[];
const heads={de:["Deutliche Fragen","Nützliche Lehren","Gottselige Gedancken"],en:["Comprehension Questions","Useful Teachings","Devotional Reflections"],ru:["Вопросы","Полезныя нравоученія","Благочестивыя размышленія"]};
const norm=s=>s.replace(/\s+/g," ").trim();
let next=1;
async function worker(){
 const context=await browser.newContext({viewport:{width:390,height:844}});
 await context.route("https://fonts.googleapis.com/**",route=>route.abort());
 await context.route("https://fonts.gstatic.com/**",route=>route.abort());
 const page=await context.newPage();page.on("pageerror",e=>errors.push({id:page.url(),error:e.message}));
 for(;;){
  const id=next++;if(id>104)break;
  try{
   const response=await page.goto(base+"/?view=story&id="+id,{waitUntil:"domcontentloaded",timeout:30000});assert(response?.ok());
   await page.locator(".chapter-title").waitFor({timeout:15000});
   assert.equal(await page.locator(".story-progress").textContent(),String(id).padStart(3,"0")+" / 104");
   const img=page.locator(".figure-art img");
   assert.equal(await img.getAttribute("src"),"/engravings/"+String(id).padStart(3,"0")+".webp");
   await img.evaluate(el=>el.decode());
   assert(await img.evaluate(el=>el.naturalWidth>0));
   const row={id,languages:{}};
   for(const lang of ["de","en","ru"]){
    await page.locator('[data-reader-lang="'+lang+'"]').click();
    assert.equal(await page.locator("html").getAttribute("lang"),lang);
    assert.equal(await page.locator('[data-reader-lang="'+lang+'"]').getAttribute("aria-pressed"),"true");
    assert((await page.locator(".chapter-title").textContent()).trim());
    const w=texts[lang][id],prose=page.locator("#story-prose");
    if(w){
     const edition=prose.locator(".edition-prose").first();
     const body=norm(await edition.innerText());
     for(const h of heads[lang])assert(body.includes(h),lang+" "+id+" missing heading "+h);
     assert(body.includes(norm(w.narrative)),lang+" "+id+" narrative mismatch");
     const q=await edition.locator("ol>li").allTextContents();
     assert.deepEqual(q.map(norm),w.questions.map(norm));
     for(const t of w.teachings)assert(body.includes(norm(t)),lang+" "+id+" teaching mismatch");
     assert(body.includes(norm(w.reflection)),lang+" "+id+" reflection mismatch");
     const latin=w.latin||texts.de[id]?.latin;
     if(latin)assert.equal(norm(await edition.locator('[lang="la"]').innerText()),norm(latin));
     assert.equal(report.rows[id-1][lang].structurally_valid,true);
    }else{
     assert.equal(report.rows[id-1][lang].structurally_valid,false);
     if(lang!=="en")assert.equal(await prose.locator(".source-absence").count(),1);
    }
    row.languages[lang]={route:true,structured:!!w};
   }
   const nextLink=page.locator(".story-nav a[aria-label=Next]");
   if(id<104){assert.equal(await nextLink.getAttribute("href"),"/?view=story&id="+(id+1));}
   results.push(row);
  }catch(e){errors.push({id,error:e.message});}
 }
 await context.close();
}
try{await Promise.all(Array.from({length:6},worker));}finally{await browser.close()}
results.sort((a,b)=>a.id-b.id);
const actual={base,commit:receipt.commit,routes:results.length,language_selections:results.reduce((n,x)=>n+Object.keys(x.languages).length,0),structured_chapters:Object.fromEntries(Object.keys(modules).map(l=>[l,results.filter(r=>r.languages[l].structured).length])),errors,run_id:process.env.GITHUB_RUN_ID||null};
fs.writeFileSync(process.env.REPORT_PATH||"route-validation.json",JSON.stringify(actual,null,2)+"\n");
console.log(JSON.stringify(actual,null,2));
assert.equal(errors.length,0);assert.equal(results.length,104);assert.equal(actual.language_selections,312);
