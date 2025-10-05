// backend/static/js/core/app.js
// Versión consolidada con auto-optimización inteligente

class MABApp {
    constructor(options = {}) {
        this.options = {
            baseUrl: '',
            debug: false,
            autoOptimize: true,  // Auto-detectar cuándo optimizar
            batchSize: 10,
            updateInterval: 30000,
            retryAttempts: 3,
            ...options
        };
        
        // Detectar si necesitamos optimizaciones
        this.shouldOptimize = this.detectOptimizationNeeds();
        
        // Core managers
        this.state = this.shouldOptimize 
            ? new StateManagerOptimized(this.options.initialData || {})
            : new StateManager(this.options.initialData || {});
            
        this.api = new APIClient({
            baseUrl: this.options.baseUrl,
            csrfToken: this.options.csrfToken
        });
        
        this.utils = new Utils();
        this.eventBus = new EventBus();
        
        // Performance monitoring (solo si optimizamos)
        if (this.shouldOptimize) {
            this.performanceMetrics = new PerformanceMonitor();
        }
        
        // UI state
        this.ui = {
            sidebarExpanded: false,
            mobileMenuOpen: false,
            activeDropdown: null
        };
        
        // Component registry
        this.components = new Map();
        this.componentObserver = null;
        
        // Batch operations (solo si optimizamos)
        if (this.shouldOptimize) {
            this.pendingUpdates = new Map();
            this.updateScheduled = false;
        }
        
        // Initialize
        this.init();
    }
    
    // ===== AUTO-OPTIMIZATION DETECTION =====
    
    detectOptimizationNeeds() {
        if (!this.options.autoOptimize) return false;
        
        // Optimizar si:
        // 1. Hay muchos experimentos (>10)
        // 2. Hay muchos componentes en la página (>20)
        // 3. Dispositivo móvil de gama baja
        // 4. Performance API indica CPU lenta
        
        const experimentCount = document.querySelectorAll('[data-experiment-id]').length;
        const componentCount = document.querySelectorAll('[data-component]').length;
        const isMobile = /Android|webOS|iPhone|iPad/i.test(navigator.userAgent);
        
        // Detectar CPU lenta (aproximado)
        const slowCPU = navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 2;
        
        const needsOptimization = 
            experimentCount > 10 || 
            componentCount > 20 || 
            (isMobile && slowCPU);
        
        if (needsOptimization && this.options.debug) {
            console.log('[MAB] Auto-optimization enabled:', {
                experimentCount,
                componentCount,
                isMobile,
                slowCPU
            });
        }
        
        return needsOptimization;
    }
    
    // ===== INITIALIZATION =====
    
    async init() {
        const initStart = this.shouldOptimize ? performance.now() : null;
        this.log('Initializing MAB System...');
        
        try {
            if (this.shouldOptimize) {
                // Optimized initialization
                await this.setupCriticalSystems();
                this.deferNonCriticalInit();
                
                const initTime = performance.now() - initStart;
                this.performanceMetrics?.record('initialization', initTime);
                this.log(`MAB System initialized in ${initTime.toFixed(2)}ms`);
            } else {
                // Simple initialization
                this.setupEventListeners();
                this.initializeSidebar();
                this.initializeDropdowns();
                this.initializeComponents();
                this.initializeLiveMetrics();
                this.setupResponsive();
                
                this.log('MAB System initialized successfully');
            }
            
        } catch (error) {
            this.error('Failed to initialize MAB System:', error);
            this.handleInitializationError(error);
        }
    }
    
    async setupCriticalSystems() {
        // Solo lo esencial para First Contentful Paint
        this.setupEventListeners();
        this.initializeSidebar();
        this.setupResponsive();
    }
    
    deferNonCriticalInit() {
        // Usar requestIdleCallback para sistemas no críticos
        const defer = window.requestIdleCallback || ((cb) => setTimeout(cb, 16));
        
        defer(() => {
            this.initializeDropdowns();
            this.initializeComponents();
            this.initializeLiveMetrics();
        });
    }
    
    handleInitializationError(error) {
        // Fallback gracioso
        console.error('Initialization error:', error);
        this.showToast('System initialization failed. Please refresh the page.', 'error');
    }
    
    // ===== CORE EVENT HANDLING =====
    
