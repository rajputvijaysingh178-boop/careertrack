let adminContentSkip = {questions: 0, materials: 0, blogs: 0};

async function renderAdminContentTools({companies = [], jobs = [], skills: initialSkills = []} = {}) {
  const grid = document.querySelector('.admin-grid');
  if (!grid || user?.role !== 'ADMIN' || currentView !== 'admin' || adminSection !== 'management') return;
  grid.insertAdjacentHTML('beforeend', '<section id="skill-tools" class="admin-wide admin-loading" role="status">Loading skills and categories…</section><section id="question-tools" class="admin-wide admin-loading" role="status">Loading interview questions…</section><section id="material-tools" class="admin-wide admin-loading" role="status">Loading study materials…</section><section id="blog-tools" class="admin-wide admin-loading" role="status">Loading blogs and guides…</section>');

  const query = skip => new URLSearchParams({skip: String(skip), limit: '50'});
  const results = await Promise.allSettled([
    api('/skills?limit=500'), api('/skills/categories'),
    api(`/interview-questions?${query(adminContentSkip.questions)}`),
    api(`/materials?${query(adminContentSkip.materials)}`),
    api(`/blogs?${query(adminContentSkip.blogs)}`),
  ]);
  if (user?.role !== 'ADMIN' || currentView !== 'admin' || adminSection !== 'management') return;

  const fail = (id, error, label) => {
    const panel = document.querySelector(`#${id}`);
    if (panel) panel.outerHTML = `<section id="${id}" class="panel prep-panel admin-wide error" role="alert">Could not load ${label}: ${esc(error.message)}</section>`;
  };
  const [skillResult, categoryResult, questionResult, materialResult, blogResult] = results;
  let allSkills = skillResult.status === 'fulfilled' ? skillResult.value : (initialSkills || []);
  let activeSkillCategory = '';
  const categories = categoryResult.status === 'fulfilled' ? categoryResult.value : [];

  const mountSkills = rows => {
    const panel = document.querySelector('#skill-tools');
    if (!panel) return;
    panel.innerHTML = renderSkillManager(rows, categories);
    document.querySelector('#admin-skill-filter').value = activeSkillCategory;
    document.querySelector('#admin-skill-form').onsubmit = async event => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(event.target));
      try {
        await api('/skills', {method: 'POST', body: JSON.stringify({name: values.name.trim(), category: values.category.trim() || null})});
        toast('Skill added'); showAdmin();
      } catch (error) { toast(error.message); }
    };
    document.querySelectorAll('[data-skill-edit]').forEach(form => form.onsubmit = async event => {
      event.preventDefault();
      if (!window.confirm('Save changes to this skill?')) return;
      const values = Object.fromEntries(new FormData(form));
      try {
        await api(`/skills/${form.dataset.skillEdit}`, {method: 'PUT', body: JSON.stringify({name: values.name.trim(), category: values.category.trim() || null})});
        toast('Skill updated'); showAdmin();
      } catch (error) { toast(error.message); }
    });
    document.querySelectorAll('[data-skill-delete]').forEach(button => button.onclick = async () => {
      if (!window.confirm('Delete this skill? Skills used by jobs cannot be deleted.')) return;
      try { await api(`/skills/${button.dataset.skillDelete}`, {method: 'DELETE'}); toast('Skill deleted'); showAdmin(); }
      catch (error) { toast(error.message); }
    });
    document.querySelector('#admin-skill-filter').onchange = event => { activeSkillCategory = event.target.value; mountSkills(allSkills.filter(skill => !activeSkillCategory || skill.category === activeSkillCategory)); };
  };
  if (skillResult.status === 'fulfilled') { allSkills = skillResult.value; mountSkills(allSkills); }
  else fail('skill-tools', skillResult.reason, 'skills');
  if (categoryResult.status === 'rejected') {
    toast(`Could not load skill categories: ${categoryResult.reason.message}`);
    document.querySelector('#skill-tools')?.insertAdjacentHTML('afterbegin', `<p class="error" role="alert">Category list unavailable: ${esc(categoryResult.reason.message)}. You can still type a category label.</p>`);
  }

  const pageControls = (kind, page) => `<div class="admin-pagination"><span>Showing ${Number(page.total) ? Number(page.skip || 0) + 1 : 0}–${Math.min(Number(page.skip || 0) + page.items.length, Number(page.total || 0))} of ${Number(page.total || 0)}</span><button class="small-button" data-content-prev="${kind}" ${Number(page.skip || 0) <= 0 ? 'disabled' : ''}>Previous</button><button class="small-button" data-content-next="${kind}" ${Number(page.skip || 0) + page.items.length >= Number(page.total || 0) ? 'disabled' : ''}>Next</button></div>`;
  const bindPageControls = (kind, page) => {
    document.querySelector(`[data-content-prev="${kind}"]`)?.addEventListener('click', () => { adminContentSkip[kind] = Math.max(0, adminContentSkip[kind] - 50); showAdmin(); });
    document.querySelector(`[data-content-next="${kind}"]`)?.addEventListener('click', () => { adminContentSkip[kind] += 50; showAdmin(); });
  };
  const questionValues = form => {
    const values = Object.fromEntries(new FormData(form));
    for (const key of ['company_id', 'job_id', 'skill_id']) values[key] = values[key] ? Number(values[key]) : null;
    for (const key of ['experience_level', 'round', 'answer']) if (values[key] === '') values[key] = null;
    values.expected_topics = (values.expected_topics || '').split(',').map(value => value.trim()).filter(Boolean);
    return values;
  };

  if (questionResult.status === 'fulfilled') {
    const page = questionResult.value, panel = document.querySelector('#question-tools');
    panel.innerHTML = renderQuestionManager(page.items || [], companies, jobs, allSkills) + pageControls('questions', page);
    document.querySelector('#admin-question-form').onsubmit = async event => {
      event.preventDefault();
      try { await api('/interview-questions', {method: 'POST', body: JSON.stringify(questionValues(event.target))}); toast('Question added'); showAdmin(); }
      catch (error) { toast(error.message); }
    };
    document.querySelectorAll('[data-question-edit]').forEach(form => form.onsubmit = async event => {
      event.preventDefault();
      if (!window.confirm('Save changes to this interview question?')) return;
      try { await api(`/interview-questions/${form.dataset.questionEdit}`, {method: 'PUT', body: JSON.stringify(questionValues(form))}); toast('Question updated'); showAdmin(); }
      catch (error) { toast(error.message); }
    });
    document.querySelectorAll('[data-question-delete]').forEach(button => button.onclick = async () => {
      if (!window.confirm('Delete this question from the shared bank?')) return;
      try { await api(`/interview-questions/${button.dataset.questionDelete}`, {method: 'DELETE'}); toast('Question deleted'); showAdmin(); }
      catch (error) { toast(error.message); }
    });
    bindPageControls('questions', page);
  } else fail('question-tools', questionResult.reason, 'interview questions');

  const materialValues = form => {
    const values = Object.fromEntries(new FormData(form));
    for (const key of ['skill_id', 'job_id', 'company_id']) values[key] = values[key] ? Number(values[key]) : null;
    for (const key of ['description', 'role', 'interview_round', 'file_url']) if (values[key] === '') values[key] = null;
    return values;
  };
  if (materialResult.status === 'fulfilled') {
    const page = materialResult.value, panel = document.querySelector('#material-tools');
    panel.innerHTML = renderMaterialManager(page.items || [], companies, jobs, allSkills) + pageControls('materials', page);
    document.querySelector('#admin-material-form').onsubmit = async event => {
      event.preventDefault();
      try { await api('/materials', {method: 'POST', body: JSON.stringify(materialValues(event.target))}); toast('Study material added'); showAdmin(); }
      catch (error) { toast(error.message); }
    };
    document.querySelector('#admin-material-upload').onsubmit = async event => {
      event.preventDefault();
      const form = event.target, body = new FormData(form), button = form.querySelector('button');
      for (const key of ['skill_id', 'job_id', 'company_id']) if (body.get(key)) body.set(key, String(Number(body.get(key)))); else body.delete(key);
      for (const key of ['description', 'role', 'interview_round']) if (!body.get(key)) body.delete(key);
      button.disabled = true;
      try {
        const headers = {}; if (token()) headers.Authorization = `Bearer ${token()}`;
        const response = await CareerTrackApi.apiFetch('/materials/upload', {method: 'POST', headers, body}, token());
        const result = await response.json().catch(() => ({detail: 'Unexpected server response'}));
        if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : result.detail?.message || `Request failed (${response.status})`);
        toast('Material uploaded'); showAdmin();
      } catch (error) { toast(error.message); }
      finally { button.disabled = false; }
    };
    document.querySelectorAll('[data-material-edit]').forEach(form => form.onsubmit = async event => {
      event.preventDefault();
      if (!window.confirm('Save changes to this study material?')) return;
      try { await api(`/materials/${form.dataset.materialEdit}`, {method: 'PUT', body: JSON.stringify(materialValues(form))}); toast('Material updated'); showAdmin(); }
      catch (error) { toast(error.message); }
    });
    document.querySelectorAll('[data-material-delete]').forEach(button => button.onclick = async () => {
      if (!window.confirm('Delete this study material? Uploaded files managed by CareerTrack will also be removed.')) return;
      try { await api(`/materials/${button.dataset.materialDelete}`, {method: 'DELETE'}); toast('Material deleted'); showAdmin(); }
      catch (error) { toast(error.message); }
    });
    bindPageControls('materials', page);
  } else fail('material-tools', materialResult.reason, 'study materials');

  if (blogResult.status === 'fulfilled') {
    const page = blogResult.value, panel = document.querySelector('#blog-tools');
    try {
      const blogs = await Promise.all((page.items || []).map(item => api(`/blogs/${encodeURIComponent(item.slug)}`)));
      if (user?.role !== 'ADMIN' || currentView !== 'admin' || adminSection !== 'management') return;
      panel.innerHTML = renderAdminBlogs(blogs) + pageControls('blogs', page); bindPageControls('blogs', page);
    } catch (error) { fail('blog-tools', error, 'blog content'); }
    document.querySelector('#admin-blog-form')?.addEventListener('submit', async event => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(event.target));
      const data = {title: values.title.trim(), content: values.content, category: values.category.trim() || null, tags: values.tags.split(',').map(tag => tag.trim()).filter(Boolean), status: values.status};
      try { await api('/blogs', {method: 'POST', body: JSON.stringify(data)}); toast('Content created'); showAdmin(); }
      catch (error) { toast(error.message); }
    });
    document.querySelectorAll('[data-blog-edit]').forEach(form => form.onsubmit = async event => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(form)), data = {title: values.title.trim(), content: values.content, category: values.category.trim() || null, tags: values.tags.split(',').map(tag => tag.trim()).filter(Boolean), status: values.status};
      if (!window.confirm('Save changes to this blog or preparation guide?')) return;
      try { await api(`/blogs/${form.dataset.blogEdit}`, {method: 'PUT', body: JSON.stringify(data)}); toast('Content updated'); showAdmin(); }
      catch (error) { toast(error.message); }
    });
    document.querySelectorAll('[data-blog-delete]').forEach(button => button.onclick = async () => {
      if (!window.confirm('Delete this blog or preparation guide? This cannot be undone.')) return;
      try { await api(`/blogs/${button.dataset.blogDelete}`, {method: 'DELETE'}); toast('Content deleted'); showAdmin(); }
      catch (error) { toast(error.message); }
    });
  } else fail('blog-tools', blogResult.reason, 'blogs and preparation guides');
}
