const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {buildApiUrl, apiFetch} = require('../../frontend/tracker/api-client.js');

test('API URL uses the same origin when no public API base is configured', () => {
  globalThis.CAREERTRACK_API_BASE_URL = '';
  assert.equal(buildApiUrl('/applications?limit=20'), '/applications?limit=20');
  assert.equal(buildApiUrl('auth/me'), '/auth/me');
});

test('API URL joins routes to the configured Render origin without duplicate slashes', () => {
  globalThis.CAREERTRACK_API_BASE_URL = 'https://careertrack-api.example.onrender.com/';
  assert.equal(
    buildApiUrl('/applications?limit=20'),
    'https://careertrack-api.example.onrender.com/applications?limit=20',
  );
});

test('served local browser config routes the login request to FastAPI on port 8000', async () => {
  const tracker = path.join(__dirname, '../../frontend/tracker');
  const browser = {Headers, fetch: async url => ({url})};
  const context = {window: browser, Headers};
  vm.runInNewContext(fs.readFileSync(path.join(tracker, 'api-config.js'), 'utf8'), context);
  vm.runInNewContext(fs.readFileSync(path.join(tracker, 'api-client.js'), 'utf8'), context);

  const response = await browser.CareerTrackApi.apiFetch('/auth/login/json', {method: 'POST'});
  assert.equal(response.url, 'http://127.0.0.1:8000/auth/login/json');
});

test('shared request helper preserves request options and sends the bearer token', async () => {
  globalThis.CAREERTRACK_API_BASE_URL = 'https://careertrack-api.example.onrender.com';
  const body = new FormData();
  body.append('resume_text', 'test');
  let captured;
  const fakeFetch = async (...args) => { captured = args; return {ok: true}; };

  const response = await apiFetch('/resume-match', {method: 'POST', body}, 'test-token', fakeFetch);

  assert.deepEqual(response, {ok: true});
  assert.equal(captured[0], 'https://careertrack-api.example.onrender.com/resume-match');
  assert.equal(captured[1].method, 'POST');
  assert.equal(captured[1].body, body);
  assert.equal(captured[1].headers.get('Authorization'), 'Bearer test-token');
  assert.equal(captured[1].headers.has('Content-Type'), false, 'multipart boundary must be set by the browser');
});

test('Vercel-root document uses relative assets, root brand link, and loads the API client first', () => {
  const html = fs.readFileSync(path.join(__dirname, '../../frontend/tracker/index.html'), 'utf8');
  assert.match(html, /href="\.\/"/);
  assert.doesNotMatch(html, /(?:href|src)="\/tracker\//);
  assert.match(html, /src="\.\/api-config\.js\?v=api-base-8000-1" defer><\/script>\s*<script src="\.\/api-client\.js" defer><\/script>\s*<script src="\.\/application-workspace\.js" defer><\/script>\s*<script src="\.\/app\.js" defer>/);
});

test('all frontend fetch calls go through the shared API URL and auth helper', () => {
  const frontend = path.join(__dirname, '../../frontend/tracker');
  const jsFiles = fs.readdirSync(frontend).filter(name => name.endsWith('.js'));
  const rawFetchFiles = jsFiles.filter(name => {
    const source = fs.readFileSync(path.join(frontend, name), 'utf8');
    return /\bfetch\s*\(/.test(source) && name !== 'api-client.js';
  });
  assert.deepEqual(rawFetchFiles, []);
});

test('registration submit is wired to exactly one handler', () => {
  const frontend = path.join(__dirname, '../../frontend/tracker');
  const jsFiles = fs.readdirSync(frontend).filter(name => name.endsWith('.js'));
  const registrations = jsFiles.flatMap(name => {
    const source = fs.readFileSync(path.join(frontend, name), 'utf8');
    return [...source.matchAll(/api\(['"]\/auth\/register['"]/g)].map(() => name);
  });
  assert.deepEqual(registrations, ['extra.js']);
});
