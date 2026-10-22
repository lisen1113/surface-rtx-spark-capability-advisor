const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const page = fs.readFileSync(path.join(__dirname, '..', 'backend', 'app', 'assets', 'guest.html'), 'utf8');
const script = page.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(script, 'guest page must contain its application script');
new vm.Script(script[1], { filename: 'guest.html' });
assert.match(page, /id="need-form"/);
assert.match(page, /id="description"/);
assert.match(page, /本次识别的需求/);
assert.match(page, /\/api\/guest\/recommendations/);
console.log('Guest page script and recommendation UI checks passed.');
