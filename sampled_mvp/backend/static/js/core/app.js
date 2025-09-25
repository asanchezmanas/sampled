// backend/static/js/core/app.js

class MABApp {
    constructor(options = {}) {
        this.options = {
            baseUrl: '',
            debug: false,
            ...options
        };
        
        // Core managers
        this.state = new StateManager(this.options.initialData || {});
        this.api = new APIClient({
            baseUrl: this.options.baseUrl,
            csrfToken: this.options.csrfToken
        });
        this.utils = new Utils();
        
        // UI state
        this.ui = {
            sidebarExpanded: false,
            mobileMenuOpen: false,
            activeDropdown: null
        };
        
        // Component registry
        this.components = new Map();
        this.eventListeners = new Map();
        
        // Initialize
        this.init();
    }
    
    init() {
        this.log('Initializing MAB System...');
        
        // Setup core functionality
        this.setupEventListeners();
        this.initializeSidebar();
        this.initializeDropdowns();
        this.initializeLiveMetrics();
        
        // Auto-initialize components
        this.initializeComponents();
        
        // Setup responsive behavior
        this.setupResponsive();
        
        this.log('MAB System initialized successfully');
    }
    
    // ===== CORE EVENT HANDLING =====
    
    setupEventListeners() {
        // Global click handler
        document.addEventListener('click', this.handleGlobalClick.bind(this));
        
        // Global form submission
        document.addEventListener('submit', this.handleGlobalSubmit.bind(this));
        
        // Global keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
        
        // Custom events
        document.addEventListener('experiment:created', this.handleExperimentCreated.bind(this));
        document.addEventListener('experiment:updated', this.handleExperimentUpdated.bind(this));
        document.addEventListener('stats:updated', this.handleStatsUpdated.bind(this));
    }
    
    handleGlobalClick(event) {
        // Close dropdowns when clicking outside
        if (this.ui.activeDropdown && !event.target.closest('[data-component="dropdown"]')) {
            this.closeAllDropdowns();
        }
        
        // Handle button clicks with data-action
        const button = event.target.closest('[data-action]');
        if (button) {
            event.preventDefault();
            const action = button.dataset.action;
            const target = button.dataset.target;
            
            this.handleAction(action, target, button);
        }
    }
    
    handleGlobalSubmit(event) {
        const form = event.target;
        const action = form.dataset.action;
        
        if (action) {
            event.preventDefault();
            this.handleFormSubmission(form, action);
        }
    }
    
    handleKeyboardShortcuts(event) {
        // Cmd/Ctrl + K for search
        if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
            event.preventDefault();
            this.focusSearch();
        }
        
