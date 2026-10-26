const {app,BrowserWindow,dialog,ipcMain,shell}=require('electron');
const {spawn}=require('node:child_process');
const {randomBytes,createHash}=require('node:crypto');
const fs=require('node:fs');const path=require('node:path');const http=require('node:http');
let backend=null,win=null;const token=randomBytes(32).toString('hex');const port=18743;
const url=`http://127.0.0.1:${port}`;
const dataDir=()=>app.getPath('userData');
function backendExe(){return app.isPackaged?path.join(process.resourcesPath,'backend','roadscan-backend.exe'):null}
function startBackend(){
 const exe=backendExe();if(!exe||!fs.existsSync(exe))throw Error('Packaged backend missing. Build the Windows installer using BUILD_WINDOWS.md.');
 const env={...process.env,ROADSCAN_API_KEY:token,ROADSCAN_DATA_DIR:dataDir(),ROADSCAN_PORT:String(port)};
 const config=path.join(dataDir(),'model.json');
 if(fs.existsSync(config)){try{const record=JSON.parse(fs.readFileSync(config,'utf8'));const raw=fs.readFileSync(record.path);const sha=createHash('sha256').update(raw).digest('hex');if(sha===record.sha256){env.ROADSCAN_YOLO_WEIGHTS=record.path;env.ROADSCAN_YOLO_SHA256=record.sha256}}catch(e){console.error('Model configuration invalid',e.message)}}
 backend=spawn(exe,[],{env,windowsHide:true,stdio:'ignore'});
 backend.on('exit',code=>console.error('Backend exited:',code));
}
function check(){return new Promise(resolve=>{const req=http.get(`${url}/api/health`,res=>{res.resume();resolve(res.statusCode===200)});req.on('error',()=>resolve(false));req.setTimeout(1200,()=>{req.destroy();resolve(false)})})}
async function waitForBackend(){for(let i=0;i<60;i++){if(await check())return true;await new Promise(r=>setTimeout(r,500))}return false}
function createWindow(){win=new BrowserWindow({width:1440,height:900,minWidth:960,minHeight:650,backgroundColor:'#0c1418',webPreferences:{preload:path.join(__dirname,'preload.cjs'),contextIsolation:true,nodeIntegration:false,sandbox:true}});win.webContents.setWindowOpenHandler(({url})=>{if(url.startsWith('https://'))shell.openExternal(url);return{action:'deny'}});win.loadURL(url)}
ipcMain.handle('roadscan:get-token',()=>token);
ipcMain.handle('roadscan:select-model',async()=>{
 const result=await dialog.showOpenDialog(win,{title:'Choose trained RoadScan YOLO checkpoint',properties:['openFile'],filters:[{name:'YOLO model',extensions:['pt']}]});
 if(result.canceled||!result.filePaths.length)return{ok:false,message:'No model selected.'};
 const src=result.filePaths[0];const stat=fs.statSync(src);if(stat.size>1024*1024*1024)return{ok:false,message:'Model file is too large.'};
 const dir=path.join(dataDir(),'models');fs.mkdirSync(dir,{recursive:true});const dst=path.join(dir,'best.pt');fs.copyFileSync(src,dst);
 const sha=createHash('sha256').update(fs.readFileSync(dst)).digest('hex');fs.writeFileSync(path.join(dataDir(),'model.json'),JSON.stringify({path:dst,sha256:sha},null,2));
 return{ok:true,message:'Checkpoint copied. Restart RoadScan to validate and activate it. Only use checkpoints you trust.'};
});
app.whenReady().then(async()=>{try{startBackend();if(!await waitForBackend())throw Error('Backend did not become healthy within 30 seconds.');createWindow()}catch(e){dialog.showErrorBox('RoadScan startup failed',String(e.message));app.quit()}});
app.on('window-all-closed',()=>{app.quit()});app.on('before-quit',()=>{if(backend)backend.kill()});
