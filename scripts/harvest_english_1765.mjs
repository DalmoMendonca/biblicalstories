import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const shard = Number(process.env.SHARD ?? "0");
const shards = Number(process.env.SHARDS ?? "8");
if (!Number.isInteger(shard) || !Number.isInteger(shards) || shard<0 || shard>=shards) throw Error("Invalid shard");
const out = "public/english-1765-pages";
fs.mkdirSync(out,{recursive:true});
const browser = await chromium.launch({headless:true,args:["--no-sandbox","--disable-dev-shm-usage"]});
const page = await browser.newPage({viewport:{width:1200,height:850}});
let saved=0, failed=[];
try {
 for(let p=shard+1;p<=251;p+=shards){
  const pg="PA"+p, filename=path.join(out,pg+".jpg");
  if(fs.existsSync(filename)&&fs.statSync(filename).size>3500){saved++;continue;}
  let ok=false;
  for(let attempt=0;attempt<3&&!ok;attempt++){
   try {
    const responsePromise=page.waitForResponse(r=>{
      const u=new URL(r.url());
      return u.hostname==="books.google.com"
       && u.pathname==="/books/content"
       && u.searchParams.get("pg")===pg
       && u.searchParams.get("img")==="1" && r.status()===200;
    },{timeout:26000});
    await page.goto("https://books.google.com/books?id=5elUAAAAcAAJ&pg="+pg,{
      waitUntil:"domcontentloaded",timeout:40000
    });
    const r=await responsePromise;
    const bytes=await r.body();
    if(!r.headers()["content-type"]?.startsWith("image/jpeg")||bytes.length<3500){
      throw Error("Unexpected response content "+r.headers()["content-type"]+" bytes "+bytes.length);
    }
    fs.writeFileSync(filename,bytes);
    saved++;ok=true;
    console.log("SAVED",pg,bytes.length,"bytes",r.url().slice(0,125));
   } catch(e){
    console.error("RETRY",pg,attempt+1,String(e).slice(0,180));
    await page.waitForTimeout(600*(attempt+1));
   }
  }
  if(!ok)failed.push(pg);
 }
 console.log("COMPLETE SHARD",shard,"saved",saved,"failed",JSON.stringify(failed));
 if(failed.length)throw new Error("Missing English 1765 pages "+failed.join(","));
} finally {await browser.close();}
