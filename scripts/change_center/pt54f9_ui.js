'use strict';
const el = id => document.getElementById(id);
const fields = ['title','category','family','reference','before','after','notes','acceptance'];
const state = { csrf:'', rows:[], current:null, revision:0 };
function notice(text, isError=false){const p=el('notice');p.textContent=text;p.className='notice '+(isError?'error':'success');}
async function api(endpoint, data){
  const res = await fetch('/api/'+endpoint, {method:'POST', headers:{'Content-Type':'application/json','X-PT54-CSRF':state.csrf},body:JSON.stringify(data)});
  const body=await res.json();
  if(!res.ok || body.error) throw Error(body.error || 'Request failed');
  return body;
}
function details(){return Object.fromEntries(fields.map(k=>[k,el(k).value]));}
function selected(){return state.rows.find(r=>r.id===state.current) || null;}
function text(id, value){el(id).textContent=value || '—';}
function updatePreview(){text('preview-before',el('before').value);text('preview-after',el('after').value);}
function renderList(){
  const holder=el('request-list');holder.replaceChildren();
  const filter=el('filter').value;
  for(const row of state.rows.filter(r=>!filter || r.status===filter).reverse()){
    const b=document.createElement('button');b.type='button';b.className='item'+(state.current===row.id?' selected':'');
    const title=document.createElement('strong'); title.textContent=row.id+' · '+row.title;
    const meta=document.createElement('small');meta.textContent=row.status.replace('_',' ')+' · '+row.category+' · '+row.family;
    b.append(title,meta); b.addEventListener('click',()=>choose(row.id));holder.append(b);
  }
  if(!holder.children.length){const x=document.createElement('p');x.className='muted';x.textContent='No requests in this view.';holder.append(x);}
}
function choose(id){
  state.current=id;
  const row=selected();
  for(const key of fields) el(key).value=row?row[key]:(key==='category'?'caption':key==='family'?'unspecified':'');
  el('editor-heading').textContent=row?`${row.id} · ${row.title}`:'New client request';
  el('editor-status').textContent=row?`Status: ${row.status.replace('_',' ')} · version ${row.version} · last updated ${row.updated_utc}`:'Save a draft before sending it for review.';
  const editable=!row||['draft','in_review'].includes(row.status);
  for(const key of fields) el(key).disabled=!editable;
  el('save').disabled=!editable;
  el('submit').disabled=!row||row.status!=='draft';
  el('redraft').disabled=!row||!['in_review','deferred','rejected','approved'].includes(row.status);
  el('defer').disabled=!row||!['draft','in_review'].includes(row.status);
  el('reject').disabled=!row||row.status!=='in_review';
  el('approve').disabled=!row||row.status!=='in_review';
  el('reviewer').value='';el('confirmation').value='';
  el('history').replaceChildren();
  if(row){for(const h of [...row.history].reverse()){
    const li=document.createElement('li');li.textContent=`${h.at} · ${h.action} · ${h.actor}`;el('history').append(li);
  }}
  updatePreview();renderList();
}
async function refresh(keep=true){
  const res=await fetch('/api/state',{cache:'no-store'});const payload=await res.json();
  if(!res.ok) throw Error(payload.error || 'Cannot load change register');
  state.csrf=payload.csrf;state.rows=payload.register.requests;state.revision=payload.register.revision;
  const counts={};for(const r of state.rows)counts[r.status]=(counts[r.status]||0)+1;
  el('summary').textContent=`${state.rows.length} requests · ${counts.approved||0} approved · ${counts.in_review||0} in review · Stored in ${payload.root}`;
  choose(keep?state.current:null);
}
async function save(){
  const row=selected();const payload=details();
  const result=await api(row?'edit':'create',row?{...payload,id:row.id,expected_version:row.version}:payload);
  await refresh(false);choose(result.request.id);notice(`${result.request.id} saved in TEST change register.`);
}
async function move(to){
  const row=selected();if(!row) throw Error('Select a saved request first.');
  const payload={id:row.id,expected_version:row.version,status:to};
  if(to==='approved') {payload.reviewer=el('reviewer').value;payload.confirmation=el('confirmation').value;}
  const result=await api('status',payload);
  await refresh(false);choose(result.request.id);notice(`${result.request.id} → ${to}. No application or production changes were made.`);
}
async function exportApproved(){
  const receipt=(await api('export',{})).export;
  el('export-result').textContent=`Exported ${receipt.count} approved request(s).\n${receipt.file}\nSHA-256: ${receipt.sha256}\n${receipt.note}`;
}
function bind(id, action){el(id).addEventListener('click',()=>Promise.resolve().then(action).catch(e=>notice(e.message,true)));}

// PT54-F10: Presentation text is a narrow, versioned TEST source file.
const presentation = { revision: null, labels: null, specs: [] };
function presentationNotice(message, error=false) {
  const out=el('presentation-notice');out.textContent=message;
  out.className='notice '+(error?'error':'success');
}
function presentationValues(){
  return Object.fromEntries(presentation.specs.map(({key})=>[key,el('ps-'+key).value]));
}
function paintPresentation(){
  const holder=el('presentation-fields');holder.replaceChildren();
  for(const item of presentation.specs){
    const label=document.createElement('label');
    const name=document.createElement('span');name.textContent=item.title;
    const input=document.createElement('input');input.id='ps-'+item.key;
    input.maxLength=80;input.value=presentation.labels[item.key];input.required=true;
    const info=document.createElement('small');info.textContent=item.help;info.className='muted';
    label.append(name,input,info);holder.append(label);
  }
  el('presentation-summary').textContent='Source revision '+presentation.revision+' · '+presentation.specs.length+' editable wording fields · Other storefront content remains protected.';
}
async function refreshPresentation(){
  const response=await fetch('/api/presentation',{cache:'no-store'});const body=await response.json();
  if(!response.ok)throw Error(body.error||'Cannot read presentation settings');
  presentation.revision=body.document.revision;
  presentation.labels=body.document.labels;
  presentation.specs=body.specs;
  paintPresentation();
}
async function savePresentation(){
  const result=await api('presentation/save',{
    expected_revision:presentation.revision,labels:presentationValues()
  });
  await refreshPresentation();
  presentationNotice('Saved '+result.changed.length+' field(s) to TEST; previous source backed up at '+result.backup+'. Refresh the local storefront to preview. No Git or PROD action.');
}

function init(){
  bind('new',()=>{choose(null);notice('New draft. Existing records remain unchanged.');});
  bind('refresh',()=>refresh(true));bind('save',save);
  bind('submit',()=>move('in_review'));bind('redraft',()=>move(selected()?.status==='approved'?'in_review':'draft'));
  bind('defer',()=>move('deferred'));bind('reject',()=>move('rejected'));
  bind('approve',()=>move('approved'));bind('export',exportApproved);
  el('filter').addEventListener('change',renderList);
  for(const id of ['before','after'])el(id).addEventListener('input',updatePreview);
  bind('presentation-save',()=>savePresentation().catch(e=>{presentationNotice(e.message,true);}));
  bind('presentation-reset',()=>refreshPresentation().then(()=>presentationNotice('Unsaved edits discarded.')).catch(e=>presentationNotice(e.message,true)));
  refreshPresentation().catch(e=>presentationNotice(e.message,true));
  refresh(false).catch(e=>notice(e.message,true));
}
init();