    setupEventListeners() {
        // Global click handler
        document.addEventListener('click', this.handleGlobalClick.bind(this));
        
        // Global form submission
        document.addEventListener('submit', this.handleGlobalSubmit.bind(this));
        
        // Global keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
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
        // Handled in global click handler
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
        if (this.shouldOptimize) {
            // Lazy loading con Intersection Observer
            this.componentObserver = new IntersectionObserver(
                this.handleComponentIntersection.bind(this),
                { rootMargin: '50px' }
            );
            
            // Observar componentes lazy
            document.querySelectorAll('[data-component][data-lazy="true"]')
                .forEach(el => this.componentObserver.observe(el));
            
            // Inicializar componentes críticos inmediatamente
            document.querySelectorAll('[data-component]:not([data-lazy="true"])')
                .forEach(element => {
                    const componentType = element.dataset.component;
                    this.initComponent(componentType, element);
                });
        } else {
            // Inicialización simple: todos los componentes inmediatamente
            document.querySelectorAll('[data-component]').forEach(element => {
                const componentType = element.dataset.component;
                this.initComponent(componentType, element);
            });
        }
        
        // Live metrics
        document.querySelectorAll('[data-live-metric]').forEach(element => {
            const metricName = element.dataset.liveMetric;
            this.registerLiveMetric(metricName, element);
        });
    }
    
    async handleComponentIntersection(entries) {
        for (const entry of entries) {
            if (entry.isIntersecting) {
                const element = entry.target;
                const componentType = element.dataset.component;
                
                await this.initComponent(componentType, element);
                this.componentObserver.unobserve(element);
            }
        }
    }
    
    async initComponent(type, element) {
        const componentId = element.id || this.utils.generateId(type);
        
        // Evitar doble inicialización
        if (this.components.has(componentId)) {
            return this.components.get(componentId);
        }
        
        try {
            let ComponentClass;
            
            // Map component types to classes
            switch (type) {
                case 'chart':
                    ComponentClass = window.ChartComponent;
                    break;
                case 'table':
                    ComponentClass = window.TableComponent;
                    break;
                case 'modal':
                    ComponentClass = window.ModalComponent;
                    break;
                case 'form':
                    ComponentClass = window.FormComponent;
                    break;
                default:
                    this.log(`Unknown component type: ${type}`);
                    return null;
            }
            
            if (!ComponentClass) {
                this.log(`Component class not found: ${type}`);
                return null;
            }
            
            const component = new ComponentClass(element, this);
            await component.init?.();
            
            this.components.set(componentId, component);
            element.setAttribute('data-component-id', componentId);
            
            this.eventBus.emit('component:initialized', { type, id: componentId });
            this.log(`Initialized component: ${type} (${componentId})`);
            
            return component;
            
        } catch (error) {
            this.error(`Failed to initialize component ${type}:`, error);
            return null;
        }
    }
    
    getComponent(id) {
        return this.components.get(id);
    }
    
    // ===== LIVE METRICS =====
    
