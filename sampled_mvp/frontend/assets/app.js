// frontend/assets/app.js
class MABDashboard {
    constructor() {
        this.apiClient = new APIClient();
        this.experiments = [];
        this.filteredExperiments = [];
        this.currentFilter = '';
        
        this.init();
    }
    
    async init() {
        // Check authentication
        if (!this.apiClient.token) {
            window.location.href = '/login';
            return;
        }
        
        // Load dashboard data
        await this.loadDashboard();
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    async loadDashboard() {
        try {
            this.showLoading(true);
            
            // Load experiments
            this.experiments = await this.apiClient.getExperiments();
            this.filteredExperiments = [...this.experiments];
            
            // Update UI
            this.renderStats();
            this.renderExperimentsList();
            
            this.showDashboard();
            
        } catch (error) {
            console.error('Dashboard load failed:', error);
            this.showError();
        }
    }
    
    renderStats() {
        const stats = this.calculateStats(this.experiments);
        
        document.getElementById('active-experiments').textContent = stats.activeCount;
        document.getElementById('total-users').textContent = stats.totalUsers.toLocaleString();
        document.getElementById('avg-conversion').textContent = (stats.avgConversion * 100).toFixed(1);
        document.getElementById('revenue-impact').textContent = this.formatCurrency(stats.revenueImpact);
        
        // Set user name (from token)
        const userInfo = this.apiClient.getUserInfo();
        if (userInfo?.name) {
            document.getElementById('user-name').textContent = userInfo.name;
        }
    }
    
    calculateStats(experiments) {
        const active = experiments.filter(exp => exp.status === 'active');
        const totalUsers = experiments.reduce((sum, exp) => sum + (exp.total_users || 0), 0);
        const totalConversions = experiments.reduce((sum, exp) => {
            return sum + Math.round((exp.total_users || 0) * (exp.conversion_rate || 0));
        }, 0);
        
        const avgConversion = totalUsers > 0 ? totalConversions / totalUsers : 0;
        
        // Estimated revenue impact (simplified calculation)
        const avgOrderValue = 50; // Placeholder
        const revenueImpact = totalConversions * avgOrderValue * 0.1; // 10% improvement assumption
        
        return {
            activeCount: active.length,
            totalUsers,
            avgConversion,
            revenueImpact
        };
    }
    
    renderExperimentsList() {
        const container = document.getElementById('experiments-list');
        
        if (this.filteredExperiments.length === 0) {
            container.innerHTML = `
                <div class="p-8 text-center">
                    <div class="text-gray-400 mb-4">
                        <svg class="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                        </svg>
                    </div>
                    <p class="text-lg text-gray-600 mb-2">No experiments found</p>
                    <p class="text-sm text-gray-500 mb-4">
                        ${this.currentFilter ? 'Try changing the filter or' : ''} Create your first A/B test to get started
                    </p>
                    <button onclick="dashboard.createNewExperiment()" 
                            class="px-6 py-2 bg-primary text-white rounded-md hover:bg-secondary transition-colors">
                        Create Experiment
                    </button>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.filteredExperiments.map(exp => `
            <div class="experiment-item px-6 py-4 hover:bg-gray-50 border-b border-gray-200 cursor-pointer" 
                 onclick="dashboard.viewExperiment('${exp.id}')">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <div class="flex items-center space-x-3 mb-2">
                            <h3 class="text-base font-medium text-gray-900">${this.escapeHtml(exp.name)}</h3>
                            ${this.renderStatusBadge(exp.status)}
                        </div>
                        
                        <p class="text-sm text-gray-600 mb-3">${this.escapeHtml(exp.description || 'No description')}</p>
                        
                        <div class="flex items-center space-x-6 text-sm text-gray-500">
                            <span class="flex items-center">
                                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                                </svg>
                                ${this.formatDate(exp.created_at)}
                            </span>
                            <span class="flex items-center">
                                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.196-2.121M9 20h8v-2a3 3 0 00-5.196-2.121m1.196 2.121a3 3 0 002-2.829V12a3 3 0 00-3-3H9a3 3 0 00-3 3v3.17a3 3 0 002 2.83"/>
                                </svg>
                                ${(exp.total_users || 0).toLocaleString()} users
                            </span>
                            <span class="flex items-center">
                                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                                </svg>
                                ${exp.arms_count || 0} variants
                            </span>
                        </div>
                    </div>
                    
                    <div class="text-right ml-4">
                        <div class="text-2xl font-bold text-gray-900 mb-1">
                            ${((exp.conversion_rate || 0) * 100).toFixed(1)}%
                        </div>
                        <div class="text-xs text-gray-500">conversion rate</div>
                        
                        <div class="mt-3 flex space-x-2">
                            ${this.renderExperimentActions(exp)}
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    renderStatusBadge(status) {
        const styles = {
            'draft': 'bg-gray-100 text-gray-800',
            'active': 'bg-green-100 text-green-800',
            'paused': 'bg-yellow-100 text-yellow-800',
            'completed': 'bg-blue-100 text-blue-800'
        };
        
        return `<span class="px-2 py-1 text-xs rounded-full ${styles[status] || styles.draft}">${status}</span>`;
    }
    
    renderExperimentActions(exp) {
        const actions = [];
        
        if (exp.status === 'draft') {
            actions.push(`<button onclick="event.stopPropagation(); dashboard.startExperiment('${exp.id}')" 
                                 class="text-xs px-2 py-1 bg-green-600 text-white rounded hover:bg-green-700">Start</button>`);
        }
        
        if (exp.status === 'active') {
            actions.push(`<button onclick="event.stopPropagation(); dashboard.pauseExperiment('${exp.id}')" 
                                 class="text-xs px-2 py-1 bg-yellow-600 text-white rounded hover:bg-yellow-700">Pause</button>`);
        }
        
        actions.push(`<button onclick="event.stopPropagation(); dashboard.viewAnalytics('${exp.id}')" 
                             class="text-xs px-2 py-1 bg-primary text-white rounded hover:bg-secondary">View</button>`);
        
        return actions.join('');
    }
    
    setupEventListeners() {
        // Create experiment form
        const createForm = document.getElementById('create-form');
        if (createForm) {
            createForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleCreateExperiment();
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'n':
                        e.preventDefault();
                        this.createNewExperiment();
                        break;
                    case 'r':
                        e.preventDefault();
                        this.refreshExperiments();
                        break;
                }
            }
            
            // Escape key closes modals
            if (e.key === 'Escape') {
                this.closeCreateModal();
            }
        });
    }
    
