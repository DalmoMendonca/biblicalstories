import { chromium } from "playwright";
import fs from "fs";
const targets = [
 ["russian1825","https://kp.rusneb.ru/item/reader/sto-chetyre-svyashchennyya-istorii-pyatdesyat-dve-svyashchennyya-istorii-iz-vethago-zaveta--ch1"],
 ["english1765","https://books.google.com/books?id=5elUAAAAcAAJ&pg=PA1"]
];
fs.mkdirSync("qa/archive-readers",{recursive:true});
const browser=await chromium.launch({headless:true,args:["--no-sandbox","--disable-dev-shm-usage"]});
for(const [name,url] of targets){
 const page=await browser.newPage({viewport:{width:1280,height:900}});
 const requests=new Set();
 const responses=[];
 page.on("request",q=>{if(/\/api\/|\/iiif|\/image|\/viewer|\/content\?|\/book\/|\/page|\/doc\/|\.pdf/i.test(q.url()))requests.add(q.url().slice(0,280));});
 page.on("response",r=>{if(/\/api\/|\/iiif|\/image|\/viewer|\/content\?|\/book\/|\/page|\/doc\/|\.pdf/i.test(r.url()))responses.push([r.status(),r.headers()["content-type"],r.url().slice(0,280)]);});
 console.log("TARGET",name,url);
 try{
  let resp=await page.goto(url,{waitUntil:"domcontentloaded",timeout:45000});
  console.log("LOADED",resp?.status(),page.url());
  await page.waitForTimeout(16000);
  console.log("TITLE",await page.title());
  console.log("BODY",String(await page.locator("body").innerText().catch(()=>'' )).slice(0,2200));
  console.log("IMG",await page.locator("img").count());
  console.log("CANVAS",await page.locator("canvas").count());
  console.log("LINKS",await page.locator("a[href]").evaluateAll(a=>a.slice(0,20).map(x=>x.href)).catch(()=>[]));
  console.log("REQUESTS",JSON.stringify([...requests]).slice(0,9000));
  console.log("RESPONSES",JSON.stringify(responses.slice(0,45)).slice(0,9000));
  await page.screenshot({path:"qa/archive-readers/"+name+".png",fullPage:false});
 }catch(e){console.log("ERROR",name,String(e).slice(0,800))}
 await page.close();
}
await browser.close();
