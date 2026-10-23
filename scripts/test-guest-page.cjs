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

// Exercise the real submit handler with a minimal DOM. Syntax-only checks
// missed regressions where the visible guest form never sent detailed needs.
const listeners = new Map();
const nodes = new Map();
const checked = new Set(['ai', 'gaming', 'generation', 'productivity']);
const values = {
  'description': '本地模型和编程', 'ai-size': '32B', 'model-name': 'Example Model',
  'game-need': 'aaa', 'game-titles': 'Example Game',
  'target-resolution': '1080p', 'target-fps': '60',
  'generation-need': 'image', 'work-need': 'coding', 'software-name': 'Example IDE',
};
function node(id) {
  if (!nodes.has(id)) nodes.set(id, {
    value: values[id] || '', textContent: '', hidden: false,
    addEventListener(type, callback) { listeners.set(`${id}:${type}`, callback); },
    replaceChildren() {}, append() {},
    querySelectorAll() { return []; },
  });
  return nodes.get(id);
}
let posted;
const sandbox = {
  URL,
  document: {
    getElementById: node,
    createElement: () => ({ append() {}, addEventListener() {}, set textContent(value) { this.text = value; } }),
    querySelectorAll(selector) {
      if (selector === 'input[name="usage"]:checked') return [...checked].map(value => ({ value }));
      if (selector === 'input[name="usage"]') return [...checked].map(() => ({ addEventListener() {} }));
      return [];
    },
    querySelector(selector) {
      const usage = selector.match(/value="([^"]+)"/);
      return usage && checked.has(usage[1]) ? {} : null;
    },
  },
  fetch: async (url, options) => {
    if (url === '/api/guest/skus') return { ok: true, json: async () => ({ items: [] }) };
    if (url === '/api/guest/recommendations') {
      posted = JSON.parse(options.body);
      return { ok: true, json: async () => ({ message: 'ok', items: [] }) };
    }
    throw new Error(`Unexpected request: ${url}`);
  },
};
vm.runInNewContext(script[1], sandbox, { filename: 'guest.html' });
(async () => {
  await listeners.get('need-form:submit')({ preventDefault() {} });
  assert.equal(posted.ai_size, '32B');
  assert.equal(posted.target_fps, 60);
  assert.equal(posted.generation_need, 'image');
  assert.equal(posted.software_name, 'Example IDE');
  assert.equal(posted.budget_cny, undefined);
  checked.delete('gaming');
  await listeners.get('need-form:submit')({ preventDefault() {} });
  assert.equal(posted.game_need, 'unsure');
  assert.equal(posted.game_titles, '');
  assert.equal(posted.target_fps, null);
  console.log('Guest page script and interactive recommendation checks passed.');
})().catch(error => { console.error(error); process.exitCode = 1; });