    initializeLiveMetrics() {
        if (!this.options.user) return;
        
        if (this.shouldOptimize) {
            // Versión optimizada con retry y backoff
            this.liveMetricsManager = new LiveMetricsManager(this.api, {
                interval: this.options.updateInterval,
                retryAttempts: this.options.retryAttempts,
                backoffMultiplier: 2
            });
            
            this.liveMetricsManager.onUpdate = (metrics) => {
                this.batchUpdateMetrics(metrics);
            };
            
            this.liveMetricsManager.start();
        } else {
            // Versión simple con interval básico
            this.liveMetricsInterval = setInterval(() => {
                this.updateLiveMetrics();
            }, 30000);
        }
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
    
    // Batch updates (optimized version)
    batchUpdateMetrics(metrics) {
        if (!this.shouldOptimize) {
            // Simple version
            this.updateMetricElements(metrics);
            return;
        }
        
        // Batch version
        Object.entries(metrics).forEach(([key, value]) => {
            this.pendingUpdates.set(key, value);
        });
        
        this.scheduleUpdate();
    }
    
    scheduleUpdate() {
        if (this.updateScheduled) return;
        
        this.updateScheduled = true;
        requestAnimationFrame(() => {
            this.flushMetricUpdates();
            this.updateScheduled = false;
        });
    }
    
    flushMetricUpdates() {
        const updates = Array.from(this.pendingUpdates.entries());
        this.pendingUpdates.clear();
        
        updates.forEach(([metricName, value]) => {
            const elements = document.querySelectorAll(`[data-live-metric="${metricName}"]`);
            elements.forEach(element => {
                this.animateValueChange(element, value);
            });
        });
    }
    
    animateValueChange(element, newValue) {
        const currentValue = element.textContent;
        
        if (currentValue !== String(newValue)) {
            // Usar Web Animations API si está disponible y estamos optimizando
            if (this.shouldOptimize && element.animate) {
                element.animate([
                    { transform: 'scale(1)', opacity: 1 },
                    { transform: 'scale(1.05)', opacity: 0.8 },
                    { transform: 'scale(1)', opacity: 1 }
                ], {
                    duration: 300,
                    easing: 'ease-out'
                });
            } else {
                // Fallback simple
                element.style.transition = 'all 0.3s ease';
                element.style.transform = 'scale(1.05)';
                setTimeout(() => {
                    element.style.transform = 'scale(1)';
                }, 300);
            }
            
            element.textContent = newValue;
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
        
        // Optimistic UI updates (solo si optimizamos)
        if (this.shouldOptimize) {
            const optimisticUpdate = this.getOptimisticUpdate(action, data);
            if (optimisticUpdate) {
                this.state.batchSet?.(optimisticUpdate) || this.state.setData(optimisticUpdate);
            }
        }
        
        this.showLoading(true);
        
        try {
            const response = await this.executeFormAction(action, data);
            
            if (response.success) {
                this.handleFormSuccess(action, response.data);
            }
            
        } catch (error) {
            // Revert optimistic updates on error (solo si optimizamos)
            if (this.shouldOptimize && optimisticUpdate) {
                this.revertOptimisticUpdate(optimisticUpdate);
            }
            this.handleAPIError(error);
        } finally {
            this.showLoading(false);
        }
    }
    
    async executeFormAction(action, data) {
        switch (action) {
            case 'login':
                return await this.api.post('/api/auth/login', data);
                
            case 'register':
                return await this.api.post('/api/auth/register', data);
                
            case 'create-experiment':
                return await this.api.post('/api/experiments', data);
                
            default:
                throw new Error(`Unknown form action: ${action}`);
        }
    }
    
    handleFormSuccess(action, data) {
        switch (action) {
            case 'login':
            case 'register':
                this.handleLoginSuccess(data);
                break;
                
            case 'create-experiment':
                this.showToast('Experiment created successfully!', 'success');
                this.state.addExperiment?.(data) || this.refresh();
                break;
        }
    }
    
    getOptimisticUpdate(action, data) {
        // Solo para versión optimizada
        switch (action) {
            case 'create-experiment':
                return {
                    'stats.active_tests': (this.state.get('stats.active_tests') || 0) + 1
                };
            case 'login':
                return {
                    'user.authenticating': true
                };
            default:
                return null;
        }
    }
    
    revertOptimisticUpdate(update) {
        // Revert logic para versión optimizada
        Object.keys(update).forEach(key => {
            const history = this.state.getHistory?.(1);
            if (history && history.length > 0) {
                const previousValue = history[0].oldValue;
                this.state.set(key, previousValue);
            }
        });
    }
    
    // ===== EXPERIMENT MANAGEMENT =====
    
    createExperiment() {
        window.location.href = '/experiments/new';
    }
    
    async startExperiment(experimentId) {
        if (!experimentId) return;
        
        try {
            this.showLoading(true);
            const response = await this.api.post(`/api/experiments/${experimentId}/start`);
            
            if (response.success) {
                this.showToast('Experiment started successfully!', 'success');
                await this.refreshExperimentData(experimentId);
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
                await this.refreshExperimentData(experimentId);
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
                this.updateExperimentCard(experimentId, response.data);
                
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
        
        const statusBadge = card.querySelector('.badge');
        if (statusBadge) {
            statusBadge.className = `badge badge-${experimentData.status}`;
            statusBadge.textContent = experimentData.status.charAt(0).toUpperCase() + experimentData.status.slice(1);
        }
        
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
        localStorage.setItem('mab_token', data.token);
        window.location.href = '/';
    }
    
    async logout() {
        if (!confirm('Are you sure you want to sign out?')) {
            return;
        }
        
        localStorage.removeItem('mab_token');
        window.location.href = '/login';
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
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'fixed top-4 right-4 z-50 space-y-2';
            document.body.appendChild(toastContainer);
        }
        
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
        
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 10);
        
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
                if (toggleButton) {
                    toggleButton.classList.remove('hidden');
                }
                this.collapseSidebar();
            } else {
                if (toggleButton) {
                    toggleButton.classList.add('hidden');
                }
                if (this.ui.mobileMenuOpen) {
                    this.toggleMobileSidebar();
                }
            }
        };
        
        handleMediaChange(mediaQuery);
        mediaQuery.addListener(handleMediaChange);
    }
    
