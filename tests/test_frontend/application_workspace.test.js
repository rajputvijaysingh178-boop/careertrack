const test = require('node:test');
const assert = require('node:assert/strict');
const {
  APPLICATION_REMINDER_TYPES,
  renderReminderTypeOptions,
  renderDocumentReference,
  renderApplicationPrepResources,
} = require('../../frontend/tracker/application-workspace.js');

const escapeHtml = value => String(value).replace(/[&<>"']/g, character => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[character]));

test('reminder selector exposes only the requirement-supported reminder types', () => {
  assert.deepEqual(APPLICATION_REMINDER_TYPES.map(([value]) => value), [
    'INTERVIEW', 'FOLLOW_UP', 'APPLICATION_DEADLINE', 'PREPARATION', 'HR_CALL', 'DOCUMENT_SUBMISSION',
  ]);
  const html = renderReminderTypeOptions('HR_CALL', escapeHtml);
  assert.match(html, /value="HR_CALL" selected/);
  assert.equal((html.match(/<option/g) || []).length, APPLICATION_REMINDER_TYPES.length);
});

test('document display communicates that the API stores a reference, not an upload', () => {
  const html = renderDocumentReference({
    name: 'Resume', file_url: '/uploads/resume.pdf', doc_type: 'Resume',
  }, escapeHtml);
  assert.match(html, /href="\/uploads\/resume\.pdf"/);
  assert.match(html, /Link\/reference only/);
  assert.match(html, /Resume/);
});

test('application workspace renders related questions, material download, blog content, and skill gaps safely', () => {
  const html = renderApplicationPrepResources({
    questions: { by_category: { Python: [{ question: '<script>x</script>', difficulty: 'MEDIUM' }] } },
    materials: [{ id: 12, title: 'Python guide', type: 'ARTICLE', description: 'Basics' }],
    blogs: [{ title: 'Interview guide', content: '<img src=x onerror=alert(1)>' }],
  }, { match_percent: 75, missing: [{ name: 'SQL' }], study_next: [] }, escapeHtml);
  assert.match(html, /data-material-open="12"/);
  assert.match(html, /&lt;script&gt;x&lt;\/script&gt;/);
  assert.match(html, /&lt;img src=x onerror=alert\(1\)&gt;/);
  assert.match(html, /75% skill match/);
  assert.match(html, /SQL/);
  assert.doesNotMatch(html, /<script>|<img/);
});

test('application workspace provides explicit empty states when no resources match', () => {
  const html = renderApplicationPrepResources({ questions: { by_category: {} }, materials: [], blogs: [] }, null, escapeHtml);
  assert.match(html, /No related interview questions yet/);
  assert.match(html, /No related study materials yet/);
  assert.match(html, /No related blogs or preparation guides yet/);
  assert.match(html, /Skill-gap analysis is unavailable/);
});
