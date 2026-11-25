const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function loadPage(wx) {
  let page;
  const source = fs.readFileSync(path.join(__dirname, '../miniprogram/pages/report/index.js'), 'utf8');
  vm.runInNewContext(source, { Page: (definition) => { page = definition; }, wx });
  return { ...page, setData(data) { this.data = { ...this.data, ...data }; } };
}

{
  let downloads = 0;
  const page = loadPage({ downloadFile() { downloads += 1; } });
  page.onLoad({ ticket: '../bad' });
  assert.equal(downloads, 0);
  assert.match(page.data.status, /授权无效/);
}

{
  let request;
  let preview;
  const page = loadPage({
    downloadFile(options) { request = options; },
    openDocument(options) { preview = options; }
  });
  page.onLoad({ ticket: 'a'.repeat(20) });
  assert.equal(request.url, 'https://surfacedmp.com/api/reports/mobile-download/' + 'a'.repeat(20));
  request.success({ statusCode: 200, tempFilePath: '/tmp/report.pdf' });
  assert.equal(preview.fileType, 'pdf');
  assert.equal(preview.showMenu, true);
  preview.success();
  assert.match(page.data.status, /右上角菜单保存/);
}

{
  let request;
  let previewed = false;
  const page = loadPage({
    downloadFile(options) { request = options; },
    openDocument() { previewed = true; }
  });
  page.onLoad({ ticket: 'b'.repeat(20) });
  request.success({ statusCode: 403, tempFilePath: '/tmp/report.pdf' });
  assert.equal(previewed, false);
  assert.match(page.data.status, /已过期或下载失败/);
}

{
  let request;
  let preview;
  const page = loadPage({
    env: { USER_DATA_PATH: '/user' },
    downloadFile(options) { request = options; },
    openDocument(options) { preview = options; }
  });
  page.onLoad({ ticket: 'c'.repeat(20), filename: 'Surface-Product-EP2-77145.pdf' });
  assert.equal(request.filePath, '/user/Surface-Product-EP2-77145.pdf');
  request.success({ statusCode: 200, filePath: request.filePath });
  assert.equal(preview.filePath, request.filePath);
}

{
  let request;
  const page = loadPage({
    env: { USER_DATA_PATH: '/user' },
    downloadFile(options) { request = options; }
  });
  page.onLoad({ ticket: 'd'.repeat(20), filename: 'Surface-Laptop-Ultra-Capability-EP2-56927.pdf' });
  assert.equal(request.filePath, '/user/Surface-Laptop-Ultra-Capability-EP2-56927.pdf');
}
process.stdout.write('Mini-program PDF report checks passed.\n');
{
  let request;
  const page=loadPage({env:{USER_DATA_PATH:'/user'},downloadFile(options){request=options;}});
  page.onLoad({kind:'workplace',ticket:'e'.repeat(43),filename:'Surface-Workplace-Budget-123abc.pdf'});
  assert.equal(request.url,'https://surfacedmp.com/api/commercial/public/budget-download/'+'e'.repeat(43));
  assert.equal(request.filePath,'/user/Surface-Workplace-Budget-123abc.pdf');
}
