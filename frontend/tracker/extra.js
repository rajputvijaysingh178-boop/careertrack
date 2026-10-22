// OWNER: M3 + M1 frontend integration for existing CareerTrack APIs.
const renderTracker = render;
const formatMatch = p => `${Math.round(p || 0)}%`;
const safeHttpUrl = value => { try { const url=new URL(value,window.location.origin); return ['http:','https:'].includes(url.protocol)?url.href:null; } catch { return null; } };
let jobsCache = [], chosenJob = null, chosenApplication = null;

render = function () {
  if (!['jobs','saved','prep','jd','match','recommendations','admin'].includes(currentView)) { $('#summary').classList.remove('hidden'); return renderTracker(); }
  const names={jobs:'Job board',saved:'Saved jobs',prep:'Interview preparation',jd:'Job description analyzer',match:'Resume match',recommendations:'Recommended for you',admin:'Administration'};
  $('#page-title').textContent=names[currentView];
  $('#page-subtitle').textContent={jobs:'Search active roles and save the ones you want to track.',prep:'Practice questions, learning resources, skill gaps, and a focused plan.',jd:'Turn a job description into a structured view of its requirements.',match:'Compare a resume with a role and see matched and missing skills.',recommendations:'Roles selected from your skill profile.'}[currentView];
  document.querySelectorAll('.nav').forEach(b=>b.classList.toggle('active',b.dataset.view===currentView));
  $('#summary').classList.add('hidden');
  if(currentView==='jobs') showJobs();
  if(currentView==='saved') showSaved();
  if(currentView==='prep') showPrep();
  if(currentView==='jd') showJD();
  if(currentView==='match') showMatch();
  if(currentView==='recommendations') showRecommendations();
  if(currentView==='admin') showAdmin();
};

async function showJobs(filters={}) {
  try {
    const params=new URLSearchParams();
    for(const [key,value] of Object.entries(filters))if(value)params.set(key,value);
    params.set('limit','50');
    const [data,bookmarks,companies]=await Promise.all([api(`/jobs?${params}`),api('/bookmarks'),api('/companies?limit=100')]);
    const ignored=new Set(bookmarks.filter(b=>b.type==='IGNORE').map(b=>b.job_id));
    jobsCache=(data.items||[]).filter(j=>!ignored.has(j.id));
    $('#content').innerHTML=`<form id="job-search" class="job-filters"><label>Keywords<input name="q" value="${esc(filters.q||'')}" placeholder="Role, company, or skill"></label><label>Location<input name="location" value="${esc(filters.location||'')}" placeholder="City or remote"></label><label>Company<select name="company_id"><option value="">Any company</option>${(companies.items||[]).map(c=>`<option value="${c.id}" ${String(filters.company_id||'')===String(c.id)?'selected':''}>${esc(c.name)}</option>`).join('')}</select></label><label>Work mode<select name="work_mode"><option value="">Any</option><option ${filters.work_mode==='REMOTE'?'selected':''}>REMOTE</option><option ${filters.work_mode==='HYBRID'?'selected':''}>HYBRID</option><option ${filters.work_mode==='ONSITE'?'selected':''}>ONSITE</option></select></label><label>Employment<select name="employment_type"><option value="">Any</option>${['FULL_TIME','PART_TIME','CONTRACT','INTERNSHIP','FREELANCE'].map(x=>`<option ${filters.employment_type===x?'selected':''}>${x}</option>`).join('')}</select></label><label>Experience (years)<input name="experience" type="number" min="0" max="60" value="${esc(filters.experience||'')}"></label><label>Minimum salary (LPA)<input name="salary_min" type="number" min="0" step="0.1" value="${esc(filters.salary_min||'')}"></label><label>Maximum salary (LPA)<input name="salary_max" type="number" min="0" step="0.1" value="${esc(filters.salary_max||'')}"></label><label>Role type<input name="job_type" value="${esc(filters.job_type||'')}" placeholder="Backend, QA…"></label><label>Skills<input name="skills" value="${esc(filters.skills||'')}" placeholder="Python, SQL"></label><label>Skill matching<select name="skills_match"><option value="any" ${filters.skills_match==='all'?'':'selected'}>Any selected skill</option><option value="all" ${filters.skills_match==='all'?'selected':''}>All selected skills</option></select></label><label>Posted within<select name="posted_within_days"><option value="">Any time</option>${[['7','7 days'],['30','30 days'],['90','90 days']].map(([v,l])=>`<option value="${v}" ${filters.posted_within_days===v?'selected':''}>${l}</option>`).join('')}</select></label><label>Sort<select name="sort"><option value="newest" ${filters.sort==='salary'||filters.sort==='expiring'?'':'selected'}>Newest</option><option value="salary" ${filters.sort==='salary'?'selected':''}>Salary</option><option value="expiring" ${filters.sort==='expiring'?'selected':''}>Expiring soon</option></select></label><button class="primary">Search roles</button><button type="reset" class="small-button">Clear filters</button></form><div id="job-detail"></div><div class="job-grid">${jobsCache.map(j=>`<article class="job-tile"><div class="eyebrow">${esc(j.company?.name||'CAREERTRACK JOB')}</div><h3>${esc(j.title)}</h3><p>${esc(j.location||'Location flexible')} · ${esc(j.work_mode||'Work mode not specified')}</p><div class="skill-tags">${(j.skills||[]).slice(0,5).map(s=>`<span>${esc(s.name)}</span>`).join('')}</div><div class="tile-foot"><span>${j.salary_min||j.salary_max?`${esc(j.salary_min||'—')}–${esc(j.salary_max||'—')} LPA`:'Salary not listed'}</span><span>${j.experience_min??'—'}${j.experience_max?`–${j.experience_max}`:'+'} yrs</span></div><div class="actions"><button class="small-button" data-job-view="${j.id}">View details</button><button class="small-button" data-job-detail="${j.id}">Prepare</button><button class="small-button" data-job-save="${j.id}">Save</button><button class="small-button" data-job-ignore="${j.id}">Ignore</button><button class="small-button" data-job-apply="${j.id}">Track application</button></div></article>`).join('')||'<div class="panel empty">No matching active roles. Try a broader search.</div>'}</div>`;
    $('#job-search').onsubmit=e=>{e.preventDefault();const values=Object.fromEntries(new FormData(e.target));showJobs(Object.fromEntries(Object.entries(values).filter(([,v])=>v)))};
    $('#job-search').onreset=()=>setTimeout(()=>showJobs(),0);
    document.querySelectorAll('[data-job-view]').forEach(b=>b.onclick=()=>showJobDetails(Number(b.dataset.jobView)));
    document.querySelectorAll('[data-job-detail]').forEach(b=>b.onclick=()=>{chosenJob=Number(b.dataset.jobDetail);currentView='prep';render()});
    document.querySelectorAll('[data-job-save]').forEach(b=>b.onclick=async()=>{try{await api('/bookmarks',{method:'POST',body:JSON.stringify({job_id:Number(b.dataset.jobSave),type:'SAVE'})});toast('Role saved')}catch(e){toast(e.message)}});
    document.querySelectorAll('[data-job-ignore]').forEach(b=>b.onclick=async()=>{try{await api('/bookmarks',{method:'POST',body:JSON.stringify({job_id:Number(b.dataset.jobIgnore),type:'IGNORE'})});showJobs(filters);toast('Role ignored')}catch(e){toast(e.message)}});
    document.querySelectorAll('[data-job-apply]').forEach(b=>b.onclick=async()=>{try{await api('/applications',{method:'POST',body:JSON.stringify({job_id:Number(b.dataset.jobApply),status:'APPLIED',source:'CareerTrack job board'})});await load();toast('Application added to your tracker')}catch(e){toast(e.message)}});
  } catch(e){$('#content').innerHTML=`<div class="panel empty">${esc(e.message)}</div>`}
}

