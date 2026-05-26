const { app, BrowserWindow, ipcMain, session } = require('electron');
const path = require('path');
const axios = require('axios');
const fs = require('fs');
const os = require('os');

// Security Configuration
const SENTRIX_HOME = path.join(os.homedir(), '.sentrix');
const TOKEN_FILE = path.join(SENTRIX_HOME, 'execution_token');
const BACKEND_URL = 'http://127.0.0.1:8765';

let mainWindow;
let executionToken = null;

// Load execution token
function loadExecutionToken() {
    try {
        if (fs.existsSync(TOKEN_FILE)) {
            executionToken = fs.readFileSync(TOKEN_FILE, 'utf8').trim();
            return true;
        }
        return false;
    } catch (error) {
        console.error('Failed to load execution token:', error);
        return false;
    }
}

// Create main browser window
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        icon: path.join(__dirname, '../assets/icon.png'),
        titleBarStyle: 'hiddenInset',
        backgroundColor: '#1a1a2e'
    });

    mainWindow.loadFile('index.html');
    
    // Open DevTools in development
    if (process.argv.includes('--dev')) {
        mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// IPC Handlers for secure communication with backend
ipcMain.handle('get-token', async () => {
    return executionToken;
});

ipcMain.handle('check-backend-health', async () => {
    try {
        const response = await axios.get(`${BACKEND_URL}/health`, {
            headers: { 'X-Sentrix-Token': executionToken }
        });
        return { success: true, data: response.data };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

ipcMain.handle('create-task', async (event, { objective, scheduledAt }) => {
    try {
        const response = await axios.post(`${BACKEND_URL}/tasks`, {
            objective,
            scheduled_at: scheduledAt
        }, {
            headers: { 'X-Sentrix-Token': executionToken }
        });
        return { success: true, data: response.data };
    } catch (error) {
        return { success: false, error: error.response?.data || error.message };
    }
});

ipcMain.handle('get-task', async (event, taskId) => {
    try {
        const response = await axios.get(`${BACKEND_URL}/tasks/${taskId}`, {
            headers: { 'X-Sentrix-Token': executionToken }
        });
        return { success: true, data: response.data };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

ipcMain.handle('chat-with-agent', async (event, { message, url }) => {
    try {
        const response = await axios.post(`${BACKEND_URL}/chat`, {
            message,
            url
        }, {
            headers: { 'X-Sentrix-Token': executionToken }
        });
        return { success: true, data: response.data };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

ipcMain.handle('execute-immediate', async (event, { objective, url }) => {
    try {
        const response = await axios.post(`${BACKEND_URL}/execute`, null, {
            params: { objective, url },
            headers: { 'X-Sentrix-Token': executionToken }
        });
        return { success: true, data: response.data };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

// App lifecycle
app.whenReady().then(() => {
    if (!loadExecutionToken()) {
        console.warn('No execution token found. Backend may not be accessible.');
    }
    createWindow();
});

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

// Security: Prevent navigation to external URLs
app.on('web-contents-created', (event, contents) => {
    contents.on('will-navigate', (event, navigationUrl) => {
        const parsedUrl = new URL(navigationUrl);
        // Only allow localhost backend API calls
        if (parsedUrl.hostname !== '127.0.0.1' && parsedUrl.hostname !== 'localhost') {
            event.preventDefault();
        }
    });
});
