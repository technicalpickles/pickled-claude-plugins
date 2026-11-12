const D=(()=>{try{return JSON.parse(document.getElementById('inflight-data').textContent)}catch(e){return {tasks:[],sessions:[],repos:[]}}})();
const V=[...document.querySelectorAll('nav [data-tab]')].map(a=>a.dataset.tab);
function show(){let h=location.hash.slice(1);if(!V.includes(h))h='overview';V.forEach(v=>{document.getElementById('v-'+v).hidden=v!==h;document.querySelector('nav [data-tab="'+v+'"]').classList.toggle('on',v===h)})}
addEventListener('hashchange',show);show();
document.querySelectorAll('[data-go]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();location.hash=a.dataset.go;const t=a.dataset.track&&document.getElementById(a.dataset.track);t?t.scrollIntoView():scrollTo(0,0)}));
document.querySelectorAll('.f').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.f').forEach(x=>x.classList.toggle('on',x===b));const f=b.dataset.f;document.querySelectorAll('.ev').forEach(e=>{e.hidden=f!=='all'&&e.dataset.g!==f})}));
document.querySelectorAll('.copy').forEach(b=>b.addEventListener('click',()=>{try{navigator.clipboard.writeText(b.dataset.c);b.textContent='copied'}catch(e){b.textContent=b.dataset.c}}));

// Task popup: formats raw taskwarrior text (headline, paragraphs, (a)(b) lists, code spans, PR links, dated notes).
const esc=s=>String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'})[c]);
const SHORT=Object.fromEntries(D.repos.map(r=>[r.split('/')[1],r]));
const rxq=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const INLINE=new RegExp([
 '(?<ref>[\\w.-]+\\/[\\w.-]+#\\d+)',
 Object.keys(SHORT).length?'(?<sref>\\b(?:'+Object.keys(SHORT).map(rxq).join('|')+')#\\d+)':'(?<sref>(?!))',
 "(?<q>(?<![\\w])'[^'\\n]{1,48}?'(?![\\w]))",
 '(?<flag>(?<![\\w-])--[a-z][\\w-]*)',
 '(?<env>\\b[A-Z][A-Z0-9]*_[A-Z0-9_]+\\b)',
 '(?<path>~?\\/?[\\w.@-]+(?:\\/[\\w.@<>:#-]+)+)',
 '(?<file>\\b[\\w-]+\\.(?:json5?|mjs|md|sh|ya?ml|env|toml|py|pdf)\\b)'
].join('|'),'g');
function inline(t){
  let out='',last=0,m;INLINE.lastIndex=0;
  while((m=INLINE.exec(t))){
    let s=m[0],tail='';const g=m.groups;
    if(g.path){const k=s.match(/[.,:;)]+$/);if(k){tail=k[0];s=s.slice(0,-tail.length)}}
    out+=esc(t.slice(last,m.index));last=m.index+m[0].length;
    const pr=g.ref||g.sref;
    if(pr){const [r,n]=pr.split('#');out+='<a href="https://github.com/'+(r.includes('/')?r:SHORT[r])+'/pull/'+n+'">'+esc(pr)+'</a>'}
    else out+='<code>'+esc(g.q?s.slice(1,-1):s)+'</code>';
    out+=esc(tail);
  }
  return out+esc(t.slice(last));
}
const sentences=t=>t.split(/(?<=[.!?])\s+(?=[A-Z0-9(])/);
function paras(t,max){const out=[];let cur='';sentences(t).forEach(s=>{if(cur&&(cur+' '+s).length>max){out.push(cur);cur=s}else cur=cur?cur+' '+s:s});if(cur)out.push(cur);return out.map(p=>'<p>'+inline(p)+'</p>').join('')}
function splitHead(d){let depth=0;for(let i=0;i<d.length;i++){const c=d[i];if(c==='(')depth++;else if(c===')')depth--;else if(!depth){if(d.substr(i,4)===' -- ')return [d.slice(0,i),d.slice(i+4)];if(c==='.'&&d[i+1]===' '&&/[A-Z]/.test(d[i+2]||''))return [d.slice(0,i),d.slice(i+2)]}}return [d.replace(/\.$/,''),'']}
function body(b){
  if(!b)return '';
  const a=b.indexOf('(a) ');
  if(a>-1&&b.indexOf('(b) ')>a){
    const pre=b.slice(0,a).trim(),items=b.slice(a).split(/\s*\(([a-z])\)\s+/).slice(1),lis=[];let post='';
    for(let i=0;i<items.length;i+=2){let txt=items[i+1].trim().replace(/,$/,'');if(i+2>=items.length){const cut=sentences(txt);txt=cut.shift();post=cut.join(' ')}lis.push('<li>'+inline(txt.replace(/\.$/,''))+'</li>')}
    return (pre?paras(pre,340):'')+'<ul>'+lis.join('')+'</ul>'+(post?paras(post,340):'');
  }
  return paras(b,340);
}
function annos(list){
  const seen={},rows=[];
  (list||[]).forEach(a=>{if(seen[a])return;seen[a]=1;const dm=a.match(/\d{4}-\d{2}-\d{2}/);let txt=a;if(dm&&a.indexOf(dm[0])===0)txt=a.slice(10).replace(/^[:,]?\s*/,'');rows.push({date:dm?dm[0]:'',txt})});
  rows.sort((x,y)=>x.date<y.date?1:x.date>y.date?-1:0);
  const card=r=>'<div class="note-row"><time>'+(r.date||'undated')+'</time><div>'+paras(r.txt,380)+'</div></div>';
  if(!rows.length)return '';
  let h='<h3>History</h3>'+rows.slice(0,2).map(card).join('');
  if(rows.length>2)h+='<details><summary>'+(rows.length-2)+' earlier note'+(rows.length>3?'s':'')+'</summary>'+rows.slice(2).map(card).join('')+'</details>';
  return h;
}
function sessFor(t){
  const mine=D.sessions.filter(s=>(s.tasks||[]).some(p=>t.uuid.startsWith(p)));
  return mine.length?'<h3>Sessions</h3><ul>'+mine.map(s=>'<li><span class="chip quiet">'+esc(s.state)+'</span> '+esc(s.title||s.id)+(s.note?'<small>'+esc(s.note)+'</small>':'')+'</li>').join('')+'</ul>':'';
}
const dlg=document.getElementById('dlg'),dbody=document.getElementById('dlg-body');
function openTask(pre){
  const t=D.tasks.find(x=>x.uuid.startsWith(pre));if(!t)return;
  const hb=splitHead(t.description);
  const meta='<span class="chip open">'+esc(t.project||'no project')+'</span> '+(t.tags||[]).map(g=>'<span class="chip quiet">'+esc(g)+'</span>').join(' ')+' <code>'+esc(t.uuid.slice(0,8))+'</code>';
  dbody.innerHTML='<h2>'+inline(hb[0])+'</h2><div class="meta">'+meta+'</div>'+sessFor(t)+'<div class="desc">'+body(hb[1])+'</div>'+annos(t.annotations)+'<button type="button" id="dlg-close">Close</button>';
  document.getElementById('dlg-close').onclick=()=>dlg.close();
  dlg.showModal();
}
document.addEventListener('click',e=>{const r=e.target.closest&&e.target.closest('.task');if(r&&!e.target.closest('a:not(.task)')){e.preventDefault();openTask(r.dataset.t)}if(e.target===dlg)dlg.close()});
document.addEventListener('keydown',e=>{if(e.key==='Enter'&&e.target.classList&&e.target.classList.contains('task'))openTask(e.target.dataset.t)});
