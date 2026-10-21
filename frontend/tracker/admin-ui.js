function renderAdminDashboard(stats, escapeHtml) {
  const metric = (label, value) => `<div class="metric"><span>${escapeHtml(label)}</span><strong>${Number(value || 0)}</strong></div>`;
  const group = (title, entries) => `<section class="panel prep-panel"><h3>${escapeHtml(title)}</h3><div class="admin-stat-grid">${Object.entries(entries || {}).map(([key, value]) => metric(key.replaceAll('_', ' '), value)).join('')}</div></section>`;
  return `<div class="admin-grid admin-dashboard">${group('Users', stats.users)}${group('Jobs', stats.jobs)}<section class="panel prep-panel"><h3>Platform content</h3><div class="admin-stat-grid">${metric('Companies', stats.companies)}${metric('Applications', stats.applications)}${metric('Interviews tracked', stats.interviews_tracked)}${metric('Offers recorded', stats.offers_recorded)}${metric('Interview questions', stats.interview_questions)}${metric('Materials', stats.materials)}${metric('Blogs', stats.blogs?.total)}${metric('Published blogs', stats.blogs?.published)}</div></section></div>`;
}

function renderAdminUsers(payload, currentUserId, escapeHtml) {
  if (!payload || !Array.isArray(payload.items)) return '<p class="error">The user list response was invalid.</p>';
  if (!payload.items.length) return '<p class="empty">No users match these filters.</p>';
  const rows = payload.items.map(user => {
    const self = Number(user.id) === Number(currentUserId);
    const created = user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Not available';
    const contact = [user.phone, user.location].filter(Boolean).map(escapeHtml).join(' · ');
    return `<article class="admin-user-row"><div class="admin-user-info"><strong>${escapeHtml(user.name)}</strong><small>${escapeHtml(user.email)} · ID ${Number(user.id)} · Joined ${escapeHtml(created)}${contact ? ` · ${contact}` : ''}</small></div><span class="badge">${escapeHtml(user.role)}</span><span class="badge">${escapeHtml(user.status)}</span><label>Role<select data-user-role="${Number(user.id)}" ${self ? 'disabled' : ''}><option value="USER" ${user.role === 'USER' ? 'selected' : ''}>USER</option><option value="ADMIN" ${user.role === 'ADMIN' ? 'selected' : ''}>ADMIN</option></select></label><button class="small-button" data-save-role="${Number(user.id)}" ${self ? 'disabled' : ''}>Update role</button><button class="small-button" data-user-status="${Number(user.id)}" data-next-status="${user.status === 'ACTIVE' ? 'BLOCKED' : 'ACTIVE'}" ${self ? 'disabled' : ''}>${user.status === 'ACTIVE' ? 'Block account' : 'Activate account'}</button>${self ? '<small>Your own role and account status cannot be changed here.</small>' : ''}</article>`;
  }).join('');
  const start = Number(payload.total) ? Number(payload.skip || 0) + 1 : 0;
  const end = Math.min(Number(payload.skip || 0) + payload.items.length, Number(payload.total || payload.items.length));
  return `<div class="admin-user-list">${rows}</div><div class="admin-pagination"><span>Showing ${start}–${end} of ${Number(payload.total || 0)}</span><button class="small-button" id="admin-users-prev" ${Number(payload.skip || 0) <= 0 ? 'disabled' : ''}>Previous</button><button class="small-button" id="admin-users-next" ${end >= Number(payload.total || 0) ? 'disabled' : ''}>Next</button></div>`;
}

function renderAdminReports(reports, escapeHtml) {
  if (!reports || typeof reports !== 'object') return '<p class="error">The reports response was invalid.</p>';
  const display = value => typeof value === 'number' ? value : escapeHtml(value ?? 'Unspecified');
  const section = (title, value) => {
    let rows;
    if (Array.isArray(value)) rows = value.map(row => [row.company || row.label || 'Item', row.jobs ?? row.count ?? '']);
    else rows = Object.entries(value || {});
    if (!rows.length) return `<section class="analytics-box"><h3>${escapeHtml(title)}</h3><p class="empty">No data yet.</p></section>`;
    const max = Math.max(1, ...rows.map(([, n]) => Number(n) || 0));
    return `<section class="analytics-box"><h3>${escapeHtml(title.replaceAll('_', ' '))}</h3>${rows.map(([label, count]) => `<div class="bar-row"><span>${escapeHtml(label)}</span><div class="bar"><i style="width:${Math.max(Number(count) ? Number(count) * 100 / max : 0, Number(count) ? 3 : 0)}%"></i></div><b>${display(count)}</b></div>`).join('')}</section>`;
  };
  return `<div class="analytics-grid">${section('Jobs by status', reports.jobs_by_status)}${section('Jobs by type', reports.jobs_by_type)}${section('Jobs by work mode', reports.jobs_by_work_mode)}${section('Jobs by employment type', reports.jobs_by_employment_type)}${section('Top companies', reports.top_companies)}${section('Jobs posted per month', reports.jobs_posted_per_month)}${section('Applications by status', reports.applications_by_status)}</div>`;
}

