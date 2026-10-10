(function(){
const status=document.getElementById('onchainStatus'),rows=document.getElementById('onchainRows');
// Render's service name from render.yaml; if it has not been deployed yet, use the public provider fallback.
const API_BASE='';
function node(tag,text){const e=document.createElement(tag);e.textContent=text;return e;}
function findRows(x){
 if(Array.isArray(x)) return x;
 if(x&&typeof x==='object'){
  for(const k of ['transactions','items','results','rows','transfers','recent']) if(Array.isArray(x[k])) return x[k];
  if(x.data!==undefined){const nested=findRows(x.data);if(nested.length)return nested;}
  for(const v of Object.values(x)) if(Array.isArray(v)) return v;
 }
 return [];
}
function display(x){
 rows.replaceChildren();const arr=findRows(x);
 if(!arr.length){const pre=node('pre',JSON.stringify(x,null,2).slice(0,1800));pre.style.cssText='white-space:pre-wrap;overflow-wrap:anywhere;font-size:11px;max-height:260px;overflow:auto;background:#f6f8fc;padding:12px;border-radius:12px';rows.append(pre);return;}
 for(const item of arr.slice(0,10)){
  const r=document.createElement('div');r.style.cssText='padding:11px;margin:7px 0;border:1px solid #e4eaf4;border-radius:12px;overflow-wrap:anywhere;font-size:12px';
  const obj=item&&typeof item==='object'?item:{value:item};
  const title=obj.method_name||obj.method||obj.action||obj.token_symbol||obj.symbol||obj.type||'تراکنش شبکه';
  r.append(node('b',String(title)));
  const details=Object.entries(obj).filter(([k,v])=>v!==null&&v!==undefined&&typeof v!=='object'&&!['input','calldata'].includes(k)).slice(0,6).map(([k,v])=>k+': '+String(v)).join(' · ');
  if(details)r.append(node('div',details));
  const hash=obj.hash||obj.tx_hash||obj.transaction_hash;
  if(typeof hash==='string'&&hash.startsWith('0x')){const a=node('a','مشاهده تراکنش');a.href='https://hypurrscan.io/tx/'+hash;a.target='_blank';a.rel='noopener noreferrer';a.style.cssText='display:inline-block;margin-top:7px;color:#246bfe';r.append(a);}
  rows.append(r);
 }
}
async function getJson(url){
 const response=await fetch(url,{cache:'no-store'});
 if(!response.ok)throw Error('HTTP '+response.status);
 return response.json();
}
async function refresh(){
 status.textContent='در حال بررسی API WAL و دریافت داده آنچین…';rows.replaceChildren();
 try{
  // Prefer our backend so the app does not depend on browser CORS support for the provider.
  const data=await getJson(API_BASE+'/onchain/hypurrscan/recent');
  display(data);
  status.textContent='اتصال به API WAL موفق · منبع داده: HypurrTrace / Hypurrscan · '+new Date().toLocaleTimeString('fa-IR')+' · تراکنش‌ها به‌تنهایی اثبات انباشت نهنگ نیستند.';
  return;
 }catch(backendError){
  try{
   const data=await getJson('https://trace.hypurrscan.io/api/v1/recent');
   display(data);
   status.textContent='داده مستقیم HypurrTrace دریافت شد؛ API بک‌اند WAL هنوز در دسترس نیست یا مستقر نشده · '+new Date().toLocaleTimeString('fa-IR');
  }catch(providerError){
   status.textContent='دریافت داده ناموفق است. احتمالاً API WAL هنوز روی Render فعال نشده یا دسترسی شبکه/CORS به HypurrTrace مسدود است. پس از استقرار بک‌اند، دوباره تازه‌سازی کنید.';
   const help=node('p','وضعیت API: '+API_BASE+'/status');help.style.cssText='font-size:12px;overflow-wrap:anywhere;color:#6d7b96';rows.replaceChildren(help);
  }
 }
}
document.getElementById('onchainRefresh').addEventListener('click',refresh);refresh();
})();