    // ===== ERROR HANDLING =====
    
    handleAPIError(error) {
        this.error('API Error:', error);
        
        let message = 'An error occurred. Please try again.';
        
        if (error.response) {
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
    
    // ===== PERFORMANCE MONITORING (solo si optimizamos) =====
    
    measureOperation(name, operation) {
        if (!this.shouldOptimize) {
            return operation();
        }
        
        const start = performance.now();
        const result = operation();
        const end = performance.now();
        
        this.performanceMetrics.record(name, end - start);
        
        if (this.options.debug && (end - start) > 100) {
            this.log(`Slow operation detected: ${name} took ${(end - start).toFixed(2)}ms`);
        }
        
        return result;
    }
    
    async measureAsyncOperation(name, asyncOperation) {
        if (!this.shouldOptimize) {
            return await asyncOperation();
        }
        
        const start = performance.now();
        const result = await asyncOperation();
        const end = performance.now();
        
        this.performanceMetrics.record(name, end - start);
        return result;
    }
    
    // ===== PUBLIC API =====
    
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
    
    getState(key) {
        return this.state.get(key);
    }
    
    setState(key, value) {
        if (typeof key === 'object' && this.shouldOptimize) {
            this.state.batchSet?.(key) || this.state.setData(key);
        } else {
            this.state.set(key, value);
        }
        return this;
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
    
    // ===== CLEANUP =====
    
    destroy() {
        // Clear intervals
        if (this.liveMetricsInterval) {
            clearInterval(this.liveMetricsInterval);
        }
        
        // Destroy optimized manager
        if (this.liveMetricsManager) {
            this.liveMetricsManager.destroy();
        }
        
        // Disconnect observers
        if (this.componentObserver) {
            this.componentObserver.disconnect();
        }
        
        // Destroy components
        this.components.forEach(component => {
            if (component.destroy) {
                component.destroy();
            }
        });
        this.components.clear();
        
        // Clear event bus
        this.eventBus?.removeAllListeners();
        
        // Clear pending operations
        if (this.pendingUpdates) {
            this.pendingUpdates.clear();
        }
        
        // Clear state
        this.state.clear();
        
        this.log('MAB System destroyed');
    }
}

// ===== STATE MANAGER OPTIMIZADO =====

class StateManagerOptimized extends StateManager {
    constructor(initialData = {}) {
        super(initialData);
        
        // Batch updates
        this.batchUpdates = new Map();
        this.batchTimeout = null;
        this.batchDelay = 16; // 1 frame
    }
    
    batchSet(updates) {
        Object.entries(updates).forEach(([key, value]) => {
            this.batchUpdates.set(key, value);
        });
        
        this.scheduleBatchFlush();
        return this;
    }
    
    scheduleBatchFlush() {
        if (this.batchTimeout) return;
        
        this.batchTimeout = setTimeout(() => {
            this.flushBatchUpdates();
        }, this.batchDelay);
    }
    
    flushBatchUpdates() {
        const updates = Array.from(this.batchUpdates.entries());
        this.batchUpdates.clear();
        this.batchTimeout = null;
        
        const oldValues = {};
        
        updates.forEach(([key, value]) => {
            oldValues[key] = this.get(key);
            this.setNestedValue(this.data, key, value);
            this.addToHistory(key, oldValues[key], value);
        });
        
        updates.forEach(([key, value]) => {
            this.notifyListeners(key, value, oldValues[key]);
        });
    }
    
    clear() {
        if (this.batchTimeout) {
            clearTimeout(this.batchTimeout);
            this.batchTimeout = null;
        }
        this.batchUpdates.clear();
        
        return super.clear();
    }
}

// ===== LIVE METRICS MANAGER (para versión optimizada) =====

class LiveMetricsManager {
    constructor(api, options = {}) {
        this.api = api;
        this.options = {
            interval: 30000,
            retryAttempts: 3,
            backoffMultiplier: 2,
            maxBackoff: 300000,
            ...options
        };
        
        this.isRunning = false;
        this.retryCount = 0;
        this.currentInterval = this.options.interval;
        this.timeoutId = null;
        this.onUpdate = null;
        this.onError = null;
    }
    
    start() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.scheduleNext(1000);
    }
    
    stop() {
        this.isRunning = false;
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
            this.timeoutId = null;
        }
    }
    
    async updateMetrics() {
        if (!this.isRunning) return;
        
        try {
            const metrics = document.querySelectorAll('[data-live-metric]');
            if (metrics.length === 0) return;
            
            const metricNames = Array.from(metrics).map(el => el.dataset.liveMetric);
            const uniqueMetrics = [...new Set(metricNames)];
            
            const response = await this.api.get('/api/metrics/live', {
                metrics: uniqueMetrics.join(',')
            });
            
            if (response.success && this.onUpdate) {
                this.onUpdate(response.data);
            }
            
            this.retryCount = 0;
            this.currentInterval = this.options.interval;
            
        } catch (error) {
            this.handleError(error);
        }
        
        if (this.isRunning) {
            this.scheduleNext(this.currentInterval);
        }
    }
    
    handleError(error) {
        this.retryCount++;
        
        if (this.retryCount <= this.options.retryAttempts) {
            this.currentInterval = Math.min(
                this.options.interval * Math.pow(this.options.backoffMultiplier, this.retryCount),
                this.options.maxBackoff
            );
        } else {
            this.stop();
            if (this.onError) {
                this.onError(error);
            }
            return;
        }
    }
    
    scheduleNext(delay) {
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
        }
        
        this.timeoutId = setTimeout(() => {
            this.updateMetrics();
        }, delay);
    }
    
