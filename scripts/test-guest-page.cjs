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
for (const id of ['ai-size', 'game-need', 'work-need', 'generation-need', 'model-name', 'game-titles', 'target-resolution', 'target-fps', 'software-name']) {
  assert.match(page, new RegExp(`id="${id}"`));
}
assert.match(page, /target_fps:usages\.includes\('gaming'\)/);
assert.doesNotMatch(page, /budget_cny:/);
assert.match(page, /本次识别的需求/);
assert.match(page, /\/api\/guest\/recommendations/);
console.log('Guest page script and recommendation UI checks passed.');