async function showJobDetails(id){
  const panel=$('#job-detail');
  if(!panel)return;
  panel.innerHTML='<section class="panel prep-panel">Loading job details…</section>';
  try{
    const job=await api(`/jobs/${id}`);
    const applicationUrl=safeHttpUrl(job.application_url);
    panel.innerHTML=`<section class="panel prep-panel job-detail"><button class="small-button" id="close-job-details">Close</button><div class="eyebrow">${esc(job.company?.name||'Company')}</div><h2>${esc(job.title)}</h2><p>${esc(job.location||'Location flexible')} · ${esc(job.work_mode||'Work mode not specified')} · ${esc(job.employment_type||'Employment type not specified')}</p><p>Experience: ${job.experience_min??'Not specified'}${job.experience_max?`–${job.experience_max} years`:''} · Salary: ${job.salary_min||job.salary_max?`${esc(job.salary_min||'—')}–${esc(job.salary_max||'—')} LPA`:'Not listed'}</p><div class="skill-tags">${(job.skills||[]).map(s=>`<span>${esc(s.name)} · ${esc(s.importance)}</span>`).join('')}</div><h3>Full job description</h3><div class="job-description">${esc(job.description||'No description provided.')}</div><div class="actions">${applicationUrl?`<a class="small-button" href="${esc(applicationUrl)}" target="_blank" rel="noopener">Open application site</a>`:''}<button class="small-button" id="job-detail-save">Save job</button><button class="small-button" id="job-detail-apply">Track application</button></div></section>`;
    $('#close-job-details').onclick=()=>panel.replaceChildren();
    $('#job-detail-save').onclick=async()=>{try{await api('/bookmarks',{method:'POST',body:JSON.stringify({job_id:id,type:'SAVE'})});toast('Role saved')}catch(e){toast(e.message)}};
    $('#job-detail-apply').onclick=async()=>{try{await api('/applications',{method:'POST',body:JSON.stringify({job_id:id,status:'APPLIED',source:'CareerTrack job board'})});await load();toast('Application added to your tracker')}catch(e){toast(e.message)}};
  }catch(e){panel.innerHTML=`<section class="panel prep-panel error">${esc(e.message)}</section>`}
}

async function showSaved(){try{const rows=(await api('/bookmarks')).filter(b=>b.type==='SAVE');const entries=await Promise.all(rows.map(async b=>{try{return {bookmark:b,job:await api(`/jobs/${b.job_id}`)}}catch{return {bookmark:b,job:null}}}));$('#content').innerHTML=`<div class="job-grid">${entries.map(({bookmark:b,job})=>job?`<article class="job-tile"><div class="eyebrow">SAVED ROLE</div><h3>${esc(job.title)}</h3><p>${esc(job.company?.name||'Company')} · ${esc(job.location||'Flexible location')}</p><div class="skill-tags">${(job.skills||[]).slice(0,5).map(s=>`<span>${esc(s.name)}</span>`).join('')}</div><div class="actions"><button class="small-button" data-saved-apply="${job.id}">Track as applied</button><button class="small-button" data-saved-remove="${b.id}">Remove</button></div></article>`:'').join('')||'<div class="panel empty">No saved jobs yet. Browse the job board and save a role to keep it here.</div>'}</div>`;document.querySelectorAll('[data-saved-remove]').forEach(b=>b.onclick=async()=>{try{await api(`/bookmarks/${b.dataset.savedRemove}`,{method:'DELETE'});showSaved()}catch(e){toast(e.message)}});document.querySelectorAll('[data-saved-apply]').forEach(b=>b.onclick=async()=>{try{await api('/applications',{method:'POST',body:JSON.stringify({job_id:Number(b.dataset.savedApply),status:'APPLIED',source:'Saved job'})});await load();currentView='board';render();toast('Application added to your tracker')}catch(e){toast(e.message)}})}catch(e){$('#content').innerHTML=`<div class="panel empty">${esc(e.message)}</div>`}}

