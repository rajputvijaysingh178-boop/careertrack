const test = require('node:test');
const assert = require('node:assert/strict');
const { renderAdminDashboard, renderAdminUsers, renderAdminReports, renderAdminCompanies, renderAdminJobs } = require('../../frontend/tracker/admin-ui.js');
const { renderSkillManager, renderQuestionManager, renderMaterialManager, renderAdminBlogs } = require('../../frontend/tracker/admin-content.js');

const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

test('admin dashboard renders nested statistics and platform counts', () => {
  const html = renderAdminDashboard({ users: { total: 8, admins: 1, blocked: 2 }, jobs: { total: 5, active: 3 }, companies: 4, applications: 9, interviews_tracked: 2, offers_recorded: 1, interview_questions: 7, materials: 6, blogs: { total: 3, published: 2 } }, esc);
  for (const label of ['Users', 'Jobs', 'Platform content', 'blocked', 'Active', 'Applications', 'Published blogs']) assert.match(html, new RegExp(label, 'i'));
  assert.match(html, />9<\/strong>/);
});

test('admin user view exposes supported roles/statuses and disables self-management', () => {
  const html = renderAdminUsers({ items: [{ id: 1, name: 'Admin', email: 'admin@example.test', role: 'ADMIN', status: 'ACTIVE' }, { id: 2, name: '<User>', email: 'user@example.test', role: 'USER', status: 'BLOCKED' }], total: 2, skip: 0 }, 1, esc);
  assert.match(html, /Update role/);
  assert.match(html, /Block account/);
  assert.match(html, /Activate account/);
  assert.match(html, /&lt;User&gt;/);
  assert.match(html, /data-save-role="1" disabled/);
  assert.match(html, /data-user-status="1"[^>]*disabled/);
  assert.match(html, /Showing 1–2 of 2/);
});

test('admin users and reports render explicit empty states', () => {
  assert.match(renderAdminUsers({ items: [], total: 0, skip: 0 }, 1, esc), /No users match/);
  assert.match(renderAdminReports({ jobs_by_status: {}, jobs_by_type: {}, jobs_by_work_mode: {}, jobs_by_employment_type: {}, top_companies: [], jobs_posted_per_month: {}, applications_by_status: {} }, esc), /No data yet/);
});

test('admin reports render the existing report endpoint response contract', () => {
  const html = renderAdminReports({ jobs_by_status: { ACTIVE: 4 }, jobs_by_type: { Backend: 2 }, jobs_by_work_mode: { REMOTE: 3 }, jobs_by_employment_type: { FULL_TIME: 2 }, top_companies: [{ company: 'Example', jobs: 5 }], jobs_posted_per_month: { '2026-10': 2 }, applications_by_status: { APPLIED: 3 } }, esc);
  for (const text of ['ACTIVE', 'Backend', 'REMOTE', 'FULL_TIME', 'Example', '2026-10', 'APPLIED']) assert.ok(html.includes(text));
});

test('company management renders edit and guarded delete controls from the companies API shape', () => {
  const html = renderAdminCompanies([
    { id: 1, name: 'Company A', industry: 'Software', status: 'ACTIVE', active_jobs: 0 },
    { id: 2, name: 'Company B', status: 'ACTIVE', active_jobs: 2 },
  ], esc);
  assert.match(html, /data-company-edit="1"/);
  assert.match(html, /data-delete-company="1"/);
  assert.match(html, /data-delete-company="2" disabled/);
  assert.match(html, /set the company INACTIVE instead/);
});