    // Modal Management
    createNewExperiment() {
        document.getElementById('create-modal').classList.remove('hidden');
        document.getElementById('experiment-name').focus();
    }
    
    closeCreateModal() {
        document.getElementById('create-modal').classList.add('hidden');
        document.getElementById('create-form').reset();
        this.resetVariants();
    }
    
    resetVariants() {
        const container = document.getElementById('variants-container');
        container.innerHTML = `
            <div class="variant-item mb-3 p-3 border border-gray-200 rounded-md">
                <input type="text" class="variant-name w-full px-3 py-2 border border-gray-300 rounded-md mb-2" 
                       placeholder="Variant A (Control)" required>
                <textarea class="variant-content w-full px-3 py-2 border border-gray-300 rounded-md" 
                          rows="2" placeholder="Content or description..."></textarea>
            </div>
            
            <div class="variant-item mb-3 p-3 border border-gray-200 rounded-md">
                <input type="text" class="variant-name w-full px-3 py-2 border border-gray-300 rounded-md mb-2" 
                       placeholder="Variant B" required>
                <textarea class="variant-content w-full px-3 py-2 border border-gray-300 rounded-md" 
                          rows="2" placeholder="Content or description..."></textarea>
            </div>
        `;
    }
    
    addVariant() {
        const container = document.getElementById('variants-container');
        const variantCount = container.children.length;
        const variantLetter = String.fromCharCode(65 + variantCount); // A, B, C, etc.
        
        if (variantCount >= 5) {
            this.showMessage('Maximum 5 variants allowed', 'warning');
            return;
        }
        
        const variantDiv = document.createElement('div');
        variantDiv.className = 'variant-item mb-3 p-3 border border-gray-200 rounded-md';
        variantDiv.innerHTML = `
            <div class="flex justify-between items-center mb-2">
                <input type="text" class="variant-name flex-1 px-3 py-2 border border-gray-300 rounded-md" 
                       placeholder="Variant ${variantLetter}" required>
                <button type="button" onclick="this.parentElement.parentElement.remove()" 
                        class="ml-2 text-red-600 hover:text-red-800">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
            <textarea class="variant-content w-full px-3 py-2 border border-gray-300 rounded-md" 
                      rows="2" placeholder="Content or description..."></textarea>
        `;
        
        container.appendChild(variantDiv);
    }
    