async function showPrep(jobId=chosenJob, applicationId=chosenApplication) {
  const [jobResult, applicationResult] = await Promise.allSettled([
    api('/jobs?limit=50'), api('/applications?limit=200')
  ]);
  if (jobResult.status === 'fulfilled') jobsCache = jobResult.value.items || [];
  else toast(jobResult.reason.message);
  const applicationPayload = applicationResult.status === 'fulfilled' ? applicationResult.value : [];
  if (applicationResult.status === 'rejected') toast(applicationResult.reason.message);

  const selected = applicationId ? `application:${applicationId}` : jobId ? `job:${jobId}` : '';
  const jobOptions = jobsCache.map(j => `<option value="job:${j.id}" ${selected===`job:${j.id}`?'selected':''}>${esc(j.title)} ? ${esc(j.company?.name||'')}</option>`).join('');
  const applicationOptions = renderPrepApplicationOptions(applicationPayload, selected, esc);
  if (applicationOptions === null) toast('Applications could not be loaded because the server returned an unexpected response.');
  $('#content').innerHTML=`<div class="prep-toolbar"><label>Choose a role<select id="prep-job"><option value="">Select a role</option>${jobOptions?`<optgroup label="Job board">${jobOptions}</optgroup>`:''}${applicationOptions?`<optgroup label="My applications">${applicationOptions}</optgroup>`:''}</select></label><button id="load-prep" class="primary">Open preparation workspace</button><button id="prep-recommendations" class="small-button">My job recommendations</button></div><form id="custom-prep-form" class="panel prep-panel"><h3>Prepare for another role</h3><label>Role title<input name="role_title" required maxlength="200" placeholder="Python backend engineer"></label><label>Job description (optional)<textarea name="jd_text" rows="4" placeholder="Paste the role description to get skill-specific guidance"></textarea></label><button class="small-button">Open custom workspace</button></form><div id="prep-results" class="prep-results"><div class="panel empty">Choose a job or application, or enter a role above.</div></div>`;
  $('#load-prep').onclick=()=>{
    const [kind, rawId] = ($('#prep-job').value || ':').split(':');
    const id = Number(rawId) || null;
    if(kind==='application' && id){chosenApplication=id;chosenJob=null;loadPrepWorkspace(null,id)}
    else if(kind==='job' && id){chosenJob=id;chosenApplication=null;loadPrepWorkspace(id)}
  };
  $('#prep-job').onchange=()=>{chosenJob=null;chosenApplication=null};
  $('#custom-prep-form').onsubmit=e=>{
    e.preventDefault();
    const value=Object.fromEntries(new FormData(e.target));
    chosenJob=null;chosenApplication=null;
    loadPrepWorkspace(null,null,{role_title:value.role_title.trim(),jd_text:value.jd_text.trim()||null});
  };
  $('#prep-recommendations').onclick=()=>{currentView='recommendations';render()};
  if(applicationId){loadPrepWorkspace(null,applicationId)}else if(jobId){loadPrepWorkspace(jobId)}
}

async function loadPrepWorkspace(jobId, applicationId=null, customTarget=null){
  if(!jobId&&!applicationId&&!customTarget)return;
  const root=$('#prep-results');
  root.innerHTML='<div class="panel empty">Loading preparation material?</div>';
  try{
    let w,g;
    if(customTarget){
      const result=await api('/prep/workspace',{method:'POST',body:JSON.stringify(customTarget)});
      w=result.workspace;g=result.skill_gap;
    }else{
      const target=applicationId?`applications/${applicationId}`:`jobs/${jobId}`;
      [w,g]=await Promise.all([api(`/prep/${target}`),api(`/prep/${target}/skill-gap`)]);
    }
    const blogs = await Promise.all((w.blogs||[]).map(async blog=>{try{return await api(`/blogs/${encodeURIComponent(blog.slug)}`)}catch{return blog}}));
    w.blogs=blogs;
    root.innerHTML=`<div class="prep-columns"><section class="panel prep-panel"><div class="eyebrow">${esc(w.job?.company||'ROLE')}</div><h2>${esc(w.job?.title||'Preparation workspace')}</h2><h3>Skill gap ? ${formatMatch(g.match_percent)} match</h3><div class="skill-tags">${(g.missing||[]).map(s=>`<span class="missing">Learn ? ${esc(s.name)}</span>`).join('')||'<span>All listed skills match your profile.</span>'}</div><h3>Skills to practice</h3>${(g.study_next||[]).slice(0,8).map(s=>`<div class="detail-item"><strong>${esc(s.skill)}</strong><small>${(s.topics||[]).map(esc).join(' ? ')}</small></div>`).join('')}</section><section class="panel prep-panel"><h3>Interview questions</h3>${Object.entries(w.questions?.by_category||{}).map(([cat,qs])=>`<details><summary>${esc(cat)} ? ${qs.length}</summary>${qs.slice(0,10).map(q=>`<div class="detail-item">${esc(q.question)}<small>${esc(q.difficulty||'')} ? ${esc(q.round||'')}</small></div>`).join('')}</details>`).join('')||'No questions have been added for this role.'}<h3>Preparation plan</h3><form id="plan-form"><label>Days<select name="days"><option>7</option><option>3</option><option>14</option><option>21</option><option>30</option></select></label><button class="small-button">Build my plan</button></form><div id="plan-result"></div></section><section class="panel prep-panel"><h3>Learning resources</h3>${(w.materials||[]).map(m=>`<div class="detail-item"><button class="small-button" type="button" data-material-open="${Number(m.id)}">${esc(m.title||m.name||'Study material')}</button><small>${esc(m.type||'Resource')}</small></div>`).join('')||'No linked materials yet'}${(w.blogs||[]).map(b=>`<details><summary>${esc(b.title||'Related article')}</summary><div class="detail-item">${esc(b.content||'Article content is unavailable.')}</div></details>`).join('')||'No related articles yet'}</section></div>`;
    $('#plan-form').onsubmit=async e=>{
      e.preventDefault();
      try{
        const days=Number(new FormData(e.target).get('days'));
        const target=customTarget?{jd_text:customTarget.jd_text||customTarget.role_title}:{job_id:jobId,application_id:applicationId};
        console.log("PREP REQUEST:", JSON.stringify({...target, days, use_ai: true}));
const plan = await api('/prep/plan', {
  method: 'POST',
  body: JSON.stringify({...target, days, use_ai: true})
});
        $('#plan-result').innerHTML=renderPrepPlanResponse(plan,esc);
      }catch(err){$('#plan-result').innerHTML=`<div class="error">${esc(err.message)}</div>`}
    };
  }catch(e){root.innerHTML=`<div class="panel empty">${esc(e.message)}</div>`}
}