test('job management exposes supported edit and lifecycle controls', () => {
  const jobs = [
    { id: 1, title: 'Draft role', status: 'DRAFT', company: { id: 10, name: 'A' }, skills: [] },
    { id: 2, title: 'Active role', status: 'ACTIVE', company: { id: 10, name: 'A' }, skills: [{ name: 'Python', importance: 'PREFERRED' }] },
    { id: 3, title: 'Expired role', status: 'EXPIRED', company: { id: 10, name: 'A' }, expiry_date: '2020-01-01', skills: [] },
  ];
  const html = renderAdminJobs(jobs, [{ id: 10, name: 'A', status: 'ACTIVE' }], esc);
  assert.match(html, /data-job-edit="2"/);
  assert.match(html, /data-job-action="publish" data-job-id="1"/);
  assert.match(html, /data-job-action="close" data-job-id="2"/);
  assert.match(html, /data-job-action="expire" data-job-id="2"/);
  assert.match(html, /data-job-action="unpublish" data-job-id="2"/);
  assert.match(html, /data-job-reopen="3"/);
  assert.match(html, /name="expiry_date" type="date"/);
  assert.match(html, /value="Python"/);
});

test('skill admin UI lists and edits skill categories using the supported label field', () => {
  const html = renderSkillManager([{ id: 7, name: 'Python', category: 'Backend' }], ['Backend']);
  assert.match(html, /id="admin-skill-form"/);
  assert.match(html, /data-skill-edit="7"/);
  assert.match(html, /data-skill-delete="7"/);
  assert.match(html, /value="Backend"/);
  assert.match(html, /does not provide standalone category create, rename, or delete operations/i);
});

test('question manager exposes supported company, job, and skill associations', () => {
  const html = renderQuestionManager([{ id: 4, category: 'Python', question: 'Explain generators', difficulty: 'MEDIUM', expected_topics: ['yield'], company_id: 2, job_id: 3, skill_id: 5 }], [{ id: 2, name: 'Co' }], [{ id: 3, title: 'Engineer' }], [{ id: 5, name: 'Python' }]);
  assert.match(html, /data-question-edit="4"/);
  assert.match(html, /data-question-delete="4"/);
  assert.match(html, /name="company_id"/);
  assert.match(html, /name="job_id"/);
  assert.match(html, /name="skill_id"/);
  assert.match(html, /name="expected_topics"/);
});

test('material admin UI supports link editing, uploads, and role/round/skill/job/company targeting', () => {
  const html = renderMaterialManager([{ id: 8, title: 'Guide PDF', type: 'PDF', file_url: 'uploads/materials/guide.pdf', skill_id: 5 }], [{ id: 2, name: 'Co' }], [{ id: 3, title: 'Engineer' }], [{ id: 5, name: 'Python' }]);
  assert.match(html, /id="admin-material-form"/);
  assert.match(html, /id="admin-material-upload"/);
  assert.match(html, /data-material-edit="8"/);
  assert.match(html, /data-material-delete="8"/);
  for (const name of ['skill_id', 'job_id', 'company_id', 'role', 'interview_round']) assert.ok(html.includes(`name="${name}"`));
  assert.match(html, /Stored file: uploads\/materials\/guide.pdf/);
});

test('blogs and guides are listed separately and guide content is clearly labelled', () => {
  const html = renderAdminBlogs([
    { id: 1, title: 'Interview guide', category: 'Preparation Guide', status: 'DRAFT', content: 'Prepare carefully.', tags: [] },
    { id: 2, title: 'Company news', category: 'Blog', status: 'PUBLISHED', content: 'News update.', tags: [] },
  ]);
  assert.match(html, /Preparation guides \(1\)/);
  assert.match(html, /PREPARATION GUIDE/);
  assert.match(html, /Other blogs \(1\)/);
  assert.match(html, /data-blog-edit="1"/);
  assert.match(html, /data-blog-delete="2"/);
  assert.match(html, /value="Preparation Guide"/);
});

test('career content managers render explicit empty states', () => {
  assert.match(renderSkillManager([], []), /No skills yet/);
  assert.match(renderQuestionManager([], [], [], []), /No interview questions yet/);
  assert.match(renderMaterialManager([], [], [], []), /No study materials yet/);
  assert.match(renderAdminBlogs([]), /No preparation guides yet/);
  assert.match(renderAdminBlogs([]), /No other blog content yet/);
});
