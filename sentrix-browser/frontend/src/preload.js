const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to renderer process
contextBridge.exposeInMainWorld('sentrixAPI', {
    // Token management
    getToken: () => ipcRenderer.invoke('get-token'),
    
    // Backend health check
    checkBackendHealth: () => ipcRenderer.invoke('check-backend-health'),
    
    // Task management
    createTask: (objective, scheduledAt) => 
        ipcRenderer.invoke('create-task', { objective, scheduledAt }),
    
    getTask: (taskId) => ipcRenderer.invoke('get-task', taskId),
    
    // Chat interface
    chatWithAgent: (message, url) => 
        ipcRenderer.invoke('chat-with-agent', { message, url }),
    
    // Immediate execution
    executeImmediate: (objective, url) => 
        ipcRenderer.invoke('execute-immediate', { objective, url })
});
