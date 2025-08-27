const { app, BrowserWindow } = require('electron');
const path = require('path');
const url = require('url');

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
    },
  });
  // SPA için file:// protokolüyle yükle
  win.loadURL(
    url.format({
      pathname: path.join(__dirname, '../react_ui/dist/index.html'),
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
