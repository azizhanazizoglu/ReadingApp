const { contextBridge, ipcRenderer } = require('electron');

// Expose PDF download APIs to renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  setupPdfDownload: (config) => ipcRenderer.invoke('setup-pdf-download', config),
  waitPdfDownload: (config) => ipcRenderer.invoke('wait-pdf-download', config),
  cleanupPdfDownload: () => ipcRenderer.invoke('cleanup-pdf-download'),
});

console.log('Preload script loaded - electronAPI exposed');