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

process.stdout.write('Mini-program PDF report checks passed.\n');
