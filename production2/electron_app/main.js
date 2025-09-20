const { app, BrowserWindow, ipcMain } = require('electron');
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
  // Enable preload script for IPC
  preload: path.join(__dirname, 'preload.js'),
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
  
  // Store window reference for PDF download handling
  global.mainWindow = win;
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

// PDF download handling state
let pdfDownloadHandler = null;
let pdfDownloadResolve = null;
let pdfDownloadTimeout = null;

// Setup PDF download interception
ipcMain.handle('setup-pdf-download', async (event, config) => {
  try {
    const { targetDir, timeout = 10000 } = config;
    
    console.log('PDF-DOWNLOAD: Setting up handler for directory:', targetDir);
    
    // Ensure target directory exists
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }
    
    // Get the webContents from the main window
    const mainWindow = global.mainWindow;
    if (!mainWindow) {
      throw new Error('Main window not available');
    }
    
    const webContents = mainWindow.webContents;
    
    // Remove any existing handler
    if (pdfDownloadHandler) {
      webContents.session.removeListener('will-download', pdfDownloadHandler);
    }
    
    // Setup new download handler
    pdfDownloadHandler = (event, item, webContents) => {
      const filename = item.getFilename();
      console.log('PDF-DOWNLOAD: Intercepted download:', filename);
      
      // Check if it's a PDF
      if (filename.toLowerCase().endsWith('.pdf') || item.getMimeType() === 'application/pdf') {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const savedFilename = `police-${timestamp}.pdf`;
        const savePath = path.join(targetDir, savedFilename);
        
        console.log('PDF-DOWNLOAD: Saving to:', savePath);
        item.setSavePath(savePath);
        
        item.on('updated', (event, state) => {
          if (state === 'interrupted') {
            console.log('PDF-DOWNLOAD: Download interrupted');
            if (pdfDownloadResolve) {
              pdfDownloadResolve({ ok: false, error: 'download_interrupted' });
              pdfDownloadResolve = null;
            }
          }
        });
        
        item.once('done', (event, state) => {
          if (state === 'completed') {
            console.log('PDF-DOWNLOAD: Download completed:', savePath);
            if (pdfDownloadResolve) {
              pdfDownloadResolve({ ok: true, path: savePath, filename: savedFilename });
              pdfDownloadResolve = null;
            }
          } else {
            console.log('PDF-DOWNLOAD: Download failed:', state);
            if (pdfDownloadResolve) {
              pdfDownloadResolve({ ok: false, error: `download_${state}` });
              pdfDownloadResolve = null;
            }
          }
        });
      } else {
        console.log('PDF-DOWNLOAD: Non-PDF download ignored:', filename);
      }
    };
    
    // Register the handler
    webContents.session.on('will-download', pdfDownloadHandler);
    
    console.log('PDF-DOWNLOAD: Handler setup complete');
    return { ok: true, targetDir };
    
  } catch (error) {
    console.error('PDF-DOWNLOAD: Setup failed:', error);
    return { ok: false, error: String(error) };
  }
});

// Wait for PDF download completion
ipcMain.handle('wait-pdf-download', async (event, config) => {
  const { timeoutMs = 15000 } = config;
  
  return new Promise((resolve) => {
    // Store resolve function for the download handler
    pdfDownloadResolve = resolve;
    
    // Setup timeout
    pdfDownloadTimeout = setTimeout(() => {
      if (pdfDownloadResolve === resolve) {
        console.log('PDF-DOWNLOAD: Timeout waiting for download');
        pdfDownloadResolve = null;
        resolve({ ok: false, error: 'timeout' });
      }
    }, timeoutMs);
  });
});

// Cleanup PDF download handler
ipcMain.handle('cleanup-pdf-download', async (event) => {
  try {
    console.log('PDF-DOWNLOAD: Cleaning up handler');
    
    const mainWindow = global.mainWindow;
    if (mainWindow && pdfDownloadHandler) {
      mainWindow.webContents.session.removeListener('will-download', pdfDownloadHandler);
      pdfDownloadHandler = null;
    }
    
    if (pdfDownloadTimeout) {
      clearTimeout(pdfDownloadTimeout);
      pdfDownloadTimeout = null;
    }
    
    if (pdfDownloadResolve) {
      pdfDownloadResolve({ ok: false, error: 'cleanup' });
      pdfDownloadResolve = null;
    }
    
    console.log('PDF-DOWNLOAD: Cleanup complete');
    return { ok: true };
    
  } catch (error) {
    console.error('PDF-DOWNLOAD: Cleanup failed:', error);
    return { ok: false, error: String(error) };
  }
});