function renderAdminCompanies(companies, escapeHtml) {
  if (!companies.length) return '<p class="empty">No companies yet.</p>';
  return companies.map(company => `<article class="admin-entity"><div class="admin-row"><span><strong>${escapeHtml(company.name)}</strong><small>${escapeHtml(company.industry || 'Industry not set')} · ${escapeHtml(company.location || 'Location not set')} · ${escapeHtml(company.status)} · ${Number(company.active_jobs || 0)} active jobs</small></span><details><summary class="small-button">Edit</summary><form data-company-edit="${Number(company.id)}"><label>Name<input name="name" required maxlength="200" value="${escapeHtml(company.name)}"></label><label>Website<input name="website" type="url" maxlength="300" value="${escapeHtml(company.website || '')}"></label><label>Industry<input name="industry" maxlength="100" value="${escapeHtml(company.industry || '')}"></label><label>Location<input name="location" maxlength="150" value="${escapeHtml(company.location || '')}"></label><label>Size<input name="company_size" maxlength="50" value="${escapeHtml(company.company_size || '')}"></label><label>Description<textarea name="description">${escapeHtml(company.description || '')}</textarea></label><label>Status<select name="status"><option ${company.status === 'ACTIVE' ? 'selected' : ''}>ACTIVE</option><option ${company.status === 'INACTIVE' ? 'selected' : ''}>INACTIVE</option></select></label><button class="small-button">Save company</button></form></details><button class="small-button" data-delete-company="${Number(company.id)}" ${Number(company.active_jobs || 0) ? 'disabled' : ''}>Delete</button></div>${Number(company.active_jobs || 0) ? '<small>Companies with jobs cannot be deleted; set the company INACTIVE instead.</small>' : ''}</article>`).join('');
}

function renderAdminJobs(jobs, companies, escapeHtml) {
  if (!jobs.length) return '<p class="empty">No jobs yet.</p>';
  const companyOptions = job => companies.filter(company => company.status === 'ACTIVE' || Number(company.id) === Number(job.company?.id)).map(company => `<option value="${Number(company.id)}" ${Number(company.id) === Number(job.company?.id) ? 'selected' : ''}>${escapeHtml(company.name)}${company.status === 'INACTIVE' ? ' (inactive current company)' : ''}</option>`).join('');
  const statuses = job => {
    const actions = {
      DRAFT: [['publish', 'Publish'], ['close', 'Close']],
      PUBLISHED: [['close', 'Close'], ['expire', 'Expire'], ['unpublish', 'Return to draft']],
      ACTIVE: [['close', 'Close'], ['expire', 'Expire'], ['unpublish', 'Return to draft']],
      EXPIRED: [['reopen', 'Reopen'], ['close', 'Close'], ['unpublish', 'Return to draft']],
      CLOSED: [['unpublish', 'Return to draft']],
    }[job.status] || [];
    return actions.map(([action, label]) => action === 'reopen'
      ? `<form data-job-reopen="${Number(job.id)}"><label>New expiry date (optional)<input name="expiry_date" type="date" min="${new Date().toISOString().slice(0, 10)}" value="${escapeHtml(job.expiry_date || '')}"></label><button class="small-button">${label}</button></form>`
      : `<button class="small-button" data-job-action="${action}" data-job-id="${Number(job.id)}">${label}</button>`).join('');
  };
  return jobs.map(job => `<article class="admin-entity"><div class="admin-row"><span><strong>${escapeHtml(job.title)}</strong><small>${escapeHtml(job.company?.name || 'Company not set')} · ${escapeHtml(job.status)} · Expires ${escapeHtml(job.expiry_date || 'not set')}</small></span><details><summary class="small-button">Edit</summary><form data-job-edit="${Number(job.id)}"><label>Company<select name="company_id">${companyOptions(job)}</select></label><label>Title<input name="title" required minlength="3" maxlength="200" value="${escapeHtml(job.title)}"></label><label>Description<textarea name="description" required minlength="20">${escapeHtml(job.description || '')}</textarea></label><label>Location<input name="location" value="${escapeHtml(job.location || '')}"></label><div class="form-row"><label>Work mode<select name="work_mode"><option value="">Unspecified</option>${['REMOTE', 'HYBRID', 'ONSITE'].map(value => `<option ${job.work_mode === value ? 'selected' : ''}>${value}</option>`).join('')}</select></label><label>Employment<select name="employment_type"><option value="">Unspecified</option>${['FULL_TIME', 'PART_TIME', 'CONTRACT', 'INTERNSHIP', 'FREELANCE'].map(value => `<option ${job.employment_type === value ? 'selected' : ''}>${value}</option>`).join('')}</select></label></div><div class="form-row"><label>Minimum experience<input name="experience_min" type="number" min="0" max="60" value="${job.experience_min ?? ''}"></label><label>Maximum experience<input name="experience_max" type="number" min="0" max="60" value="${job.experience_max ?? ''}"></label></div><div class="form-row"><label>Minimum salary<input name="salary_min" type="number" min="0" step="0.1" value="${job.salary_min ?? ''}"></label><label>Maximum salary<input name="salary_max" type="number" min="0" step="0.1" value="${job.salary_max ?? ''}"></label></div><div class="form-row"><label>Posted date<input name="posted_date" type="date" value="${escapeHtml(job.posted_date || '')}"></label><label>Expiry date<input name="expiry_date" type="date" value="${escapeHtml(job.expiry_date || '')}"></label></div><label>Application URL<input name="application_url" type="url" value="${escapeHtml(job.application_url || '')}"></label><label>Skills · comma separated<input name="skills" value="${escapeHtml((job.skills || []).map(skill => skill.name).join(', '))}"></label><button class="small-button">Save job</button></form></details>${statuses(job)}<button class="small-button" data-delete-job="${Number(job.id)}">Delete</button></div></article>`).join('');
}

if (typeof module !== 'undefined' && module.exports) module.exports = { renderAdminDashboard, renderAdminUsers, renderAdminReports, renderAdminCompanies, renderAdminJobs };
