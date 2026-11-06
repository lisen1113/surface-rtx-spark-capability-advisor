/* Real loopback-browser smoke test. Credentials and artifacts stay outside Git. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const { chromium } = require(process.env.CAPABILITY_PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.CAPABILITY_PREVIEW_URL || 'http://127.0.0.1:8020';
if (!/^http:\/\/(127\.0\.0\.1|localhost):\d+$/.test(base)) throw Error('Browser smoke test is loopback-only');
const privateDir = path.join(root, '.commercial-local');
const credentials = JSON.parse(fs.readFileSync(path.join(privateDir, 'credentials.json'), 'utf8'));
const output = path.join(root, 'artifacts', 'commercial');
fs.mkdirSync(output, {recursive:true});

(async()=>{
 const executable=process.env.CAPABILITY_BROWSER_EXECUTABLE;
 const browser=await chromium.launch({headless:true,...(executable?{executablePath:executable}:{})});
 const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
 const page=await context.newPage();const errors=[];
 page.on('pageerror',error=>errors.push(error.message));
 async function login(role) {
  await page.goto(base+'/workplace');
  await page.evaluate(()=>sessionStorage.removeItem('cap_token'));
  await page.reload();
  await page.locator('#login-form [name=email]').fill(credentials[role].email);
  await page.locator('#login-form [name=password]').fill(credentials[role].password);
  await page.locator('#login-form button').click();
  await page.locator('#workspace').waitFor({state:'visible'});
  await page.locator('#hardware-select option').nth(1).waitFor({state:'attached'});
  await page.waitForFunction(()=>document.querySelector('#message')?.textContent==='登录成功');
 }
 try {
  await login('owner');
  await page.locator('#fx').fill('7.2');await page.locator('#tax').fill('0');await page.locator('#fx-reference').fill('本地验收示例汇率 非正式报价');
  await page.locator('#policy').selectOption({index:1});
  const device=await page.locator('#hardware-select optgroup[label="Surface 设备"] option').first().getAttribute('value');
  await page.locator('#hardware-select').selectOption(device);await page.locator('#hardware-quantity').fill('10');await page.locator('#add-hardware').click();
  await page.getByText('按需求比较订阅与 Bundle',{exact:true}).click();
  await page.locator('#software-users').fill('10');await page.locator('#copilot-users').fill('3');
  await page.locator('#compare-cloud').click();
  await page.locator('[data-subscription-option]').first().waitFor();
  assert.equal(await page.locator('[data-subscription-option]').count(),2);
  await page.locator('[data-subscription-option]').first().click();
  await page.locator('#azure-requested').check();
  await page.locator('#discount').fill('100');await page.locator('#discount-reason').fill('本地整体项目优惠验收');
  await page.locator('#save-quote').click();
  await page.waitForFunction(()=>document.querySelector('#message')?.textContent.includes('方案已保存'));
  await page.locator('#result-panel').screenshot({path:path.join(output,'customer-budget-desktop.png')});
  const quoteId=(await page.locator('#result-state').innerText()).match(/Q-[a-f0-9]+/)[0];
  assert(!/software_cost_factor|erp_unit_cost_cny|annual_irr/.test(await page.locator('#result-panel').innerText()));
  const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'下载预算方案 PDF'}).click()]);
  await download.saveAs(path.join(output,'budget-sample.pdf'));
  await page.setViewportSize({width:390,height:844});await page.locator('#result-panel').scrollIntoViewIfNeeded();
  await page.locator('#result-panel').screenshot({path:path.join(output,'customer-budget-mobile.png')});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'Mobile page overflows');
  await page.setViewportSize({width:1440,height:1000});
  await login('admin');
  await page.locator('#admin-panel').waitFor({state:'visible'});
  // Test the administrative review panel on the saved customer quote.
  await page.locator('#quotes-list tbody tr').filter({hasText:'企业办公设备与订阅方案'}).first().getByRole('button',{name:'打开方案'}).click();
  await page.locator('#internal-active').waitFor();
  await page.locator('#internal-active').screenshot({path:path.join(output,'internal-review.png')});
  assert((await page.locator('#internal-active').innerText()).includes('0.85'));
  assert.equal(errors.length,0,errors.join('\n'));
  fs.writeFileSync(path.join(output,'browser-results.json'),JSON.stringify({passed:true,quoteId,checks:['login','hardware selection','bundle comparison','project discount','saved quote','budget PDF download','mobile layout','admin-only internal metrics'],pageErrors:errors},null,2));
  console.log('Commercial browser checks passed: customer budget, Bundle comparison, PDF, mobile layout and admin metrics.');
 } catch(error) {
  console.error('Page errors:',errors.join('; '));
  console.error('Visible status:',await page.locator('#message').textContent());
  await page.screenshot({path:path.join(output,'browser-failure.png'),fullPage:true});
  throw error;
 } finally {await browser.close();}
})().catch(error=>{console.error(error.message);process.exitCode=1;});
