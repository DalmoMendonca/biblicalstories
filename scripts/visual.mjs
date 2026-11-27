import { chromium } from "playwright";
import assert from "node:assert/strict";
import fs from "node:fs";
import { german1768 } from "../src/german1768.js";
import { englishFromGerman } from "../src/englishFromGerman.js";
import { russianHistorical } from "../src/russianHistorical.js";
import { english1765 } from "../src/english1765.js";

const editions={de:german1768,en:englishFromGerman,ru:russianHistorical};
const headings={
 de:["Deutliche Fragen","Nützliche Lehren","Gottselige Gedancken","Lateinisch"],
 en:["Comprehension Questions","Useful Teachings","Devotional Reflections","Latin"],
 ru:["Вопросы","Полезныя нравоученія","Благочестивыя размышленія"]
};
// Select the original-page panel by its contents, not the optional OCR or
// historical narrative disclosure panels which share its CSS class.
const originalPanel=page=>page.locator(".original-pages");


const base=process.env.SITE_BASE || "http://127.0.0.1:8123";
fs.mkdirSync("qa",{recursive:true});
const browser=await chromium.launch({headless:true,args:["--no-sandbox"]});
try{
 const desktop=await browser.newPage({viewport:{width:1440,height:900}});
 const errors=[];
 desktop.on("pageerror",e=>errors.push(e.message));
 await desktop.goto(base+"/",{waitUntil:"domcontentloaded"});
 await desktop.locator(".plate").first().waitFor();
 assert.equal(await desktop.locator(".plate").count(),104);
 assert.equal(await desktop.locator(".plate img").first().getAttribute("src"),"/engravings/thumb/001.webp");
 await desktop.locator(".plate img").first().evaluate(i=>i.decode());
 await desktop.screenshot({path:"qa/new-index-desktop.jpg",type:"jpeg",quality:82});
 await desktop.locator('[data-filter="new"]').click();
 assert.equal(await desktop.locator(".plate").count(),52);
 await desktop.locator('[data-filter="all"]').click();
 assert.equal(await desktop.locator(".plate").count(),104);
 await desktop.locator("#plate-search").fill("Job");
 assert.equal(await desktop.locator(".plate").count(),1);
 await desktop.locator(".plate-link").first().click();
 assert.match(desktop.url(),/stories\/043\//);
 await desktop.locator(".figure-art img").evaluate(i=>i.decode());
 assert.ok((await desktop.locator(".figure-art img").getAttribute("src")).startsWith("/engravings/"));
 await desktop.locator('[data-lang="de"]').click();
 assert.equal(await desktop.locator(".folio-btn").count(),6);
 assert.ok(await originalPanel(desktop).isVisible(),"original pages should be visible by default");
 await desktop.locator(".folio-btn img").first().evaluate(i=>i.decode());
 await desktop.screenshot({path:"qa/new-reader-desktop.jpg",type:"jpeg",quality:82});
 await desktop.locator(".folio-btn").first().click();
 assert.ok(await desktop.locator("#lightbox").evaluate(el=>el.open));
 await desktop.locator("#lightbox-close").click();
 await desktop.locator('[data-lang="ru"]').click();
 assert.match(await desktop.locator(".chapter-title").textContent(),/Иов/);
 assert.match(desktop.url(),/stories\/043\//);
 await desktop.locator('[data-story="44"]').first().click();
 assert.match(desktop.url(),/stories\/044\//);
 assert.equal(errors.length,0,errors.join("; "));
 console.log("DESKTOP PASSED: 104 original-only images; filters; search; source photographs; 3-language navigation; enlargement; sequential reading.");

 const mobile=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true});
 const mobileErrors=[];
 mobile.on("pageerror",e=>mobileErrors.push(e.message));
 await mobile.goto(base+"/",{waitUntil:"domcontentloaded"});
 await mobile.locator(".plate").first().waitFor();
 await mobile.locator(".plate img").first().evaluate(i=>i.decode());
 assert.equal(await mobile.locator(".plate").count(),104);
 assert.ok(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2),"gallery overflow");
 await mobile.screenshot({path:"qa/new-index-mobile.jpg",type:"jpeg",quality:84});
 await mobile.goto(base+"/?view=story&id=104",{waitUntil:"domcontentloaded"});
 await mobile.locator(".figure-art img").evaluate(i=>i.decode());
 assert.ok(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2),"reader overflow");
 const art=await mobile.locator(".reader-art").boundingBox();
 const txt=await mobile.locator(".reader-text").boundingBox();
 assert.ok(art.y < txt.y,"mobile original engraving must precede story text");
 await mobile.screenshot({path:"qa/new-reader-mobile.jpg",type:"jpeg",quality:84,fullPage:true});
 await mobile.locator('[data-lang="de"]').click();
 assert.ok(await mobile.locator(".folio-btn").count()>=1);
 assert.ok(await originalPanel(mobile).isVisible(),"original pages should be visible on mobile");
 await mobile.locator('[data-zoom="104"]').click();
 assert.ok(await mobile.locator("#lightbox").evaluate(el=>el.open));
 await mobile.locator("#lightbox-close").click();
 assert.equal(mobileErrors.length,0,mobileErrors.join("; "));
 console.log("MOBILE PASSED: 104 engravings, image-led responsive story, original German pages, working language selector, no overflow or JS errors");
 // The reader modules are the authoritative structured editions; the rejected
 // legacy public/texts files are not a prerequisite for editorial checks.
 const chapter=await browser.newPage({viewport:{width:1024,height:820}});
 for(const id of [1,3,69,71,87,104]){
   await chapter.goto(base+"/?view=story&id="+id,{waitUntil:"domcontentloaded"});
   for(const lang of ["de","en","ru"]){
     await chapter.locator('[data-lang="'+lang+'"]').click();
     const prose=chapter.locator("#story-prose");
     const expected=editions[lang][id];
     if(expected){
       const article=prose.locator(":scope > .edition-prose");
       await article.waitFor({timeout:20000});
       assert.equal(await article.count(),1,"One primary edition must render");
       assert.equal(await prose.locator(".source-absence").count(),0);
       assert.equal(await article.getAttribute("lang"),lang);
       assert.equal(await article.locator(".scripture-reference").textContent(),expected.reference);
       assert.equal(await article.locator(".chapter-narrative").innerText(),expected.narrative.replace(/\n/g," "));
       assert.deepEqual(await article.locator("ol > li").allTextContents(),expected.questions);
       if(expected.question_numbers){
         assert.deepEqual(await article.locator("ol > li").evaluateAll(nodes=>nodes.map(n=>Number(n.getAttribute("value")))),expected.question_numbers);
       }
       const actualHeadings=await article.locator("h2").allTextContents();
       assert.deepEqual(actualHeadings.slice(0,headings[lang].length),headings[lang]);
       const normalized=s=>s.replace(/\s+/g," ").trim();
       const plain=await article.evaluate(el=>el.innerText);
       for(const teaching of expected.teachings) assert.ok(normalized(plain).includes(normalized(teaching)),`Missing teaching ${id}/${lang}`);
       assert.ok(normalized(plain).includes(normalized(expected.reflection)),`Missing reflection ${id}/${lang}`);
       if(expected.latin) assert.equal(normalized(await article.locator('p[lang="la"]').innerText()),normalized(expected.latin));
       assert.equal(await prose.locator("a[href^='http']").count(),0,"Source links must not interrupt reading");
     }else if(lang==="en"&&english1765[id]){
       await prose.locator(".edition-prose").waitFor({timeout:20000});
       assert.match(await prose.innerText(),/omits the questions and reflections/i);
       assert.equal(await prose.locator("ol").count(),0,"Narrative-only witness must not impersonate full text");
     }else{
       await prose.locator(".source-absence").waitFor({timeout:20000});
       assert.equal(await prose.locator(".edition-prose").count(),0,`Unverified OCR displayed as primary ${lang} text for story ${id}`);
     }
     if(id===69) assert.equal(await originalPanel(chapter).count(),0,"Do not invent absent facsimiles");
     else{
       assert.equal(await originalPanel(chapter).count(),1);
       assert.ok(await originalPanel(chapter).isVisible(),"Original pages must remain directly visible");
       assert.ok(await chapter.locator(".folio-btn").count()>=1);
     }
     assert.equal(await chapter.locator("[data-lang]").count(),3,"Exactly one language selector");
     assert.equal(await chapter.locator(".reader a[href^='http']").count(),0,"Reader must not contain outbound source links");
     assert.equal(await chapter.locator(".chapter-title").count(),1);
     assert.ok(await chapter.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2),"Reader overflow");
     assert.ok(chapter.url().includes("/stories/"+String(id).padStart(3,"0")+"/"),"Language changed story");
     console.log("EDITORIAL INTEGRITY PASS",id,lang);
   }
 }
 await chapter.locator("#about-link").click();
 assert.match(chapter.url(),/edition\/\?id=104/);
 assert.match(await chapter.locator(".edition-record").innerText(),/Basel 1768/);
 assert.ok(await chapter.locator(".edition-record a[href^='http']").count()>0,"Archival links must remain available in Edition");
 await chapter.locator(".edition-record .back-link").click();
 assert.match(chapter.url(),/stories\/104\//);
 await chapter.close();

}finally{await browser.close();}