function showJD(){ $('#content').innerHTML=`<div class="tool-layout"><form id="jd-form" class="panel tool-card"><label>Paste a job description<textarea name="jd_text" required minlength="20" rows="15" placeholder="Paste the full job description here…"></textarea></label><label class="inline-check"><input type="checkbox" name="use_ai"> Use optional AI enrichment</label><button class="primary">Analyze job description</button></form><section id="jd-result" class="panel tool-card empty">Your analysis will appear here.</section></div>`;$('#jd-form').onsubmit=async e=>{e.preventDefault();const fd=new FormData(e.target);const out=$('#jd-result');out.classList.remove('empty');out.textContent='Analyzing…';try{const result=await api('/jd-analyzer/analyze',{method:'POST',body:JSON.stringify({jd_text:fd.get('jd_text'),use_ai:fd.has('use_ai')})});out.innerHTML=`<div class="eyebrow">${esc(result.source||'RULE-BASED')}</div><h2>Role requirements</h2><div class="skill-tags">${(result.skills||[]).map(s=>`<span>${esc(s.name)} · ${esc(s.importance)}</span>`).join('')}</div><h3>Experience</h3><p>${esc(result.experience?.text||'Not specified')}</p><h3>Responsibilities</h3><ul>${(result.responsibilities||[]).map(x=>`<li>${esc(x)}</li>`).join('')}</ul><h3>Tools</h3><div class="skill-tags">${(result.tools||[]).map(esc).join('')}</div><h3>Interview topics</h3>${(result.interview_topics||[]).map(t=>`<div class="detail-item"><strong>${esc(t.skill)}</strong><small>${(t.topics||[]).map(esc).join(' · ')}</small></div>`).join('')}${result.ai_error?`<small>${esc(result.ai_error)}</small>`:''}`}catch(err){out.innerHTML=`<div class="error">${esc(err.message)}</div>`}}}

async function showMatch(){
  if(!jobsCache.length){
    try{const data=await api('/jobs?limit=50');jobsCache=data.items||[]}
    catch(e){toast(e.message)}
  }
  $('#content').innerHTML=`<div class="tool-layout"><form id="match-form" class="panel tool-card"><label>Target role<select name="job_id"><option value="">Choose from job board…</option>${jobsCache.map(j=>`<option value="${j.id}" ${j.id===chosenJob?'selected':''}>${esc(j.title)} · ${esc(j.company?.name||'')}</option>`).join('')}</select></label><label>Or paste a job description<textarea name="jd_text" rows="4" placeholder="Optional when a job is selected"></textarea></label><label>Upload resume (PDF, DOCX, TXT)<input type="file" name="file" accept=".pdf,.docx,.txt"></label><label>Or paste resume text<textarea name="resume_text" rows="8" placeholder="Paste your resume text"></textarea></label><button class="primary">Match resume</button></form><section id="match-result" class="panel tool-card empty">Matched skills and improvement areas will appear here.</section></div>`;
  $('#match-form').onsubmit=async e=>{e.preventDefault();const form=new FormData(e.target),fd=new FormData();for(const key of ['job_id','jd_text','resume_text'])if(form.get(key))fd.append(key,form.get(key));if(form.get('file')?.size)fd.append('file',form.get('file'));const out=$('#match-result');out.classList.remove('empty');out.textContent='Comparing…';try{const response=await CareerTrackApi.apiFetch('/resume-match',{method:'POST',body:fd},token());const result=await response.json();if(!response.ok)throw Error(result.detail||'Could not match this resume');out.innerHTML=`<div class="eyebrow">RESUME MATCH</div><h2>${formatMatch(result.match_percent)} · ${esc(result.label||'')}</h2><div class="bar"><i style="width:${Math.min(result.match_percent||0,100)}%"></i></div><h3>Matched skills</h3><div class="skill-tags">${(result.matched||[]).map(s=>`<span>${esc(s.name)}</span>`).join('')||'None identified'}</div><h3>Skills to strengthen</h3><div class="skill-tags">${(result.missing||[]).map(s=>`<span class="missing">${esc(s.name)}</span>`).join('')||'No gaps identified'}</div><h3>Suggestions</h3><ul>${(result.recommendations||[]).map(t=>`<li>${esc(t)}</li>`).join('')}</ul>`}catch(err){out.innerHTML=`<div class="error">${esc(err.message)}</div>`}}
}

