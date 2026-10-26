const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('roadscanDesktop',{
 getToken:()=>ipcRenderer.invoke('roadscan:get-token'),
 selectModel:()=>ipcRenderer.invoke('roadscan:select-model')
});
