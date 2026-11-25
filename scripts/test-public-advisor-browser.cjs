const assert=require('node:assert/strict'),path=require('node:path');
const {chromium}=require(process.env.CAPABILITY_PLAYWRIGHT_MODULE||'playwright');
const base=process.env.CAPABILITY_PREVIEW_URL||'http://127.0.0.1:8020';
if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(base)&&base!=='https://surfacedmp.com')throw Error('Unknown target');
(async()=>{const browser=await chromium.launch({headless:true,executablePath:process.env.CAPABILITY_BROWSER_EXECUTABLE});try{
 const context=await browser.newContext({acceptDownloads:true,viewport:{width:1440,height:1000}}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));await page.goto(base+'/guest');await page.locator('#product-details').first().waitFor();assert.equal(await page.locator('#sku option').count(),11);
 const sku=await page.locator('#sku').inputValue();
 for(const tab of ['ai','gaming','generation','productivity','deployment','faq','tco','evidence']){await page.locator(`[data-tab=${tab}]`).click();if(tab==='faq')await page.locator('#faqresult article').first().waitFor();if(tab==='tco')await page.locator('#tco-purchase_price_cny').waitFor();assert.ok((await page.locator('#content').textContent()).length>30,tab);}
 await page.getByText('预览客户能力报告',{exact:true}).click();await page.getByRole('button',{name:'关闭预览，返回能力顾问'}).click();
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'下载 PDF 报告',exact:true}).click();await(await download).saveAs(path.join(__dirname,'../artifacts/releases/public-advisor-'+(base.includes('127.0.0.1')?'local':'production')+'.pdf'));
 const ticket=await context.request.post(base+'/api/reports/mobile-ticket',{data:{part_number:sku}});assert.equal(ticket.status(),200);const data=await ticket.json();const url=base+'/api/reports/mobile-download/'+data.ticket;assert.equal((await context.request.get(url)).status(),200);assert.equal((await context.request.get(url)).status(),404);
 await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.deepEqual(errors,[]);
 console.log(JSON.stringify({destination:base,anonymous:true,skus:11,tabs:8,pdf:true,mobile_single_use_pdf:true,page_errors:errors}));
}finally{await browser.close()}})().catch(e=>{console.error(e.stack);process.exitCode=1});
