function prepApplicationRows(payload) {
  if (Array.isArray(payload)) return payload;
  if (payload && Array.isArray(payload.items)) return payload.items;
  return null;
}

function renderPrepApplicationOptions(payload, selected, escapeHtml) {
  const rows = prepApplicationRows(payload);
  if (rows === null) return null;
  return rows.map(application => {
    const value = `application:${application.id}`;
    const label = `${application.job_title || 'Untitled role'} - ${application.company_name || 'Application'} (${application.status || 'UNKNOWN'})`;
    return `<option value="${escapeHtml(value)}" ${selected === value ? 'selected' : ''}>${escapeHtml(label)}</option>`;
  }).join('');
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { prepApplicationRows, renderPrepApplicationOptions };
}