async function showRecommendations(){try{const [data,skills]=await Promise.all([api('/recommendations/jobs?limit=20'),api('/recommendations/my-skills')]);$('#content').innerHTML=`<div class="panel prep-panel"><div class="eyebrow">YOUR SKILL PROFILE</div><div class="skill-tags">${(skills.skills||[]).map(s=>`<span>${esc(s)}</span>`).join('')||'<span>Add skills from your profile first.</span>'}</div><label class="skill-editor">Edit skills · separate names with commas<input id="skill-input" value="${esc((skills.skills||[]).join(', '))}"></label><button id="save-skills" class="small-button">Save skill profile</button></div><h2 class="section-title">Suggested roles</h2><div class="job-grid">${(data.jobs||[]).map(j=>`<article class="job-tile"><div class="eyebrow">${formatMatch(j.match_percent)} SKILL MATCH</div><h3>${esc(j.title)}</h3><p>${esc(j.company||'Company')}</p><div class="skill-tags">${(j.matched||[]).map(s=>`<span>${esc(s)}</span>`).join('')}</div><button class="small-button" data-recommended="${j.job_id}">Prepare for this role</button></article>`).join('')||`<div class="panel empty">${esc(data.note||'No recommendations available yet.')}</div>`}</div>`;$('#save-skills').onclick=async()=>{try{const value=$('#skill-input').value.split(',').map(s=>s.trim()).filter(Boolean);const result=await api('/recommendations/my-skills',{method:'PUT',body:JSON.stringify({skills:value})});await showRecommendations();if(result.unknown?.length){toast(`Not in skill catalog: ${result.unknown.join(', ')}`);const input=$('#skill-input');if(input)input.value=value.join(', ');const label=$('.skill-editor');if(label){const warning=document.createElement('p');warning.className='error';warning.textContent=`Not in the skill catalog: ${result.unknown.join(', ')}. Add these skills in Admin → Skills, then save again.`;label.insertAdjacentElement('afterend',warning)}}else{toast('Skill profile saved')}}catch(e){toast(e.message)}};document.querySelectorAll('[data-recommended]').forEach(b=>b.onclick=()=>{chosenJob=Number(b.dataset.recommended);currentView='prep';render()})}catch(e){$('#content').innerHTML=`<div class="panel empty">${esc(e.message)}</div>`}}

