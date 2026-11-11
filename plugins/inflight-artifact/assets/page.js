const V=['overview','happened','next'];
function show(){let h=location.hash.slice(1);if(!V.includes(h))h='overview';V.forEach(v=>{document.getElementById('v-'+v).hidden=v!==h;document.querySelector('[data-tab='+v+']').classList.toggle('on',v===h)})}
addEventListener('hashchange',show);show();
document.querySelectorAll('.f').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.f').forEach(x=>x.classList.toggle('on',x===b));const f=b.dataset.f;document.querySelectorAll('.ev').forEach(e=>{e.hidden=f!=='all'&&e.dataset.t!==f})}));
document.querySelectorAll('.copy').forEach(b=>b.addEventListener('click',()=>{try{navigator.clipboard.writeText(b.dataset.c);b.textContent='copied'}catch(e){b.textContent=b.dataset.c}}));
