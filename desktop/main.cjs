const {app,BrowserWindow,protocol,net,shell,ipcMain,Menu}=require('electron');const path=require('node:path');const {pathToFileURL}=require('node:url');
protocol.registerSchemesAsPrivileged([{scheme:'https',privileges:{standard:true,secure:true,supportFetchAPI:true,corsEnabled:true}}]);
const origin='https://blockwise.local',repo='https://github.com/maynorzeledon/Blockwise';
function safeExternal(url){try{const u=new URL(url);if(u.protocol!=='https:')return false;return ['github.com','minecraft.wiki','www.minecraft.net','wiki.ronlab.site'].includes(u.hostname)}catch{return false}}
async function latestRelease(){const r=await net.fetch('https://api.github.com/repos/maynorzeledon/Blockwise/releases/latest',{headers:{'Accept':'application/vnd.github+json'}});if(!r.ok)throw Error('Release unavailable');const v=await r.json();return {tag_name:v.tag_name,assets:v.assets.map(a=>({name:a.name,browser_download_url:a.browser_download_url}))}}
app.whenReady().then(async()=>{
 protocol.handle('https',request=>{const u=new URL(request.url);if(u.origin!==origin)return net.fetch(request.url,{bypassCustomProtocolHandlers:true});let name=decodeURIComponent(u.pathname);if(name==='/'||name==='/app/'||name==='/app')name='/index.html';const root=path.join(__dirname,'web');const target=path.resolve(root,'.'+name);if(!target.startsWith(root+path.sep))return new Response('Not found',{status:404});return net.fetch(pathToFileURL(target).href)});
 ipcMain.handle('latest-release',()=>latestRelease());ipcMain.handle('open-external',(_event,url)=>{if(safeExternal(url))return shell.openExternal(url)});
 const win=new BrowserWindow({width:1180,height:820,minWidth:360,minHeight:480,backgroundColor:'#111e19',title:'Blockwise',webPreferences:{preload:path.join(__dirname,'preload.cjs'),nodeIntegration:false,contextIsolation:true,sandbox:true}});
 win.webContents.setWindowOpenHandler(({url})=>{if(safeExternal(url))shell.openExternal(url);return {action:'deny'}});win.webContents.on('will-navigate',(e,url)=>{if(!url.startsWith(origin+'/')){e.preventDefault();if(safeExternal(url))shell.openExternal(url)}});
 Menu.setApplicationMenu(Menu.buildFromTemplate([{label:'Blockwise',submenu:[{label:'Check for updates / Buscar actualizaciones',click:()=>win.webContents.executeJavaScript('window.BlockwiseUpdates?.check(true)')},{label:'Downloads / Descargas',click:()=>shell.openExternal(repo+'/releases')},{type:'separator'},{role:'quit'}]},{label:'View',submenu:[{role:'reload'},{role:'resetZoom'},{role:'zoomIn'},{role:'zoomOut'},{role:'togglefullscreen'}]}]));
 await win.loadURL(origin+'/');
 if(process.argv.includes('--smoke-test')){try{
  await new Promise(r=>setTimeout(r,5000));
  const result=await win.webContents.executeJavaScript("JSON.stringify({cards:document.querySelectorAll('.feed-grid .card').length,hero:!!document.querySelector('.hero'),bridge:!!window.BlockwiseDesktop})");
  const parsed=JSON.parse(result);if(parsed.cards<1||parsed.hero||!parsed.bridge)throw Error(result);
  require('node:fs').writeFileSync(path.join(app.getPath('temp'),'blockwise-windows-smoke.json'),result);app.exit(0);
 }catch(e){console.error(e);app.exit(1)}}
});app.on('window-all-closed',()=>app.quit());