        // Escape to close modals/dropdowns
        if (event.key === 'Escape') {
            this.closeAllDropdowns();
            this.closeAllModals();
        }
    }
    
    // ===== UI MANAGEMENT =====
    
    initializeSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar) return;
        
        // Handle hover expansion (desktop)
        sidebar.addEventListener('mouseenter', () => {
            if (window.innerWidth >= 1024) {
                this.expandSidebar();
            }
        });
        
        sidebar.addEventListener('mouseleave', () => {
            if (window.innerWidth >= 1024) {
                this.collapseSidebar();
            }
        });
    }
    
    expandSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.add('expanded');
        }
    }
    
    collapseSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.remove('expanded');
        }
    }
    
    toggleMobileSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar) return;
        
        this.ui.mobileMenuOpen = !this.ui.mobileMenuOpen;
        
        if (this.ui.mobileMenuOpen) {
            sidebar.classList.add('mobile-open');
        } else {
            sidebar.classList.remove('mobile-open');
        }
    }
    
    initializeDropdowns() {
        // No need for complex initialization with vanilla JS
        // Everything is handled in the global click handler
    }
    
    toggleUserMenu() {
        const menu = document.getElementById('user-menu');
        if (!menu) return;
        
        const isOpen = !menu.classList.contains('hidden');
        
        this.closeAllDropdowns();
        
        if (!isOpen) {
            menu.classList.remove('hidden');
            this.ui.activeDropdown = 'user-menu';
        }
    }
    
    toggleNotifications() {
        // Placeholder for notifications
        this.showToast('Notifications feature coming soon!', 'info');
    }
    
    closeAllDropdowns() {
        const dropdowns = document.querySelectorAll('[id$="-menu"]');
        dropdowns.forEach(dropdown => {
            dropdown.classList.add('hidden');
        });
        this.ui.activeDropdown = null;
    }
    
    closeAllModals() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.classList.add('hidden');
        });
    }
    
    // ===== COMPONENT MANAGEMENT =====
    
    initializeComponents() {
        // Auto-initialize components with data-component attribute
        document.querySelectorAll('[data-component]').forEach(element => {
            const componentType = element.dataset.component;
            this.initComponent(componentType, element);
        });
        
        // Initialize live metrics
        document.querySelectorAll('[data-live-metric]').forEach(element => {
            const metricName = element.dataset.liveMetric;
            this.registerLiveMetric(metricName, element);
        });
    }
    
    initComponent(type, element) {
        const componentId = element.id || this.utils.generateId(type);
        
        try {
            let component;
            
            switch (type) {
                case 'chart':
                    component = new ChartComponent(element, this);
                    break;
                case 'table':
                    component = new TableComponent(element, this);
                    break;
                case 'modal':
                    component = new ModalComponent(element, this);
                    break;
                case 'form':
                    component = new FormComponent(element, this);
                    break;
                default:
                    this.log(`Unknown component type: ${type}`);
                    return;
            }
            
            this.components.set(componentId, component);
            element.setAttribute('data-component-id', componentId);
            
            this.log(`Initialized component: ${type} (${componentId})`);
            
        } catch (error) {
            this.error(`Failed to initialize component ${type}:`, error);
        }
    }
    
    getComponent(id) {
        return this.components.get(id);
    }
    
    // ===== LIVE METRICS =====
    
    initializeLiveMetrics() {
        if (!this.options.user) return;
        
        // Start periodic updates for live metrics
        this.liveMetricsInterval = setInterval(() => {
            this.updateLiveMetrics();
        }, 30000); // Every 30 seconds
    }
    
    registerLiveMetric(metricName, element) {
        if (!this.liveMetrics) {
            this.liveMetrics = new Map();
        }
        
        const metrics = this.liveMetrics.get(metricName) || [];
        metrics.push(element);
        this.liveMetrics.set(metricName, metrics);
    }
    
    async updateLiveMetrics() {
        if (!this.liveMetrics || this.liveMetrics.size === 0) return;
        
        try {
            const metricNames = Array.from(this.liveMetrics.keys());
            const response = await this.api.get('/api/metrics/live', {
                metrics: metricNames.join(',')
            });
            
            if (response.success) {
                this.updateMetricElements(response.data);
            }
            
        } catch (error) {
            this.error('Failed to update live metrics:', error);
        }
    }
    
    updateMetricElements(metricsData) {
        for (const [metricName, elements] of this.liveMetrics.entries()) {
            const value = metricsData[metricName];
            if (value !== undefined) {
                elements.forEach(element => {
                    this.animateValueChange(element, value);
                });
            }
        }
    }
    
    animateValueChange(element, newValue) {
        const currentValue = element.textContent;
        
        if (currentValue !== String(newValue)) {
            element.style.transition = 'all 0.3s ease';
            element.style.transform = 'scale(1.05)';
            element.textContent = newValue;
            
            setTimeout(() => {
                element.style.transform = 'scale(1)';
            }, 300);
        }
    }
    
    // ===== ACTIONS & FORMS =====
    
    handleAction(action, target, element) {
        this.log(`Handling action: ${action} (target: ${target})`);
        
        switch (action) {
            case 'create-experiment':
                this.createExperiment();
                break;
            case 'start-experiment':
                this.startExperiment(target);
                break;
            case 'pause-experiment':
                this.pauseExperiment(target);
                break;
            case 'view-experiment':
                this.viewExperiment(target);
                break;
            case 'delete-experiment':
                this.deleteExperiment(target);
                break;
            case 'logout':
                this.logout();
                break;
            default:
                this.log(`Unknown action: ${action}`);
        }
    }
    
    async handleFormSubmission(form, action) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        this.showLoading(true);
        
        try {
            let response;
            
            switch (action) {
                case 'login':
                    response = await this.api.post('/api/auth/login', data);
                    if (response.success) {
                        this.handleLoginSuccess(response.data);
                    }
                    break;
                    
                case 'register':
                    response = await this.api.post('/api/auth/register', data);
                    if (response.success) {
                        this.handleLoginSuccess(response.data);
                    }
                    break;
                    
                case 'create-experiment':
                    response = await this.api.post('/api/experiments', data);
                    if (response.success) {
                        this.handleExperimentCreated(response.data);
                    }
                    break;
                    
                default:
                    this.error(`Unknown form action: ${action}`);
            }
            
        } catch (error) {
            this.handleAPIError(error);
        } finally {
            this.showLoading(false);
        }
    }
    
    // ===== EXPERIMENT MANAGEMENT =====
    
    createExperiment() {
        // Navigate to experiment creation page or show modal
        window.location.href = '/experiments/new';
    }
    
    async startExperiment(experimentId) {
        if (!experimentId) return;
        
        try {
            this.showLoading(true);
            const response = await this.api.post(`/api/experiments/${experimentId}/start`);
            
            if (response.success) {
                this.showToast('Experiment started successfully!', 'success');
                this.refreshExperimentData(experimentId);
            }
            
        } catch (error) {
            this.handleAPIError(error);
        } finally {
            this.showLoading(false);
        }
    }
    
    async pauseExperiment(experimentId) {
        if (!experimentId) return;
        
        try {
            this.showLoading(true);
            const response = await this.api.post(`/api/experiments/${experimentId}/pause`);
            
            if (response.success) {
                this.showToast('Experiment paused successfully!', 'success');
                this.refreshExperimentData(experimentId);
            }
            
        } catch (error) {
            this.handleAPIError(error);
        } finally {
            this.showLoading(false);
        }
    }
    
    viewExperiment(experimentId) {
        if (!experimentId) return;
        window.location.href = `/experiment/${experimentId}`;
    }
    
    async deleteExperiment(experimentId) {
        if (!experimentId) return;
        
        if (!confirm('Are you sure you want to delete this experiment? This action cannot be undone.')) {
            return;
        }
        
        try {
            this.showLoading(true);
            const response = await this.api.delete(`/api/experiments/${experimentId}`);
            
            if (response.success) {
                this.showToast('Experiment deleted successfully!', 'success');
                // Remove experiment from DOM
                const experimentCard = document.querySelector(`[data-experiment-id="${experimentId}"]`);
                if (experimentCard) {
                    experimentCard.remove();
                }
            }
            
        } catch (error) {
            this.handleAPIError(error);
        } finally {
            this.showLoading(false);
        }
    }
    
    async refreshExperimentData(experimentId) {
        try {
            const response = await this.api.get(`/api/experiments/${experimentId}`);
            
            if (response.success) {
                // Update experiment card in DOM
                this.updateExperimentCard(experimentId, response.data);
                
                // Trigger update event
                document.dispatchEvent(new CustomEvent('experiment:updated', {
                    detail: { experiment: response.data }
                }));
            }
            
        } catch (error) {
            this.error('Failed to refresh experiment data:', error);
        }
    }
    
    updateExperimentCard(experimentId, experimentData) {
        const card = document.querySelector(`[data-experiment-id="${experimentId}"]`);
        if (!card) return;
        
        // Update status badge
        const statusBadge = card.querySelector('.badge');
        if (statusBadge) {
            statusBadge.className = `badge badge-${experimentData.status}`;
            statusBadge.textContent = experimentData.status.charAt(0).toUpperCase() + experimentData.status.slice(1);
        }
        
        // Update metrics if they exist
        const metricsElements = card.querySelectorAll('[data-live-metric]');
        metricsElements.forEach(element => {
            const metric = element.dataset.liveMetric;
            if (experimentData[metric] !== undefined) {
                this.animateValueChange(element, experimentData[metric]);
            }
        });
    }
    
    // ===== AUTH MANAGEMENT =====
    
    handleLoginSuccess(data) {
        // Store token
        localStorage.setItem('mab_token', data.token);
        
        // Redirect to dashboard
        window.location.href = '/';
    }
    
    async logout() {
        if (!confirm('Are you sure you want to sign out?')) {
            return;
        }
        
        // Clear token
        localStorage.removeItem('mab_token');
        
        // Redirect to login
        window.location.href = '/login';
    }
    
    // ===== EVENT HANDLERS =====
    
    handleExperimentCreated(event) {
        const experiment = event.detail?.experiment;
        if (experiment) {
            this.showToast('Experiment created successfully!', 'success');
            this.state.addExperiment(experiment);
        }
    }
    
    handleExperimentUpdated(event) {
        const experiment = event.detail?.experiment;
        if (experiment) {
            this.state.updateExperiment(experiment.id, experiment);
        }
    }
    
    handleStatsUpdated(event) {
        const stats = event.detail?.stats;
        if (stats) {
            this.state.updateStats(stats);
        }
    }
    
    // ===== UI UTILITIES =====
    
    showLoading(show = true) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            if (show) {
                overlay.classList.remove('hidden');
            } else {
                overlay.classList.add('hidden');
            }
        }
    }
    
    showToast(message, type = 'info') {
        // Create toast element if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'fixed top-4 right-4 z-50 space-y-2';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} bg-white border border-gray-200 rounded-lg shadow-lg p-4 min-w-80 transform transition-all duration-300 translate-x-full`;
        
        const typeConfig = {
            success: {
                icon: `<svg class="w-5 h-5 text-success-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                       </svg>`,
                color: 'success'
            },
            error: {
                icon: `<svg class="w-5 h-5 text-error-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                       </svg>`,
                color: 'error'
            },
            warning: {
                icon: `<svg class="w-5 h-5 text-warning-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                       </svg>`,
                color: 'warning'
            },
            info: {
                icon: `<svg class="w-5 h-5 text-brand-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                       </svg>`,
                color: 'brand'
            }
        };
        
        const config = typeConfig[type] || typeConfig.info;
        
        toast.innerHTML = `
            <div class="flex items-start gap-3">
                <div class="flex-shrink-0">
                    ${config.icon}
                </div>
                <div class="flex-1">
                    <p class="text-sm font-medium text-gray-900">${message}</p>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="flex-shrink-0 text-gray-400 hover:text-gray-600">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 10);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, 300);
        }, 5000);
    }
    
    focusSearch() {
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // ===== RESPONSIVE DESIGN =====
    
    setupResponsive() {
        const mediaQuery = window.matchMedia('(max-width: 1024px)');
        
        const handleMediaChange = (e) => {
            const toggleButton = document.querySelector('.sidebar-toggle');
            
            if (e.matches) {
                // Mobile view
                if (toggleButton) {
                    toggleButton.classList.remove('hidden');
                }
                this.collapseSidebar();
            } else {
                // Desktop view
                if (toggleButton) {
                    toggleButton.classList.add('hidden');
                }
                // Close mobile menu if open
                if (this.ui.mobileMenuOpen) {
                    this.toggleMobileSidebar();
                }
            }
        };
        
        // Initial check
        handleMediaChange(mediaQuery);
        
        // Listen for changes
        mediaQuery.addListener(handleMediaChange);
    }
    
    // ===== ERROR HANDLING =====
    
    handleAPIError(error) {
        this.error('API Error:', error);
        
        let message = 'An error occurred. Please try again.';
        
        if (error.response) {
            // HTTP error response
            if (error.response.status === 401) {
                message = 'Please sign in to continue.';
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            } else if (error.response.data?.detail) {
                message = error.response.data.detail;
            } else {
                message = `Error ${error.response.status}: ${error.response.statusText}`;
            }
        } else if (error.message) {
            message = error.message;
        }
        
        this.showToast(message, 'error');
    }
    
    // ===== UTILITY METHODS =====
    
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
    
    formatPercentage(value, decimals = 1) {
        return (value * 100).toFixed(decimals) + '%';
    }
    
    formatCurrency(value, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(value);
    }
    
    formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        };
        
        return new Intl.DateTimeFormat('en-US', { ...defaultOptions, ...options }).format(new Date(date));
    }
    
    formatTimeAgo(date) {
        const now = new Date();
        const then = new Date(date);
        const diffInSeconds = Math.floor((now - then) / 1000);
        
        if (diffInSeconds < 60) {
            return 'just now';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else {
            const days = Math.floor(diffInSeconds / 86400);
            return `${days} day${days > 1 ? 's' : ''} ago`;
        }
    }
    
    // ===== DEBUGGING & LOGGING =====
    
    log(...args) {
        if (this.options.debug || window.location.hostname === 'localhost') {
            console.log('[MAB]', ...args);
        }
    }
    
    error(...args) {
        console.error('[MAB]', ...args);
    }
    
    // ===== PUBLIC API =====
    
    // Methods exposed for templates and external scripts
    
    // Refresh data for current page
    async refresh() {
        const currentPage = this.options.currentPage;
        
        if (currentPage === '/') {
            await this.refreshDashboard();
        } else if (currentPage.startsWith('/experiment/')) {
            const experimentId = currentPage.split('/')[2];
            await this.refreshExperimentData(experimentId);
        }
    }
    
    async refreshDashboard() {
        try {
            this.showLoading(true);
            
            const response = await this.api.get('/api/dashboard');
            if (response.success) {
                this.state.setData(response.data);
                
                // Trigger refresh event
                document.dispatchEvent(new CustomEvent('dashboard:refreshed', {
                    detail: { data: response.data }
                }));
            }
            
        } catch (error) {
            this.handleAPIError(error);
        } finally {
            this.showLoading(false);
        }
    }
    
    // Get current state
    getState(key) {
        return this.state.get(key);
    }
    
    // Update state
    setState(key, value) {
        return this.state.set(key, value);
    }
    
    // Clean up resources
    destroy() {
        // Clear intervals
        if (this.liveMetricsInterval) {
            clearInterval(this.liveMetricsInterval);
        }
        
        // Destroy components
        this.components.forEach(component => {
            if (component.destroy) {
                component.destroy();
            }
        });
        
        // Clear event listeners
        this.eventListeners.forEach(listener => {
            document.removeEventListener(listener.type, listener.handler);
        });
        
        this.log('MAB System destroyed');
    }
}

// Make MABApp available globally
window.MABApp = MABApp;