let adminSection='overview', adminUserSkip=0;
async function showAdmin(){
  if(user?.role!=='ADMIN'){toast('Admin access required');currentView='board';return render()}
  $('#summary').classList.add('hidden');
  $('#content').innerHTML='<div class="panel admin-loading" role="status">Loading administration…</div>';
  try{
    const [stats,companies,skills,jobs]=await Promise.all([api('/admin/dashboard'),api('/companies?limit=100'),api('/skills?limit=500'),api('/jobs?limit=100')]);
    if(user?.role!=='ADMIN'||currentView!=='admin')return;
    $('#content').innerHTML=`<nav class="admin-tabs" aria-label="Administration sections"><button class="small-button" data-admin-section="overview" aria-current="${adminSection==='overview'?'page':'false'}">Dashboard</button><button class="small-button" data-admin-section="users" aria-current="${adminSection==='users'?'page':'false'}">Users</button><button class="small-button" data-admin-section="reports" aria-current="${adminSection==='reports'?'page':'false'}">Reports</button><button class="small-button" data-admin-section="management" aria-current="${adminSection==='management'?'page':'false'}">Management</button></nav><div id="admin-panel"></div>`;
    document.querySelectorAll('[data-admin-section]').forEach(button=>button.onclick=()=>{adminSection=button.dataset.adminSection;showAdmin()});
    const panel=$('#admin-panel');
    if(adminSection==='overview')panel.innerHTML=renderAdminDashboard(stats,esc);
    if(adminSection==='users')await renderAdminUsersPage();
    if(adminSection==='reports')await renderAdminReportsPage();
    if(adminSection==='management'){
      const co=companies.items||[], js=jobs.items||[];
      panel.innerHTML='<div class="admin-loading" role="status">Loading company and job details…</div>';
      const detailedJobs=await Promise.all(js.map(job=>api(`/jobs/${job.id}`)));
      if(user?.role!=='ADMIN'||currentView!=='admin'||adminSection!=='management')return;
      panel.innerHTML=`<div class="admin-grid"><section class="panel prep-panel"><h3>Create company</h3><form id="company-create"><label>Name<input name="name" required></label><label>Website<input name="website" type="url"></label><label>Industry<input name="industry"></label><label>Location<input name="location"></label><button class="primary">Add company</button></form></section><section class="panel prep-panel"><h3>Add skill</h3><form id="skill-create"><label>Skill name<input name="name" required></label><label>Category<input name="category"></label><button class="primary">Add skill</button></form></section><section class="panel prep-panel"><h3>Create a job</h3><form id="job-create"><label>Company<select name="company_id" required><option value="">Choose company</option>${co.filter(c=>c.status==='ACTIVE').map(c=>`<option value="${c.id}">${esc(c.name)}</option>`).join('')}</select></label><label>Role title<input name="title" required minlength="3"></label><label>Description<textarea name="description" required minlength="20" rows="5"></textarea></label><div class="form-row"><label>Location<input name="location"></label><label>Work mode<select name="work_mode"><option value="">Not specified</option><option>REMOTE</option><option>HYBRID</option><option>ONSITE</option></select></label></div><div class="form-row"><label>Salary min (LPA)<input name="salary_min" type="number" min="0"></label><label>Salary max (LPA)<input name="salary_max" type="number" min="0"></label></div><label>Skills · comma separated<input name="skills" placeholder="Python, FastAPI"></label><div id="job-duplicate-warning" role="alert"></div><button class="primary">Create draft</button></form></section><section class="panel prep-panel admin-wide"><h3>Companies</h3>${renderAdminCompanies(co,esc)}</section><section class="panel prep-panel admin-wide"><h3>Job listings</h3><button class="small-button" id="run-job-maintenance">Run expiry maintenance</button><p class="muted">Activates scheduled jobs and expires overdue listings.</p>${renderAdminJobs(detailedJobs,co,esc)}</section></div>`;
      $('#company-create').onsubmit=async e=>{e.preventDefault();const v=Object.fromEntries(new FormData(e.target));for(const k of Object.keys(v))if(!v[k])delete v[k];try{await api('/companies',{method:'POST',body:JSON.stringify(v)});toast('Company created');showAdmin()}catch(err){toast(err.message)}};
      $('#skill-create').onsubmit=async e=>{e.preventDefault();const v=Object.fromEntries(new FormData(e.target));if(!v.category)delete v.category;try{await api('/skills',{method:'POST',body:JSON.stringify(v)});toast('Skill added');showAdmin()}catch(err){toast(err.message)}};
      $('#job-create').onsubmit=async e=>{e.preventDefault();const form=e.target,v=Object.fromEntries(new FormData(form)),warning=$('#job-duplicate-warning');warning.innerHTML='';const names=(v.skills||'').split(',').map(s=>s.trim()).filter(Boolean);delete v.skills;for(const k of ['salary_min','salary_max'])if(v[k])v[k]=Number(v[k]);else delete v[k];for(const k of Object.keys(v))if(!v[k])delete v[k];v.company_id=Number(v.company_id);v.skills=names.map(name=>({name,importance:'REQUIRED'}));try{const duplicate=await api('/jobs/check-duplicate',{method:'POST',body:JSON.stringify({company_id:v.company_id,title:v.title,description:v.description})});if(duplicate.duplicate){warning.innerHTML=`<strong>Similar jobs found:</strong> ${duplicate.similar_jobs.map(j=>`${esc(j.title)} (${esc(j.status)}, score ${Math.round(j.score*100)}%)`).join('; ')}`;if(!window.confirm(`Similar job(s) exist: ${duplicate.similar_jobs.map(j=>j.title).join(', ')}. Create this job anyway?`))return;await api('/jobs?force=true',{method:'POST',body:JSON.stringify(v)})}else await api('/jobs',{method:'POST',body:JSON.stringify(v)});toast('Job draft created');showAdmin()}catch(err){warning.textContent=err.message;toast(err.message)}};
      document.querySelectorAll('[data-company-edit]').forEach(form=>form.onsubmit=async e=>{e.preventDefault();const id=form.dataset.companyEdit,data=Object.fromEntries(new FormData(form));if(!window.confirm('Save these company changes?'))return;try{await api(`/companies/${id}`,{method:'PUT',body:JSON.stringify(data)});toast('Company updated');showAdmin()}catch(err){toast(err.message)}});
      document.querySelectorAll('[data-delete-company]').forEach(button=>button.onclick=async()=>{if(!window.confirm('Delete this company? This cannot be undone.'))return;try{await api(`/companies/${button.dataset.deleteCompany}`,{method:'DELETE'});toast('Company deleted');showAdmin()}catch(err){toast(err.message)}});
      document.querySelectorAll('[data-job-edit]').forEach(form=>form.onsubmit=async e=>{e.preventDefault();const id=Number(form.dataset.jobEdit),formValues=Object.fromEntries(new FormData(form)),fields={...formValues},original=detailedJobs.find(job=>job.id===id);if(!original)return;const description=fields.description,title=fields.title,companyId=Number(fields.company_id);delete fields.skills;if(companyId===Number(original.company?.id))delete fields.company_id;for(const key of ['salary_min','salary_max','experience_min','experience_max'])if(fields[key]==='')delete fields[key];else if(fields[key]!==undefined)fields[key]=Number(fields[key]);for(const key of ['posted_date','expiry_date','application_url','location','work_mode','employment_type'])if(fields[key]==='')fields[key]=null;const oldImportance=new Map((original.skills||[]).map(skill=>[skill.name.toLowerCase(),skill.importance]));fields.skills=formValues.skills.split(',').map(name=>name.trim()).filter(Boolean).map(name=>({name,importance:oldImportance.get(name.toLowerCase())||'REQUIRED'}));try{const duplicate=await api('/jobs/check-duplicate',{method:'POST',body:JSON.stringify({company_id:companyId,title,description,exclude_job_id:id})});if(duplicate.duplicate&&!window.confirm(`Similar job(s) exist: ${duplicate.similar_jobs.map(j=>j.title).join(', ')}. Save these changes anyway?`))return;if(!window.confirm('Save changes to this job?'))return;await api(`/jobs/${id}`,{method:'PUT',body:JSON.stringify(fields)});toast('Job updated');showAdmin()}catch(err){toast(err.message)}});
      document.querySelectorAll('[data-delete-job]').forEach(button=>button.onclick=async()=>{if(!window.confirm('Delete this job? Jobs with applications cannot be deleted and should be closed instead.'))return;try{await api(`/jobs/${button.dataset.deleteJob}`,{method:'DELETE'});toast('Job deleted');showAdmin()}catch(err){toast(err.message)}});
      document.querySelectorAll('[data-job-action]').forEach(button=>button.onclick=async()=>{const action=button.dataset.jobAction,id=Number(button.dataset.jobId);if(action==='publish'){const job=detailedJobs.find(item=>item.id===id);try{const duplicate=await api('/jobs/check-duplicate',{method:'POST',body:JSON.stringify({company_id:job.company.id,title:job.title,description:job.description,exclude_job_id:id})});if(duplicate.duplicate&&!window.confirm(`Similar job(s) exist: ${duplicate.similar_jobs.map(j=>j.title).join(', ')}. Publish anyway?`))return;await api(`/jobs/${id}/publish${duplicate.duplicate?'?force=true':''}`,{method:'POST'});toast('Job published');showAdmin()}catch(err){toast(err.message)}return}const confirmText={close:'Close this job?',expire:'Mark this job expired?',unpublish:'Return this job to draft?'}[action];if(!window.confirm(confirmText||'Continue with this status change?'))return;try{await api(`/jobs/${id}/${action}`,{method:'POST'});toast(({close:'Job closed',expire:'Job expired',unpublish:'Job returned to draft'})[action]||'Job status updated');showAdmin()}catch(err){toast(err.message)}});
      document.querySelectorAll('[data-job-reopen]').forEach(form=>form.onsubmit=async e=>{e.preventDefault();const id=Number(form.dataset.jobReopen),expiry_date=new FormData(form).get('expiry_date')||null;if(!window.confirm('Reopen this expired job?'))return;try{await api(`/jobs/${id}/reopen`,{method:'POST',body:JSON.stringify({expiry_date})});toast('Job reopened');showAdmin()}catch(err){toast(err.message)}});
      $('#run-job-maintenance').onclick=async()=>{if(!window.confirm('Run expiry maintenance for all jobs now? Scheduled jobs may activate and overdue jobs may expire.'))return;try{const result=await api('/admin/jobs/run-maintenance',{method:'POST'});toast(`Maintenance complete: ${result.activated} activated, ${result.expired} expired`);showAdmin()}catch(err){toast(err.message)}};
      renderAdminContentTools({companies:co,jobs:detailedJobs,skills});
    }
  }catch(e){if(currentView==='admin')$('#content').innerHTML=`<div class="panel empty error" role="alert">Could not load administration: ${esc(e.message)}</div>`}
}

