// Task Management Dashboard JavaScript

class TaskDashboard {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000/api';
        this.wsUrl = 'ws://localhost:8000/ws/tasks';
        this.token = localStorage.getItem('access_token');
        this.currentUser = null;
        this.websocket = null;
        this.userId = null;
        
        this.init();
    }
    
    init() {
        this.checkAuth();
        this.setupEventListeners();
    }
    
    checkAuth() {
        if (this.token) {
            this.getCurrentUser();
        }
    }
    
    setupEventListeners() {
        // Add any global event listeners here
        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.target.id === 'task-title') {
                this.createTask();
            }
        });
    }
    
    async login() {
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        
        if (!email || !password) {
            this.showMessage('Please enter email and password', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
            });
            
            if (response.ok) {
                const data = await response.json();
                this.token = data.access_token;
                localStorage.setItem('access_token', this.token);
                await this.getCurrentUser();
                this.showMessage('Login successful!', 'success');
            } else {
                const error = await response.json();
                this.showMessage(error.detail || 'Login failed', 'error');
            }
        } catch (error) {
            this.showMessage('Network error: ' + error.message, 'error');
        }
    }
    
    async getCurrentUser() {
        if (!this.token) return;
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
            
            if (response.ok) {
                this.currentUser = await response.json();
                this.userId = this.currentUser.id;
                this.showUserInfo();
                this.loadTasks();
                this.connectWebSocket();
            } else {
                this.logout();
            }
        } catch (error) {
            console.error('Error getting current user:', error);
            this.logout();
        }
    }
    
    showUserInfo() {
        document.getElementById('login-form').style.display = 'none';
        document.getElementById('user-info').style.display = 'flex';
        document.getElementById('user-name').textContent = this.currentUser.username;
    }
    
    logout() {
        this.token = null;
        this.currentUser = null;
        this.userId = null;
        localStorage.removeItem('access_token');
        document.getElementById('login-form').style.display = 'flex';
        document.getElementById('user-info').style.display = 'none';
        document.getElementById('tasks-list').innerHTML = '';
        this.disconnectWebSocket();
    }
    
    async loadTasks() {
        if (!this.token) return;
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/tasks/`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
            
            if (response.ok) {
                const tasks = await response.json();
                this.displayTasks(tasks);
            } else {
                this.showMessage('Failed to load tasks', 'error');
            }
        } catch (error) {
            this.showMessage('Error loading tasks: ' + error.message, 'error');
        }
    }
    
    async createTask() {
        if (!this.token) return;
        
        const title = document.getElementById('task-title').value;
        const description = document.getElementById('task-description').value;
        const priority = document.getElementById('task-priority').value;
        
        if (!title.trim()) {
            this.showMessage('Please enter a task title', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/tasks/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify({
                    title: title.trim(),
                    description: description.trim(),
                    priority: priority
                })
            });
            
            if (response.ok) {
                const task = await response.json();
                this.showMessage('Task created successfully!', 'success');
                this.clearTaskForm();
                this.loadTasks(); // Reload tasks to show the new one
            } else {
                const error = await response.json();
                this.showMessage(error.detail || 'Failed to create task', 'error');
            }
        } catch (error) {
            this.showMessage('Error creating task: ' + error.message, 'error');
        }
    }
    
    async updateTask(taskId, updates) {
        if (!this.token) return;
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/tasks/${taskId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify(updates)
            });
            
            if (response.ok) {
                this.loadTasks(); // Reload tasks to show updates
            } else {
                const error = await response.json();
                this.showMessage(error.detail || 'Failed to update task', 'error');
            }
        } catch (error) {
            this.showMessage('Error updating task: ' + error.message, 'error');
        }
    }
    
    async deleteTask(taskId) {
        if (!this.token) return;
        
        if (!confirm('Are you sure you want to delete this task?')) {
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/tasks/${taskId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
            
            if (response.ok) {
                this.showMessage('Task deleted successfully!', 'success');
                this.loadTasks(); // Reload tasks
            } else {
                const error = await response.json();
                this.showMessage(error.detail || 'Failed to delete task', 'error');
            }
        } catch (error) {
            this.showMessage('Error deleting task: ' + error.message, 'error');
        }
    }
    
    displayTasks(tasks) {
        const tasksList = document.getElementById('tasks-list');
        
        if (tasks.length === 0) {
            tasksList.innerHTML = '<p style="text-align: center; color: #718096; padding: 20px;">No tasks found. Create your first task!</p>';
            return;
        }
        
        tasksList.innerHTML = tasks.map(task => `
            <div class="task-item ${task.status} ${task.priority}-priority">
                <div class="task-header">
                    <div class="task-title">${this.escapeHtml(task.title)}</div>
                    <div class="task-actions">
                        ${task.status !== 'completed' ? 
                            `<button class="btn-complete" onclick="dashboard.updateTask('${task.id}', {status: 'completed'})">Complete</button>` : 
                            `<button class="btn-edit" onclick="dashboard.updateTask('${task.id}', {status: 'pending'})">Reopen</button>`
                        }
                        <button class="btn-edit" onclick="dashboard.editTask('${task.id}')">Edit</button>
                        <button class="btn-delete" onclick="dashboard.deleteTask('${task.id}')">Delete</button>
                    </div>
                </div>
                ${task.description ? `<div class="task-description">${this.escapeHtml(task.description)}</div>` : ''}
                <div class="task-meta">
                    <span class="task-status status-${task.status}">${task.status}</span>
                    <span class="task-priority priority-${task.priority}">${task.priority}</span>
                    <span>Created: ${new Date(task.created_at).toLocaleDateString()}</span>
                </div>
            </div>
        `).join('');
    }
    
    editTask(taskId) {
        // Simple edit functionality - in a real app, you'd have a proper edit form
        const newTitle = prompt('Enter new title:');
        if (newTitle && newTitle.trim()) {
            this.updateTask(taskId, { title: newTitle.trim() });
        }
    }
    
    clearTaskForm() {
        document.getElementById('task-title').value = '';
        document.getElementById('task-description').value = '';
        document.getElementById('task-priority').value = 'medium';
    }
    
    connectWebSocket() {
        if (!this.userId || this.websocket) return;
        
        this.websocket = new WebSocket(`${this.wsUrl}/${this.userId}`);
        
        this.websocket.onopen = () => {
            this.updateWebSocketStatus('connected');
            this.showMessage('Connected to real-time updates', 'success');
            
            // Send subscription message
            this.websocket.send(JSON.stringify({
                type: 'subscribe',
                user_id: this.userId
            }));
        };
        
        this.websocket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleWebSocketMessage(message);
        };
        
        this.websocket.onclose = () => {
            this.updateWebSocketStatus('disconnected');
            this.showMessage('Disconnected from real-time updates', 'error');
            this.websocket = null;
            
            // Try to reconnect after 3 seconds
            setTimeout(() => {
                if (this.userId) {
                    this.connectWebSocket();
                }
            }, 3000);
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showMessage('WebSocket connection error', 'error');
        };
    }
    
    disconnectWebSocket() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        this.updateWebSocketStatus('disconnected');
    }
    
    handleWebSocketMessage(message) {
        console.log('WebSocket message:', message);
        
        switch (message.type) {
            case 'task_created':
            case 'task_updated':
            case 'task_deleted':
                this.showMessage(`Task ${message.type.replace('task_', '')}`, 'success');
                this.loadTasks(); // Reload tasks to show updates
                break;
            case 'status_update':
                this.showMessage(message.data.message, 'success');
                break;
            case 'pong':
                // Handle pong response
                break;
            default:
                console.log('Unknown message type:', message.type);
        }
    }
    
    updateWebSocketStatus(status) {
        const statusElement = document.getElementById('ws-status');
        statusElement.textContent = status === 'connected' ? 'Connected' : 'Disconnected';
        statusElement.className = `status-indicator ${status}`;
    }
    
    showMessage(message, type = 'info') {
        const messagesContainer = document.getElementById('ws-messages');
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;
        messageElement.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
        
        messagesContainer.appendChild(messageElement);
        
        // Keep only last 10 messages
        while (messagesContainer.children.length > 10) {
            messagesContainer.removeChild(messagesContainer.firstChild);
        }
        
        // Auto-scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global functions for HTML onclick handlers
function login() {
    dashboard.login();
}

function logout() {
    dashboard.logout();
}

function createTask() {
    dashboard.createTask();
}

// Initialize dashboard when page loads
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new TaskDashboard();
});