    async handleCreateExperiment() {
        try {
            const form = document.getElementById('create-form');
            const formData = new FormData(form);
            
            // Collect form data
            const name = document.getElementById('experiment-name').value.trim();
            const description = document.getElementById('experiment-description').value.trim();
            
            // Collect variants
            const variants = [];
            const variantItems = document.querySelectorAll('.variant-item');
            
            variantItems.forEach((item, index) => {
                const nameInput = item.querySelector('.variant-name');
                const contentInput = item.querySelector('.variant-content');
                
                if (nameInput && nameInput.value.trim()) {
                    variants.push({
                        name: nameInput.value.trim(),
                        description: contentInput ? contentInput.value.trim() : '',
                        content: {
                            text: contentInput ? contentInput.value.trim() : '',
                            index: index
                        }
                    });
                }
            });
            
            if (variants.length < 2) {
                this.showMessage('At least 2 variants are required', 'error');
                return;
            }
            
            if (!name) {
                this.showMessage('Experiment name is required', 'error');
                return;
            }
            
            // Show loading state
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating...';
            
            // Create experiment
            const experimentData = {
                name,
                description,
                arms: variants,
                config: {
                    auto_pause: false,
                    confidence_threshold: 0.95,
                    min_sample_size: 100
                }
            };
            
            const response = await this.apiClient.createExperiment(experimentData);
            
            this.showMessage('Experiment created successfully!', 'success');
            this.closeCreateModal();
            
            // Refresh experiments list
            await this.loadDashboard();
            
            // Navigate to experiment details
            setTimeout(() => {
                this.viewExperiment(response.experiment_id);
            }, 1000);
            
        } catch (error) {
            console.error('Create experiment failed:', error);
            this.showMessage(error.message || 'Failed to create experiment', 'error');
        } finally {
            // Reset button state
            const submitBtn = document.querySelector('#create-form button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Create Experiment';
            }
        }
    }
    
    // Experiment Actions
    async startExperiment(experimentId) {
        if (!confirm('Are you sure you want to start this experiment?')) return;
        
        try {
            await this.apiClient.startExperiment(experimentId);
            this.showMessage('Experiment started successfully!', 'success');
            await this.loadDashboard();
        } catch (error) {
            this.showMessage(error.message || 'Failed to start experiment', 'error');
        }
    }
    
    async pauseExperiment(experimentId) {
        if (!confirm('Are you sure you want to pause this experiment?')) return;
        
        try {
            await this.apiClient.pauseExperiment(experimentId);
            this.showMessage('Experiment paused successfully!', 'success');
            await this.loadDashboard();
        } catch (error) {
            this.showMessage(error.message || 'Failed to pause experiment', 'error');
        }
    }
    
    viewExperiment(experimentId) {
        window.location.href = `/experiment?id=${experimentId}`;
    }
    
    viewAnalytics(experimentId) {
        window.location.href = `/analytics?id=${experimentId}`;
    }
    
