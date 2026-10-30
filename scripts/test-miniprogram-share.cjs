const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.join(__dirname, '..', 'miniprogram');
const config = JSON.parse(fs.readFileSync(path.join(root, 'app.json'), 'utf8'));
const home = '/pages/home/index';
assert.ok(config.pages.includes(home.slice(1)));

for (const route of ['home', 'guest', 'company', 'advisor']) {
  const source = fs.readFileSync(path.join(root, 'pages', route, 'index.js'), 'utf8');
  let page;
  let menus;
  vm.runInNewContext(source, {
    Page(definition) { page = definition; },
    wx: { showShareMenu(options) { menus = Array.from(options.menus); } },
  });
  page.onShow();
  assert.deepEqual(menus, ['shareAppMessage', 'shareTimeline'], route);
  const message = page.onShareAppMessage();
  assert.equal(message.path, home, route);
  assert.match(message.title, /上海以和信息技术/, route);
  assert.match(page.onShareTimeline().title, /上海以和信息技术/, route);
}

console.log('Public mini-program share routes passed.');
