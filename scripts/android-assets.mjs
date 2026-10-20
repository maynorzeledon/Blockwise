import fs from 'node:fs';const dest='android/app/src/main/assets';fs.mkdirSync(dest,{recursive:true});fs.cpSync('web',dest,{recursive:true});let js=fs.readFileSync('web/app.js','utf8');
js=js.replace("const blob=new Blob([JSON.stringify({version:1,...state},null,2)]", "if(window.BlockwiseNative){BlockwiseNative.exportBackup(JSON.stringify({version:1,...state},null,2));return}const blob=new Blob([JSON.stringify({version:1,...state},null,2)]");
js=js.replace("if(navigator.share)await navigator.share", "if(window.BlockwiseNative){BlockwiseNative.share(text);return}if(navigator.share)await navigator.share");
js=js.replace("function speak(id){", "function speak(id){if(window.BlockwiseNative){const f=facts.find(f=>f.id===id)[state.language];BlockwiseNative.speak([f.title,f.summary,...f.body].join('. '),state.language);return}");
js=js.replace("()=>window.speechSynthesis?.cancel()", "()=>{window.speechSynthesis?.cancel();window.BlockwiseNative?.stop()}");
js=js.replace("if('serviceWorker'in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{});", "");
// A public Cloudflare origin can be configured after deployment. No credentials are bundled.
const origin=process.env.BLOCKWISE_API_ORIGIN||'';if(origin&&!/^https:\/\/[a-z0-9.-]+(?::\d+)?$/i.test(origin))throw Error('Use a bare HTTPS API origin');js="const API_ORIGIN="+JSON.stringify(origin)+";const originalFetch=window.fetch.bind(window);window.fetch=(url,options)=>{if(typeof url==='string'&&url.startsWith('/api/')){const backend=localStorage.getItem('blockwise-api-origin')||API_ORIGIN;if(!backend)return Promise.reject(new Error('Public backend not configured'));return originalFetch(backend+url,options)}return originalFetch(url,options)};\n"+js;
fs.writeFileSync(dest+'/app.js',js);
