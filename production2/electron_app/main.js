const { app, BrowserWindow } = require('electron');
const path = require('path');
const url = require('url');
const fs = require('fs');

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
  contextIsolation: true,
  // WebView kullanımını aç ve cross-origin erişimi kolaylaştır
  webviewTag: true,
  webSecurity: false,
  // Clear cache on startup to avoid old bundle issues
  clearCache: true,
    },
  });
  // SPA için file:// protokolüyle yükle (production2 lokal)
  const reactIndex = path.join(__dirname, '../react_ui/dist/index.html');
  const entry = fs.existsSync(reactIndex) ? reactIndex : reactIndex;
  console.log('[Electron] Loading UI from:', entry);
  win.loadURL(
    url.format({
      pathname: entry,
      protocol: 'file:',
      slashes: true,
    })
  );
  win.webContents.openDevTools();
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