    destroy() {
        this.stop();
        this.onUpdate = null;
        this.onError = null;
    }
}

// ===== EVENT BUS =====

class EventBus {
    constructor() {
        this.events = new Map();
    }
    
    on(event, callback) {
        if (!this.events.has(event)) {
            this.events.set(event, []);
        }
        
        const listener = { 
            callback, 
            id: Math.random().toString(36).substr(2, 9)
        };
        
        this.events.get(event).push(listener);
        
        return () => this.off(event, listener.id);
    }
    
    off(event, listenerId) {
        const listeners = this.events.get(event);
        if (!listeners) return false;
        
        const index = listeners.findIndex(l => l.id === listenerId);
        if (index !== -1) {
            listeners.splice(index, 1);
            return true;
        }
        return false;
    }
    
    emit(event, data) {
        const listeners = this.events.get(event) || [];
        
        listeners.forEach(({ callback }) => {
            try {
                callback(data);
            } catch (error) {
                console.error(`Error in event handler for ${event}:`, error);
            }
        });
    }
    
    removeAllListeners() {
        this.events.clear();
    }
}

// ===== PERFORMANCE MONITOR (para versión optimizada) =====

class PerformanceMonitor {
    constructor() {
        this.metrics = new Map();
        this.errors = [];
        this.startTime = performance.now();
    }
    
    record(name, value) {
        if (!this.metrics.has(name)) {
            this.metrics.set(name, []);
        }
        
        this.metrics.get(name).push({
            value,
            timestamp: performance.now()
        });
        
        const values = this.metrics.get(name);
        if (values.length > 100) {
            values.shift();
        }
    }
    
    recordError(error) {
        this.errors.push({
            error: error.message || error,
            timestamp: performance.now(),
            stack: error.stack
        });
        
        if (this.errors.length > 50) {
            this.errors.shift();
        }
    }
    
    getMetrics() {
        const summary = {};
        
        this.metrics.forEach((values, name) => {
            const numValues = values.map(v => v.value);
            summary[name] = {
                count: numValues.length,
                avg: numValues.reduce((a, b) => a + b, 0) / numValues.length,
                min: Math.min(...numValues),
                max: Math.max(...numValues),
                last: numValues[numValues.length - 1]
            };
        });
        
        return {
            summary,
            uptime: performance.now() - this.startTime,
            errorCount: this.errors.length
        };
    }
}

// ===== GLOBAL INITIALIZATION =====

// Make MABApp available globally
window.MABApp = MABApp;

// Auto-initialize if config is present
if (typeof window !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        const config = document.getElementById('page-config');
        const initialData = document.getElementById('initial-data');
        
        if (config) {
            const configData = JSON.parse(config.textContent);
            
            window.MAB = new MABApp({
                initialData: initialData ? JSON.parse(initialData.textContent) : {},
                user: configData.user,
                csrfToken: configData.csrfToken || '',
                currentPage: configData.page || window.location.pathname,
                baseUrl: configData.baseUrl || '',
                debug: configData.debug || false
            });
            
            // Expose to console for debugging
            if (window.MAB.options.debug) {
                console.log('[MAB] System initialized and available as window.MAB');
                console.log('[MAB] Optimization mode:', window.MAB.shouldOptimize ? 'ENABLED' : 'DISABLED');
            }
        }
    });
}
