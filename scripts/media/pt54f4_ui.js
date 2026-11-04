'use strict';
let token = '', plannedBatch = '', currentBatch = '';
let libraryRows = [];
let captionEtag = "";
const $ = id => document.getElementById(id);
const fields = ['family','size','material','valve','style','variant','role','sequence','version'];
function values(){const out={};for(const key of fields)out[key]=$(key).value;const file=$('file').files[0];out.extension=file?file.name.toLowerCase().split('.').pop():'';return out;}
function notice(id,text,kind=''){const target=$(id);target.className=text?'notice '+kind:'';target.textContent=text;}
function element(name,content){const n=document.createElement(name);if(content!==undefined)n.textContent=content;return n;}
function updateFields(){const family=$('family').value;for(const el of document.querySelectorAll('[data-applies]')){const k=el.dataset.applies;el.hidden=(k==='tank'&&family==='origin')||(k==='valve'&&!['refine','essence'].includes(family))||(k==='origin'&&family!=='origin');}previewName();}
function previewName(){const v=values();const n=Number(v.sequence),r=Number(v.version);let start;if(['refine','essence'].includes(v.family))start=[v.family,v.size,v.material,v.valve,v.style].join('_');else if(v.family==='harmony')start=['harmony',v.size,v.material].join('_');else start=['origin',v.variant].join('_');$('preview-name').textContent=`${start}_${v.role}_${String(n).padStart(2,'0')}_v${String(r).padStart(2,'0')}.${v.extension||'???'}`;}
async function api(url,method='GET',body=null,raw=false){const options={method,headers:{}};if(method==='POST'){options.headers['X-PT54-CSRF']=token;options.headers['Content-Type']=raw?'application/octet-stream':'application/json';options.body=raw?body:JSON.stringify(body);};const result=await fetch(url,options);const data=await result.json();if(!result.ok)throw new Error(data.error||`HTTP ${result.status}`);return data;}
async function refresh(){const data=await api('/api/state');token=data.csrf;$('overview').textContent=`${data.intake.file_count} intake item(s) · ${data.batches.length} review batch(es) · ${data.published_count} published revision(s). Library: ${data.root}`;
const selector=$('intake-select');const selected=selector.value;selector.replaceChildren(new Option('All eligible intake photos',''));const list=$('intake-list');list.replaceChildren();for(const item of data.intake.candidates){selector.add(new Option(item.filename,item.filename));list.append(element('li',`${item.filename} · ${item.status}`));}for(const item of data.intake.rejected)list.append(element('li',`${item.filename} · REJECTED: ${item.reason}`));for(const item of data.intake.unsafe_items)list.append(element('li',`${item} · UNSAFE`));selector.value=[...selector.options].some(o=>o.value===selected)?selected:'';if(!list.children.length)list.append(element('li','No photographs imported yet.'));
const batch=$('batch');const old=batch.value;batch.replaceChildren(new Option('Choose a review batch',''));for(const item of data.batches)batch.add(new Option(`${item.name}${item.published?' · published':''}`,item.name));batch.value=[...batch.options].some(o=>o.value===old)?old:'';if(!batch.value&&data.batches.length)batch.value=data.batches[0].name;await showBatch();}
async function showBatch(){plannedBatch='';currentBatch=$('batch').value;$('confirm-name').value='';$('ack').checked=false;$('publish').disabled=true;$('gallery').replaceChildren();$('plan-output').textContent='';notice('batch-msg','');if(!currentBatch){notice('batch-msg','No batch prepared yet.');return;}try{const data=await api('/api/batch?name='+encodeURIComponent(currentBatch));notice('batch-msg',`${data.count} staged photograph(s). Inspect thumbnails before publishing.`);for(const item of data.items){const card=element('article');card.className='thumb';const image=element('img');image.src=item.preview;image.alt=item.name;card.append(image,element('h3',item.name));if(item.conflicts.length)card.append(element('small','WARNING: destination collision'));$('gallery').append(card);}}catch(e){notice('batch-msg',e.message,'error');}}
async function upload(){const file=$('file').files[0];if(!file){notice('ingest-msg','Choose an image first.','error');return;}if(file.size>64*1024*1024){notice('ingest-msg','64 MiB upload limit exceeded. Use the terminal intake folder for larger originals.','error');return;}try{const params=new URLSearchParams(values());notice('ingest-msg','Validating image and saving to intake…');const data=await api('/api/upload?'+params.toString(),'POST',file,true);notice('ingest-msg',`Added ${data.upload.name} (${data.upload.image.width}×${data.upload.image.height}) to intake only. Nothing published.`,'success');await refresh();}catch(e){notice('ingest-msg',e.message,'error');}}
async function prepareBatch(){try{notice('prepare-msg','Preparing derivatives with ImageMagick…');const name=$('intake-select').value;const result=await api('/api/prepare','POST',{filename:name||null});notice('prepare-msg',`Prepared ${result.batch.count} item(s) in ${result.batch.name}. Review the thumbnails below.`,'success');await refresh();$('batch').value=result.batch.name;await showBatch();}catch(e){notice('prepare-msg',e.message,'error');}}
async function planBatch(){const name=$('batch').value;if(!name){notice('batch-msg','Select a batch first.','error');return;}try{const result=await api('/api/plan','POST',{batch:name});plannedBatch=name;$('plan-output').textContent=result.items.map(x=>`${x.name}\n  ${x.configuration} · ${x.role} #${x.sequence} · revision ${x.version}`).join('\n\n')+'\n\n'+result.note;notice('batch-msg','Publication plan verified. Review the batch carefully before confirming.','success');togglePublish();}catch(e){plannedBatch='';$('plan-output').textContent='';notice('batch-msg',e.message,'error');togglePublish();}}
function togglePublish(){$('publish').disabled=!(plannedBatch&&plannedBatch===$('batch').value&&$('confirm-name').value===plannedBatch&&$('ack').checked);}
async function publishBatch(){if($('publish').disabled)return;const batch=plannedBatch;try{notice('publish-msg','Verifying batch checksums and copying files to TEST…');const result=await api('/api/publish','POST',{batch,approval:$('confirm-name').value,confirmed:$('ack').checked});notice('publish-msg',`Published to local TEST source. Receipt: ${result.receipt}. Review site behavior and Git changes before any commit.`, 'success');plannedBatch='';await refresh();}catch(e){notice('publish-msg',e.message,'error');}}
async function refreshLibrary(){
  const result=await api('/api/library');libraryRows=result.configurations;captionEtag=result.caption_etag;
  $('library-overview').textContent=`${result.count} selected configurations · Read-only TEST registry (not PROD)`;
  filterLibrary();
}
function filterLibrary(){
  const family=$('library-family').value, selector=$('library-config'), previous=selector.value;
  const available=libraryRows.filter(row=>!family||row.family===family);
  selector.replaceChildren();
  for(const row of available)selector.add(new Option(`${row.key} · ${row.count} images`,row.key));
  if(available.length){selector.value=available.some(row=>row.key===previous)?previous:available[0].key;}
  showLibrary();
}
function selectedCaption(){
  const row=libraryRows.find(item=>item.key===$('library-config').value);
  const photo=row?.photos.find(item=>item.id===$('caption-photo').value);
  return {row,photo};
}
function updateCaptionForm(){
  const {row,photo}=selectedCaption(),scope=$('caption-scope').value;
  $('caption-save').disabled=!photo;$('caption-clear').disabled=!photo;
  if(!photo){$('caption-text').value='';$('caption-info').textContent='Choose a photo.';return;}
  const explicit=scope==='family'?photo.family_caption:photo.configuration_caption;
  $('caption-text').value=explicit||photo.label;
  $('caption-info').textContent=`Original: ${photo.base_label} · Displayed: ${photo.label} (${photo.caption_source}). `+
    (scope==='family'?'Family updates affect all configurations with this photo role; a configuration override takes precedence.':'Only the selected configuration will change.');
  $('caption-version').textContent=`Photo ID: ${photo.id}`;
  notice('caption-msg','');
}
async function saveCaption(clear=false){
  const {row,photo}=selectedCaption();if(!row||!photo)return;
  const scope=$('caption-scope').value,caption=clear?'':$('caption-text').value.trim();
  if(!clear&&(!caption||caption.length>96)){notice('caption-msg','Enter a subtitle of 1–96 characters. Use Remove to reset an override.','error');return;}
  try{
    const result=await api('/api/caption','POST',{key:row.key,photo_id:photo.id,scope,caption,expected_etag:captionEtag});
    notice('caption-msg',result.changed?'Saved to TEST. Review the local website and Git diff before deployment.':'No change needed.','success');
    const message=$('caption-msg').textContent;
    await refreshLibrary();
    $('caption-photo').value=photo.id;
    updateCaptionForm();notice('caption-msg',message,'success');
  }catch(e){notice('caption-msg',e.message,'error');}
}
function showLibrary(){
  const row=libraryRows.find(item=>item.key===$('library-config').value);
  const gallery=$('library-gallery');gallery.replaceChildren();notice('library-msg','');
  if(!row){notice('library-msg','No approved configurations in this filter.');$('caption-photo').replaceChildren();return;}
  const chooser=$('caption-photo'),oldSelection=chooser.value;chooser.replaceChildren();
  for(const photo of row.photos)chooser.add(new Option(`${photo.label} [${photo.id}]`,photo.id));
  if(row.photos.length)chooser.value=row.photos.some(photo=>photo.id===oldSelection)?oldSelection:row.photos[0].id;
  updateCaptionForm();
  const missing=row.photos.filter(photo=>!photo.available).length;
  notice('library-msg',`${row.key} · ${row.count} gallery images${missing?` · ${missing} missing`:''}. Click a photograph to open full size.`,missing?'error':'');
  for(const photo of row.photos){
    const card=element('article');card.className='thumb'+(photo.available?'':' missing');
    const zoom=element('button');zoom.type='button';zoom.disabled=!photo.available;
    const thumb=element('img');thumb.src=photo.preview;thumb.loading='lazy';thumb.alt=photo.label;
    zoom.append(thumb);zoom.addEventListener('click',()=>{
      $('library-large').src=photo.full;
      $('library-large').alt=`${row.key}, ${photo.label}`;
      $('library-caption').textContent=`${photo.label} · ${row.key} · ${photo.filename} · ${photo.source}`;
      $('library-lightbox').showModal();
    });
    card.append(zoom,element('h3',photo.label));
    card.append(element('small',photo.filename+' · '+photo.source+(photo.available?'':' · MISSING')));
    gallery.append(card);
  }
}
window.addEventListener('DOMContentLoaded',()=>{for(const key of fields)$(key).addEventListener('change',()=>{if(key==='family')updateFields();else previewName();});$('file').addEventListener('change',previewName);$('upload').addEventListener('click',upload);$('prepare').addEventListener('click',prepareBatch);$('refresh').addEventListener('click',()=>refresh().catch(e=>notice('ingest-msg',e.message,'error')));$('batch').addEventListener('change',showBatch);$('plan').addEventListener('click',planBatch);$('confirm-name').addEventListener('input',togglePublish);$('ack').addEventListener('change',togglePublish);$('publish').addEventListener('click',publishBatch);const drop=$('drop');drop.addEventListener('dragover',e=>{e.preventDefault();drop.classList.add('dragover');});drop.addEventListener('dragleave',()=>drop.classList.remove('dragover'));drop.addEventListener('drop',e=>{e.preventDefault();drop.classList.remove('dragover');if(e.dataTransfer.files.length){$('file').files=e.dataTransfer.files;previewName();}});$('library-family').addEventListener('change',filterLibrary);
$('library-config').addEventListener('change',showLibrary);
$('caption-photo').addEventListener('change',updateCaptionForm);
$('caption-scope').addEventListener('change',updateCaptionForm);
$('caption-save').addEventListener('click',()=>saveCaption(false));
$('caption-clear').addEventListener('click',()=>saveCaption(true));
$('library-refresh').addEventListener('click',()=>refreshLibrary().catch(e=>notice('library-msg',e.message,'error')));
$('library-close').addEventListener('click',()=>$('library-lightbox').close());
$('library-lightbox').addEventListener('close',()=>{$('library-large').removeAttribute('src');});
updateFields();refresh().catch(e=>notice('ingest-msg',e.message,'error'));
refreshLibrary().catch(e=>notice('library-msg',e.message,'error'));});