async function renderAdminUsersPage(filters={}){
  const panel=$('#admin-panel');if(!panel)return;
  panel.innerHTML='<section class="panel admin-loading" role="status">Loading users…</section>';
  try{
    const params=new URLSearchParams({skip:String(adminUserSkip),limit:'20'});for(const [key,value] of Object.entries(filters))if(value)params.set(key,value);
    const payload=await api(`/admin/users?${params}`);if(user?.role!=='ADMIN'||currentView!=='admin'||adminSection!=='users')return;
    panel.innerHTML=`<section class="panel prep-panel admin-wide"><h2>User accounts</h2><form id="admin-user-filters" class="admin-filters"><label>Search<input name="q" value="${esc(filters.q||'')}" placeholder="Name or email"></label><label>Role<select name="role"><option value="">Any role</option><option ${filters.role==='USER'?'selected':''}>USER</option><option ${filters.role==='ADMIN'?'selected':''}>ADMIN</option></select></label><label>Status<select name="status"><option value="">Any status</option><option ${filters.status==='ACTIVE'?'selected':''}>ACTIVE</option><option ${filters.status==='BLOCKED'?'selected':''}>BLOCKED</option></select></label><button class="primary">Filter users</button></form>${renderAdminUsers(payload,user.id,esc)}</section>`;
    $('#admin-user-filters').onsubmit=e=>{e.preventDefault();adminUserSkip=0;renderAdminUsersPage(Object.fromEntries(new FormData(e.target)))};
    $('#admin-users-prev')?.addEventListener('click',()=>{adminUserSkip=Math.max(0,adminUserSkip-20);renderAdminUsersPage(filters)});
    $('#admin-users-next')?.addEventListener('click',()=>{adminUserSkip+=20;renderAdminUsersPage(filters)});
    document.querySelectorAll('[data-save-role]').forEach(button=>button.onclick=async()=>{
      const id=Number(button.dataset.saveRole),select=document.querySelector(`[data-user-role="${id}"]`),role=select?.value;
      if(!['ADMIN','USER'].includes(role)){toast('Choose a supported role.');return}
      if(!window.confirm(`Change this account's role to ${role}?`))return;
      try{await api(`/admin/users/${id}/role`,{method:'PUT',body:JSON.stringify({role})});toast('User role updated');renderAdminUsersPage(filters)}catch(err){toast(err.message)}
    });
    document.querySelectorAll('[data-user-status]').forEach(button=>button.onclick=async()=>{
      const id=Number(button.dataset.userStatus),status=button.dataset.nextStatus;
      if(!['ACTIVE','BLOCKED'].includes(status)){toast('Unsupported account status.');return}
      const action=status==='BLOCKED'?'Block':'Activate';if(!window.confirm(`${action} this user account?`))return;
      try{await api(`/admin/users/${id}/status`,{method:'PUT',body:JSON.stringify({status})});toast(`User account ${status.toLowerCase()}`);renderAdminUsersPage(filters)}catch(err){toast(err.message)}
    });
  }catch(err){panel.innerHTML=`<div class="panel empty error" role="alert">Could not load users: ${esc(err.message)}</div>`}
}

async function renderAdminReportsPage(){
  const panel=$('#admin-panel');if(!panel)return;
  panel.innerHTML='<section class="panel admin-loading" role="status">Loading reports…</section>';
  try{const reports=await api('/admin/reports');if(user?.role!=='ADMIN'||currentView!=='admin'||adminSection!=='reports')return;panel.innerHTML=renderAdminReports(reports,esc)}
  catch(err){panel.innerHTML=`<div class="panel empty error" role="alert">Could not load reports: ${esc(err.message)}</div>`}
}

