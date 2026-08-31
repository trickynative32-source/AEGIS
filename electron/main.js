const { app, BrowserWindow, globalShortcut, ipcMain, Tray, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow = null;
let backendProcess = null;
let tray = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: '#0a0d14',
    title: 'AURA — Adaptive Universal Routine Assistant',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    },
    autoHideMenuBar: true
  });

  // Load the web app URL
  const startUrl = process.env.ELECTRON_START_URL || 'http://127.0.0.1:8000';
  mainWindow.loadURL(startUrl);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  backendProcess = spawn(pythonCmd, ['-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', '8000'], {
    cwd: path.join(__dirname, '..'),
    stdio: 'inherit'
  });

  backendProcess.on('error', (err) => {
    console.error('Failed to spawn backend process:', err);
  });
}

app.whenReady().then(() => {
  // If backend not running externally, start it
  if (!process.env.EXTERNAL_BACKEND) {
    startBackend();
  }

  // Allow backend 1.5s to initialize before loading window
  setTimeout(createWindow, 1500);

  // Global Push-to-Talk Hotkey (Ctrl+Space)
  globalShortcut.register('CommandOrControl+Space', () => {
    if (mainWindow) {
      mainWindow.webContents.send('global-push-to-talk');
      mainWindow.show();
      mainWindow.focus();
    }
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    if (backendProcess) {
      try {
        backendProcess.kill();
      } catch (e) {}
    }
    app.quit();
  }
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
  if (backendProcess) {
    try {
      backendProcess.kill();
    } catch (e) {}
  }
});
