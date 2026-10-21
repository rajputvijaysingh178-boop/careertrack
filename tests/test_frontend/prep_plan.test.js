const test = require('node:test');
const assert = require('node:assert/strict');
const { renderPrepPlanResponse } = require('../../frontend/tracker/prep-plan.js');

const escapeHtml = value => String(value).replace(/[&<>"']/g, character => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[character]));

test('renders the actual prep-plan response where days is a count and plan is the day array', () => {
  const response = {
    role: 'Python developer',
    days: 2,
    source: 'rules',
    skills: [{ name: 'Python', importance: 'REQUIRED' }],
    plan: [
      {
        day: 1,
        title: 'Python fundamentals',
        skills: ['Python'],
        topics: ['data structures'],
        tasks: ['Review lists and dictionaries'],
        questions: [],
      },
      {
        day: 2,
        title: 'Mock interview & final revision',
        skills: ['Python'],
        topics: [],
        tasks: ['Complete a timed mock interview'],
        questions: [],
      },
    ],
  };

  const html = renderPrepPlanResponse(response, escapeHtml);
  assert.match(html, /Preparation plan · 2 days \(rules\)/);
  assert.match(html, /Day 1: Python fundamentals/);
  assert.match(html, /Review lists and dictionaries/);
  assert.match(html, /Day 2: Mock interview &amp; final revision/);
});

test('reports a malformed plan contract instead of treating a day count as an array', () => {
  assert.throws(
    () => renderPrepPlanResponse({ days: 2, plan: 2 }, escapeHtml),
    /plan array/,
  );
  assert.throws(
    () => renderPrepPlanResponse({ days: 2, plan: [{ day: 1, title: 'Only day', topics: [], tasks: [] }] }, escapeHtml),
    /inconsistent day count/,
  );
});
