// Sentrix Browser - Frontend Renderer Script

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const currentUrlInput = document.getElementById('current-url');
const taskList = document.getElementById('task-list');
const taskModal = document.getElementById('task-modal');
const backendStatus = document.getElementById('backend-status');

// Navigation
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Update active state
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Show corresponding view
        const viewName = btn.dataset.view;
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        document.getElementById(`${viewName}-view`).classList.add('active');
    });
});

// Check backend health on load
async function checkBackendHealth() {
    try {
        const result = await window.sentrixAPI.checkBackendHealth();
        if (result.success) {
            backendStatus.classList.add('connected');
            backendStatus.classList.remove('disconnected');
            backendStatus.querySelector('.text').textContent = 'Connected';
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        backendStatus.classList.add('disconnected');
        backendStatus.classList.remove('connected');
        backendStatus.querySelector('.text').textContent = 'Disconnected';
        console.error('Backend connection failed:', error);
    }
}

// Chat functionality
async function sendMessage() {
    const message = chatInput.value.trim();
    const url = currentUrlInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    chatInput.value = '';
    
    // Show loading indicator
    const loadingId = addMessage('Thinking...', 'system', true);
    
    try {
        const result = await window.sentrixAPI.chatWithAgent(message, url);
        
        // Remove loading message
        removeMessage(loadingId);
        
        if (result.success) {
            addMessage(result.data.response, 'system');
        } else {
            addMessage(`Error: ${result.error}`, 'system');
        }
    } catch (error) {
        removeMessage(loadingId);
        addMessage(`Error: ${error.message}`, 'system');
    }
}

function addMessage(content, type, isLoading = false) {
    const messageId = `msg-${Date.now()}`;
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.id = messageId;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    if (isLoading) {
        contentDiv.style.opacity = '0.6';
        contentDiv.id = `${messageId}-content`;
    }
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageId;
}

function removeMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

// Event listeners for chat
sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Task management
let tasks = [];

async function loadTasks() {
    // In a real implementation, fetch from backend
    renderTasks();
}

function renderTasks() {
    if (tasks.length === 0) {
        taskList.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 40px;">No tasks yet. Create your first task!</p>';
        return;
    }
    
    taskList.innerHTML = tasks.map(task => `
        <div class="task-card">
            <h3>${escapeHtml(task.objective)}</h3>
            <div class="task-meta">
                <span class="task-status ${task.status}">${task.status}</span>
                <span>ID: ${task.id}</span>
                <span>Created: ${new Date(task.created_at).toLocaleString()}</span>
                ${task.scheduled_at ? `<span>Scheduled: ${new Date(task.scheduled_at).toLocaleString()}</span>` : ''}
            </div>
            ${task.result ? `<div style="margin-top: 15px; padding: 15px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; font-size: 13px;">${escapeHtml(task.result)}</div>` : ''}
        </div>
    `).join('');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// New task modal
document.getElementById('new-task-btn').addEventListener('click', () => {
    taskModal.classList.add('active');
});

document.getElementById('cancel-task-btn').addEventListener('click', () => {
    taskModal.classList.remove('active');
    document.getElementById('task-objective').value = '';
    document.getElementById('task-url').value = '';
});

document.getElementById('create-task-btn').addEventListener('click', async () => {
    const objective = document.getElementById('task-objective').value.trim();
    const url = document.getElementById('task-url').value.trim();
    
    if (!objective) {
        alert('Please enter a task objective');
        return;
    }
    
    try {
        const result = await window.sentrixAPI.createTask(objective, null);
        
        if (result.success) {
            tasks.unshift(result.data);
            renderTasks();
            taskModal.classList.remove('active');
            document.getElementById('task-objective').value = '';
            document.getElementById('task-url').value = '';
            
            // Switch to tasks view
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
            document.querySelector('[data-view="tasks"]').classList.add('active');
            document.getElementById('tasks-view').classList.add('active');
        } else {
            alert(`Failed to create task: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
});

// Schedule task
document.getElementById('schedule-task-btn').addEventListener('click', async () => {
    const objective = document.getElementById('schedule-objective').value.trim();
    const scheduledTime = document.getElementById('schedule-time').value;
    const url = document.getElementById('schedule-url').value.trim();
    
    if (!objective || !scheduledTime) {
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        const result = await window.sentrixAPI.createTask(objective, scheduledTime);
        
        if (result.success) {
            tasks.unshift(result.data);
            renderTasks();
            alert('Task scheduled successfully!');
            document.getElementById('schedule-objective').value = '';
            document.getElementById('schedule-time').value = '';
            document.getElementById('schedule-url').value = '';
        } else {
            alert(`Failed to schedule task: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
});

// Settings - Test connection
document.getElementById('test-connection-btn').addEventListener('click', async () => {
    const result = await window.sentrixAPI.checkBackendHealth();
    if (result.success) {
        alert('Connection successful! Backend is running.');
    } else {
        alert(`Connection failed: ${result.error}\n\nMake sure the backend server is running on port 8765.`);
    }
});

// Gmail integration placeholder
document.getElementById('connect-gmail-btn').addEventListener('click', () => {
    alert('Gmail Integration:\n\nTo connect Gmail, you need to:\n1. Set up OAuth2 credentials in Google Cloud Console\n2. Place gmail_credentials.json in ~/.sentrix/\n3. The app will guide you through authentication');
});

// Initialize
checkBackendHealth();
loadTasks();

// Refresh tasks periodically
setInterval(loadTasks, 30000);
