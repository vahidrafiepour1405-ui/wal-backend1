(function(){
const status=document.getElementById('onchainStatus'),rows=document.getElementById('onchainRows');
function node(tag,text){const e=document.createElement(tag);e.textContent=text;return e;}
function findRows(x){
 if(Array.isArray(x)) return x;
 if(x&&typeof x==='object'){
  for(const k of ['transactions','items','results','data','rows','transfers','recent']) if(Array.isArray(x[k])) return x[k];
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
async function refresh(){
 status.textContent='در حال دریافت داده عمومی HypurrTrace…';rows.replaceChildren();
 try{
  const response=await fetch('https://trace.hypurrscan.io/api/v1/recent',{cache:'no-store'});
  if(!response.ok)throw Error('HTTP '+response.status);
  const data=await response.json();display(data);
  status.textContent='اتصال موفق · منبع: HypurrTrace / Hypurrscan · '+new Date().toLocaleTimeString('fa-IR');
 }catch(e){status.textContent='دریافت مستقیم انجام نشد. ممکن است شبکه، محدودیت API یا CORS مانع باشد. برای استفاده از پراکسی، API باید روی Render مستقر شود.';}
}
document.getElementById('onchainRefresh').addEventListener('click',refresh);refresh();
})();