$('#register-toggle')?.addEventListener('click',()=>{$('#login-form').classList.add('hidden');$('#register-form').classList.remove('hidden')});
$('#register-cancel')?.addEventListener('click',()=>{$('#register-form').classList.add('hidden');$('#login-form').classList.remove('hidden')});
$('#register-form')?.addEventListener('submit',async e=>{e.preventDefault();$('#register-error').textContent='';const values=Object.fromEntries(new FormData(e.target));try{await api('/auth/register',{method:'POST',body:JSON.stringify(values)});$('#register-form').classList.add('hidden');$('#login-form').classList.remove('hidden');$('#login-form [name=email]').value=values.email;toast('Account created. Sign in to continue.')}catch(err){$('#register-error').textContent=err.message}});

const openTrackerDetail=openDetail;
openDetail=async function(id){await openTrackerDetail(id);try{const data=await api(`/interview-questions/mine?application_id=${id}&limit=100`),items=data.items||[];$('#detail').insertAdjacentHTML('beforeend',`<h3 class="section-title">Interview memory</h3>${items.map(q=>`<div class="detail-item"><strong>${esc(q.question)}</strong><small>${esc(q.round||'Round not set')} · ${esc(q.difficulty||'')}<br>${esc(q.my_answer||'Answer not recorded')}<br>${q.need_to_improve?`Improve: ${esc(q.need_to_improve)}`:''}</small></div>`).join('')}<form id="question-memory-form"><input name="question" required minlength="5" placeholder="Question you were asked"><input name="round" placeholder="Round, e.g. HR call"><input name="asked_by" placeholder="Company / interviewer"><select name="difficulty"><option value="">Difficulty</option><option>EASY</option><option>MEDIUM</option><option>HARD</option></select><textarea name="my_answer" placeholder="How did you answer?"></textarea><textarea name="need_to_improve" placeholder="What would you improve next time?"></textarea><button class="small-button">Save interview question</button></form>`);$('#question-memory-form').onsubmit=async e=>{e.preventDefault();const v=Object.fromEntries(new FormData(e.target));try{await api('/interview-questions/mine',{method:'POST',body:JSON.stringify({...v,application_id:id})});await openDetail(id)}catch(err){toast(err.message)}}}catch(err){toast(err.message)}};
const detailWithInterviewMemory=openTrackerDetail;
openDetail=async function(id){await detailWithInterviewMemory(id);await loadApplicationPrepResources(id);try{const data=await api(`/interview-questions/mine?application_id=${id}&limit=100`),items=data.items||[];$('#detail').insertAdjacentHTML('beforeend',`<h3 class="section-title">Interview memory</h3>${items.map(q=>`<div class="detail-item"><strong>${esc(q.question)}</strong><small>${esc(q.round||'Round not set')} · ${esc(q.difficulty||'')}<br>${esc(q.my_answer||'Answer not recorded')}<br>${q.need_to_improve?`Improve: ${esc(q.need_to_improve)}`:''}</small></div>`).join('')}<form id="question-memory-form"><input name="question" required minlength="5" placeholder="Question you were asked"><input name="round" placeholder="Round, e.g. HR call"><input name="asked_by" placeholder="Company / interviewer"><select name="difficulty"><option value="">Difficulty</option><option>EASY</option><option>MEDIUM</option><option>HARD</option></select><textarea name="my_answer" placeholder="How did you answer?"></textarea><textarea name="need_to_improve" placeholder="What would you improve next time?"></textarea><button class="small-button">Save interview question</button></form>`);$('#question-memory-form').onsubmit=async e=>{e.preventDefault();const v=Object.fromEntries(new FormData(e.target));try{await api('/interview-questions/mine',{method:'POST',body:JSON.stringify({...v,application_id:id})});await openDetail(id)}catch(err){toast(err.message)}}}catch(err){toast(err.message)}};

async function loadApplicationPrepResources(id){
  const root=$('#application-prep');
  if(!root)return;
  root.innerHTML='<p class="empty">Loading related preparation resources…</p>';
  try{
    const [workspace,skillGap]=await Promise.all([
      api(`/prep/applications/${id}`),api(`/prep/applications/${id}/skill-gap`)
    ]);
    workspace.blogs=await Promise.all((workspace.blogs||[]).map(async blog=>{
      try{return await api(`/blogs/${encodeURIComponent(blog.slug)}`)}catch{return blog}
    }));
    root.innerHTML=renderApplicationPrepResources(workspace,skillGap,esc);
  }catch(error){root.innerHTML=`<p class="error" role="alert">Could not load preparation resources: ${esc(error.message)}</p>`}
}

document.addEventListener('click', async event=>{
  const button=event.target.closest('[data-material-open]');
  if(!button)return;
  const id=Number(button.dataset.materialOpen);
  if(!Number.isInteger(id)||id<1)return;
  const destination=window.open('about:blank','_blank');
  try{
    const material=await api(`/materials/${id}`);
    if(/^https?:\/\//i.test(material.file_url)){
      if(destination)destination.location.href=material.file_url;
      else window.location.href=material.file_url;
      return;
    }
    const headers={};if(token())headers.Authorization=`Bearer ${token()}`;
    const response=await CareerTrackApi.apiFetch(`/materials/${id}/download`,{headers},token());
    if(!response.ok)throw new Error(`Could not open study material (${response.status})`);
    const fileUrl=URL.createObjectURL(await response.blob());
    if(destination)destination.location.href=fileUrl;
    else window.location.href=fileUrl;
    setTimeout(()=>URL.revokeObjectURL(fileUrl),60000);
  }catch(error){destination?.close();toast(error.message)}
});
