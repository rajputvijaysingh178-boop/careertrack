const test = require('node:test');
const assert = require('node:assert/strict');
const {
  prepApplicationRows,
  renderPrepApplicationOptions,
} = require('../../frontend/tracker/prep-roles.js');

const escapeHtml = value => String(value).replace(/[&<>"']/g, character => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[character]));

test('preparation dropdown renders the authenticated applications API array', () => {
  const rows = [{
    id: 1,
    job_title: 'python devloper',
    company_name: null,
    status: 'SHORTLISTED',
  }];

  assert.deepEqual(prepApplicationRows(rows), rows);
  assert.equal(
    renderPrepApplicationOptions(rows, 'application:1', escapeHtml),
    '<option value="application:1" selected>python devloper - Application (SHORTLISTED)</option>',
  );
});

test('preparation dropdown also accepts a paginated application response', () => {
  const rows = [{ id: 2, job_title: 'Backend Engineer', status: 'APPLIED' }];
  assert.deepEqual(prepApplicationRows({ items: rows, total: 1 }), rows);
  assert.match(
    renderPrepApplicationOptions({ items: rows }, '', escapeHtml),
    /application:2.*Backend Engineer/,
  );
});

test('preparation dropdown rejects unrecognized response shapes instead of throwing', () => {
  assert.equal(prepApplicationRows({ data: [] }), null);
  assert.equal(renderPrepApplicationOptions({ data: [] }, '', escapeHtml), null);
});