    // Filtering
    filterExperiments() {
        const filterValue = document.getElementById('status-filter').value;
        this.currentFilter = filterValue;
        
        if (!filterValue) {
            this.filteredExperiments = [...this.experiments];
        } else {
            this.filteredExperiments = this.experiments.filter(exp => exp.status === filterValue);
        }
        
        this.renderExperimentsList();
    }
    
    async refreshExperiments() {
        await this.loadDashboard();
        this.showMessage('Experiments refreshed', 'info');
    }
    
    // UI State Management
    showLoading(show = true) {
        document.getElementById('loading').classList.toggle('hidden', !show);
        document.getElementById('dashboard-content').classList.toggle('hidden', show);
        document.getElementById('error-state').classList.add('hidden');
    }
    
    showDashboard() {
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('dashboard-content').classList.remove('hidden');
        document.getElementById('error-state').classList.add('hidden');
    }
    
    showError() {
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('dashboard-content').classList.add('hidden');
        document.getElementById('error-state').classList.remove('hidden');
    }
    
    showMessage(message, type = 'info', duration = 3000) {
        // Create message element if it doesn't exist
        let messageEl = document.getElementById('toast-message');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.id = 'toast-message';
            messageEl.className = 'fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-all duration-300';
            document.body.appendChild(messageEl);
        }
        
        // Set message content and style
        const styles = {
            'success': 'bg-green-500 text-white',
            'error': 'bg-red-500 text-white',
            'warning': 'bg-yellow-500 text-white',
            'info': 'bg-blue-500 text-white'
        };
        
