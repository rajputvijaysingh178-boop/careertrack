function renderPrepPlanResponse(response, escapeHtml) {
  if (!response || !Array.isArray(response.plan)) {
    throw new TypeError('Preparation plan response must include a plan array.');
  }
  if (!Number.isInteger(response.days) || response.days !== response.plan.length) {
    throw new TypeError('Preparation plan response has an inconsistent day count.');
  }

  const entries = response.plan.map((day, index) => {
    if (!day || typeof day !== 'object' || Array.isArray(day)
      || !Number.isInteger(day.day) || typeof day.title !== 'string'
      || !Array.isArray(day.topics) || !Array.isArray(day.tasks)) {
      throw new TypeError(`Preparation plan day ${index + 1} has an invalid shape.`);
    }
    const topics = day.topics.length
      ? `<small>Topics: ${day.topics.map(topic => escapeHtml(String(topic))).join(', ')}</small>`
      : '';
    const tasks = day.tasks.length
      ? `<ul>${day.tasks.map(task => `<li>${escapeHtml(String(task))}</li>`).join('')}</ul>`
      : '';
    return `<article class="detail-item"><strong>Day ${day.day}: ${escapeHtml(day.title)}</strong>${topics}${tasks}</article>`;
  }).join('');

  const role = response.role ? `${escapeHtml(response.role)} · ` : '';
  const source = response.source ? ` (${escapeHtml(response.source)})` : '';
  return `<h4>${role}Preparation plan · ${response.days} days${source}</h4>${entries}`;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { renderPrepPlanResponse };
}
