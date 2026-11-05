const {chromium}=require('playwright');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
(async()=>{
const browser=await chromium.launch({headless:true,...(process.env.BROWSER_CHANNEL?{channel:process.env.BROWSER_CHANNEL}:{})});
const page=await browser.newPage({viewport:{width:1200,height:1800},deviceScaleFactor:1});
await page.goto(pathToFileURL(path.resolve(__dirname,'../submission/poster.html')).href);
await page.emulateMedia({media:'print'});
await page.screenshot({path:path.resolve(__dirname,'../submission/poster-preview.png'),fullPage:true});
console.log(await page.evaluate(()=>({width:document.querySelector('.sheet').offsetWidth,height:document.querySelector('.sheet').offsetHeight,a3Height:420*96/25.4,images:[...document.images].map(x=>x.complete&&x.naturalWidth>0)})));
await browser.close();
})().catch(e=>{console.error(e);process.exitCode=1;});