        messageEl.textContent = message;
        messageEl.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-all duration-300 ${styles[type] || styles.info}`;
        
        // Show message
        messageEl.style.transform = 'translateX(0)';
        
        // Auto hide
        setTimeout(() => {
            messageEl.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (messageEl.parentNode) {
                    messageEl.parentNode.removeChild(messageEl);
                }
            }, 300);
        }, duration);
    }
    
    // Utility Methods
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text ? text.replace(/[&<>"']/g, m => map[m]) : '';
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffDays < 30) return `${Math.ceil(diffDays / 7)} weeks ago`;
        
        return date.toLocaleDateString();
    }
    
    formatCurrency(amount) {
        if (amount === 0) return '$0';
        if (amount < 1000) return `${Math.round(amount)}`;
        if (amount < 1000000) return `${(amount / 1000).toFixed(1)}k`;
        return `${(amount / 1000000).toFixed(1)}m`;
    }
    
    logout() {
        if (confirm('Are you sure you want to logout?')) {
            this.apiClient.logout();
            window.location.href = '/login';
        }
    }
}

// API Client Class
class APIClient {
    constructor() {
        this.baseURL = '/api';
        this.token = localStorage.getItem('mab_token');
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...(this.token && { 'Authorization': `Bearer ${this.token}` })
            },
            ...options
        };
        
        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }
        
        const response = await fetch(url, config);
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        
        return response.json();
    }
    
    getUserInfo() {
        if (!this.token) return null;
        try {
            const payload = JSON.parse(atob(this.token.split('.')[1]));
            return payload;
        } catch {
            return null;
        }
    }
    
    logout() {
        localStorage.removeItem('mab_token');
        this.token = null;
    }
    
    // API Methods
    async getExperiments() {
        return this.request('/experiments');
    }
    
    async createExperiment(data) {
        return this.request('/experiments', {
            method: 'POST',
            body: data
        });
    }
    
    async getExperiment(experimentId) {
        return this.request(`/experiments/${experimentId}`);
    }
    
    async startExperiment(experimentId) {
        return this.request(`/experiments/${experimentId}/start`, {
            method: 'POST'
        });
    }
    
    async pauseExperiment(experimentId) {
        return this.request(`/experiments/${experimentId}/pause`, {
            method: 'POST'
        });
    }
    
    async getAnalytics(experimentId) {
        return this.request(`/experiments/${experimentId}/analytics`);
    }
}

// Global functions for inline event handlers
let dashboard;

function createNewExperiment() {
    dashboard.createNewExperiment();
}

function closeCreateModal() {
    dashboard.closeCreateModal();
}

function addVariant() {
    dashboard.addVariant();
}

function filterExperiments() {
    dashboard.filterExperiments();
}

function refreshExperiments() {
    dashboard.refreshExperiments();
}

function logout() {
    dashboard.logout();
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new MABDashboard();
});

// frontend/assets/auth.js
class AuthManager {
    constructor() {
        this.apiURL = '/api/auth';
        this.init();
    }
    
    init() {
        // Check if already logged in
        const token = localStorage.getItem('mab_token');
        if (token && this.isValidToken(token)) {
            window.location.href = '/';
            return;
        }
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Enter key handling
        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const activeTab = document.querySelector('.tab-button.border-primary');
                if (activeTab && activeTab.id === 'login-tab') {
                    this.handleLogin();
                } else {
                    this.handleRegister();
                }
            }
        });
    }
    
    isValidToken(token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.exp > Date.now() / 1000;
        } catch {
            return false;
        }
    }
    
    switchTab(tab) {
        // Update tab buttons
        document.getElementById('login-tab').classList.remove('border-primary', 'text-primary');
        document.getElementById('login-tab').classList.add('border-transparent', 'text-gray-500');
        document.getElementById('register-tab').classList.remove('border-primary', 'text-primary');
        document.getElementById('register-tab').classList.add('border-transparent', 'text-gray-500');
        
        // Show active tab
        if (tab === 'login') {
            document.getElementById('login-tab').classList.remove('border-transparent', 'text-gray-500');
            document.getElementById('login-tab').classList.add('border-primary', 'text-primary');
            document.getElementById('login-form').classList.remove('hidden');
            document.getElementById('register-form').classList.add('hidden');
            document.getElementById('login-email').focus();
        } else {
            document.getElementById('register-tab').classList.remove('border-transparent', 'text-gray-500');
            document.getElementById('register-tab').classList.add('border-primary', 'text-primary');
            document.getElementById('register-form').classList.remove('hidden');
            document.getElementById('login-form').classList.add('hidden');
            document.getElementById('register-name').focus();
        }
        
        this.hideMessage();
    }
    
    async handleLogin() {
        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;
        
        if (!email || !password) {
            this.showMessage('Please fill in all fields', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${this.apiURL}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }
            
            const data = await response.json();
            localStorage.setItem('mab_token', data.token);
            
            this.showMessage('Login successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
            
        } catch (error) {
            this.showMessage(error.message, 'error');
        }
    }
    
    async handleRegister() {
        const name = document.getElementById('register-name').value.trim();
        const email = document.getElementById('register-email').value.trim();
        const password = document.getElementById('register-password').value;
        
        if (!name || !email || !password) {
            this.showMessage('Please fill in all fields', 'error');
            return;
        }
        
        if (password.length < 8) {
            this.showMessage('Password must be at least 8 characters', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${this.apiURL}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Registration failed');
            }
            
            const data = await response.json();
            localStorage.setItem('mab_token', data.token);
            
            this.showMessage('Registration successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
            
        } catch (error) {
            this.showMessage(error.message, 'error');
        }
    }
    
    showMessage(message, type) {
        const messageEl = document.getElementById('message');
        const styles = {
            'success': 'bg-green-50 border-green-200 text-green-800',
            'error': 'bg-red-50 border-red-200 text-red-800',
            'warning': 'bg-yellow-50 border-yellow-200 text-yellow-800'
        };
        
        messageEl.textContent = message;
        messageEl.className = `p-4 rounded-md text-center border ${styles[type] || styles.error}`;
        messageEl.classList.remove('hidden');
    }
    
    hideMessage() {
        document.getElementById('message').classList.add('hidden');
    }
}

// Global functions
function switchTab(tab) {
    authManager.switchTab(tab);
}

function handleLogin() {
    authManager.handleLogin();
}

function handleRegister() {
    authManager.handleRegister();
}

// Initialize
let authManager;
document.addEventListener('DOMContentLoaded', () => {
    authManager = new AuthManager();
});