import { chromium } from "playwright";
import assert from "node:assert/strict";
import fs from "node:fs";

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
 assert.match(desktop.url(),/id=43/);
 await desktop.locator(".figure-art img").evaluate(i=>i.decode());
 assert.ok((await desktop.locator(".figure-art img").getAttribute("src")).startsWith("/engravings/"));
 await desktop.locator('[data-reader-lang="de"]').click();
 assert.equal(await desktop.locator(".folio-btn").count(),6);
 assert.ok(await desktop.locator(".source-facsimile").evaluate(el=>el.open),"original pages should be visible by default");
 await desktop.locator(".folio-btn img").first().evaluate(i=>i.decode());
 await desktop.screenshot({path:"qa/new-reader-desktop.jpg",type:"jpeg",quality:82});
 await desktop.locator(".folio-btn").first().click();
 assert.ok(await desktop.locator("#lightbox").evaluate(el=>el.open));
 await desktop.locator("#lightbox-close").click();
 await desktop.locator('[data-reader-lang="ru"]').click();
 assert.match(await desktop.locator(".chapter-title").textContent(),/Иов/);
 assert.match(desktop.url(),/id=43/);
 await desktop.locator('[data-story="44"]').first().click();
 assert.match(desktop.url(),/id=44/);
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
 await mobile.locator('[data-reader-lang="de"]').click();
 assert.ok(await mobile.locator(".folio-btn").count()>=1);
 assert.ok(await mobile.locator(".source-facsimile").evaluate(el=>el.open),"original pages should be visible on mobile");
 await mobile.locator('[data-zoom="104"]').click();
 assert.ok(await mobile.locator("#lightbox").evaluate(el=>el.open));
 await mobile.locator("#lightbox-close").click();
 assert.equal(mobileErrors.length,0,mobileErrors.join("; "));
 console.log("MOBILE PASSED: 104 engravings, image-led responsive story, original German pages, working language selector, no overflow or JS errors");
 if(fs.existsSync("public/texts/001.json")){
   const chapter=await browser.newPage({viewport:{width:1024,height:820}});
   for(const id of [1,3,69,71,87,104]){
     await chapter.goto(base+"/?view=story&id="+id,{waitUntil:"domcontentloaded"});
     for(const lang of ["de","en","ru"]){
       await chapter.locator('[data-reader-lang="'+lang+'"]').click();
       await chapter.locator(".source-absence").waitFor({timeout:20000});
       assert.equal(await chapter.locator(".edition-prose").count(),0,`Unreviewed OCR displayed as ${lang} original for story ${id}`);
       if(id===69) assert.match(await chapter.locator(".source-facsimile").textContent(),/Heidelberg/,"Chapter 69 requires an explicit archival collation warning");
       else assert.ok(await chapter.locator(".folio-btn").count()>=1,"Original Giessen pages should remain available");
       assert.ok(await chapter.locator(".source-facsimile").evaluate(el=>el.open),"Facsimiles must open by default");
       if(lang!=="de") assert.ok(await chapter.locator('#source-content a[href^="http"]').count()>=2,"Historic edition/source links missing");
       assert.ok(chapter.url().includes("id="+id),"Language changed story");
       console.log("EDITORIAL INTEGRITY PASS",id,lang);
     }
   }
   await chapter.close();
 }

}finally{await browser.close();}
