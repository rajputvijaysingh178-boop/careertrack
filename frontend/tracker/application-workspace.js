const APPLICATION_REMINDER_TYPES = [
  ['INTERVIEW', 'Interview'],
  ['FOLLOW_UP', 'Follow-up'],
  ['APPLICATION_DEADLINE', 'Application Deadline'],
  ['PREPARATION', 'Preparation'],
  ['HR_CALL', 'HR Call'],
  ['DOCUMENT_SUBMISSION', 'Document Submission'],
];

function mergeCreatedApplication(applications, created) {
  return [created, ...(applications || []).filter(application => application.id !== created.id)];
}

async function submitApplicationAndRefresh({api, payload, isAdmin, refresh, onCreated}) {
  const body = {...payload};
  let route = '/applications';
  if (isAdmin) {
    route = '/admin/applications';
    body.user_id = Number(body.user_id);
  } else {
    // Ownership for a regular user always comes from the authenticated token.
    delete body.user_id;
  }
  const created = await api(route, {method: 'POST', body: JSON.stringify(body)});
  if (!isAdmin) onCreated?.(created);
  let refreshed = false;
  try { refreshed = Boolean(await refresh()); } catch { refreshed = false; }
  return {created, refreshed};
}

function renderReminderTypeOptions(selected = 'FOLLOW_UP', escapeHtml = value => String(value)) {
  return APPLICATION_REMINDER_TYPES.map(([value, label]) => `<option value="${escapeHtml(value)}" ${selected === value ? 'selected' : ''}>${escapeHtml(label)}</option>`).join('');
}

function renderDocumentReference(document, escapeHtml) {
  const type = document.doc_type || 'Document reference';
  return `<div class="detail-item"><a href="${escapeHtml(document.file_url)}" target="_blank" rel="noopener">${escapeHtml(document.name)}</a><small>${escapeHtml(type)} - Link/reference only</small></div>`;
}

function renderApplicationPrepResources(workspace, skillGap, escapeHtml) {
  if (!workspace) return '<p class="empty">Preparation resources could not be loaded.</p>';
  const questions = Object.entries(workspace.questions?.by_category || {});
  const questionHtml = questions.length ? questions.map(([category, rows]) => `<details><summary>${escapeHtml(category)} - ${rows.length}</summary>${rows.map(question => `<div class="detail-item"><strong>${escapeHtml(question.question)}</strong><small>${escapeHtml(question.difficulty || 'Difficulty not set')}${question.round ? ` - ${escapeHtml(question.round)}` : ''}${question.expected_topics?.length ? `<br>Topics: ${question.expected_topics.map(escapeHtml).join(', ')}` : ''}</small></div>`).join('')}</details>`).join('') : '<p class="empty">No related interview questions yet.</p>';
  const materials = workspace.materials || [];
  const materialHtml = materials.length ? materials.map(material => `<div class="detail-item"><button class="small-button" type="button" data-material-open="${Number(material.id)}">${escapeHtml(material.title || 'Study material')}</button><small>${escapeHtml(material.type || 'Resource')}${material.description ? ` - ${escapeHtml(material.description)}` : ''}</small></div>`).join('') : '<p class="empty">No related study materials yet.</p>';
  const blogs = workspace.blogs || [];
  const blogHtml = blogs.length ? blogs.map(blog => `<details><summary>${escapeHtml(blog.title || 'Preparation article')}${blog.category ? ` - ${escapeHtml(blog.category)}` : ''}</summary><div class="detail-item">${escapeHtml(blog.content || 'Article content is unavailable.')}</div></details>`).join('') : '<p class="empty">No related blogs or preparation guides yet.</p>';
  const gapHtml = skillGap ? `<p><strong>${Math.round(skillGap.match_percent || 0)}% skill match</strong></p><div class="skill-tags">${(skillGap.missing || []).map(skill => `<span class="missing">Practice - ${escapeHtml(skill.name)}</span>`).join('') || '<span>No identified skill gaps.</span>'}</div>${(skillGap.study_next || []).map(item => `<div class="detail-item"><strong>${escapeHtml(item.skill)}</strong><small>${(item.topics || []).map(escapeHtml).join(' - ')}</small></div>`).join('')}` : '<p class="empty">Skill-gap analysis is unavailable.</p>';
  return `<section class="application-prep-resources"><h3>Skill-gap preparation</h3>${gapHtml}<h3>Interview questions</h3>${questionHtml}<h3>Study materials</h3>${materialHtml}<h3>Blogs and preparation guides</h3>${blogHtml}</section>`;
}

if (typeof module !== 'undefined' && module.exports) module.exports = {
  APPLICATION_REMINDER_TYPES,
  mergeCreatedApplication,
  submitApplicationAndRefresh,
  renderReminderTypeOptions,
  renderDocumentReference,
  renderApplicationPrepResources,
};
