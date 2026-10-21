const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.join(__dirname, '../miniprogram');
const config = JSON.parse(fs.readFileSync(path.join(root, 'app.json'), 'utf8'));
assert.equal(config.pages[0], 'pages/home/index');
for (const route of ['pages/home/index', 'pages/company/index', 'pages/advisor/index', 'pages/report/index']) {
  assert.ok(config.pages.includes(route));
  assert.ok(fs.existsSync(path.join(root, route + '.js')));
  assert.ok(fs.existsSync(path.join(root, route + '.wxml')));
}

const home = fs.readFileSync(path.join(root, 'pages/home/index.wxml'), 'utf8');
assert.match(home, /url="\/pages\/company\/index"/);
assert.match(home, /url="\/pages\/advisor\/index"/);
assert.match(home, /需登录并通过授权/);

function pageData(route) {
  let definition;
  vm.runInNewContext(fs.readFileSync(path.join(root, route + '.js'), 'utf8'), {
    Page: (page) => { definition = page; }
  });
  return definition.data;
}

assert.equal(pageData('pages/company/index').companyUrl, 'https://yiheit.net/');
assert.equal(pageData('pages/advisor/index').advisorUrl, 'https://surfacedmp.com/account');
process.stdout.write('Mini-program landing navigation checks passed.\n');
