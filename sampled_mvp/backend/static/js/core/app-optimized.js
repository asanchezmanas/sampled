// backend/static/js/core/app-optimized.js

class MABAppOptimized {
    constructor(options = {}) {
        this.options = {
            baseUrl: '',
            debug: false,
            batchSize: 10,
            updateInterval: 30000,
            retryAttempts: 3,
            ...options
        };
        
        // Core managers con lazy loading
        this.state = new StateManagerOptimized(this.options.initialData || {});
        this.api = new APIClient({
            baseUrl: this.options.baseUrl,
            csrfToken: this.options.csrfToken
        });
        this.utils = new Utils();
        this.eventBus = new EventBus();
        
        // Performance monitoring
        this.performanceMetrics = new PerformanceMonitor();
        
        // UI state optimizado
        this.ui = {
            sidebarExpanded: false,
            mobileMenuOpen: false,
            activeDropdown: null
        };
        
        // Module registry para lazy loading
        this.modules = new Map();
        this.moduleLoader = new ModuleLoader();
        
        // Component registry optimizado
        this.components = new Map();
        this.componentObserver = null;
        
        // Batch operations
        this.pendingUpdates = new Map();
        this.updateScheduled = false;
        
        // Initialize con performance tracking
        this.init();
    }
    
    async init() {
        const initStart = performance.now();
        this.log('Initializing MAB System...');
        
        try {
            // Setup core functionality (crítico)
            await this.setupCriticalSystems();
            
            // Non-critical systems con defer
            this.deferNonCriticalInit();
            
            const initTime = performance.now() - initStart;
            this.performanceMetrics.record('initialization', initTime);
            
            this.log(`MAB System initialized in ${initTime.toFixed(2)}ms`);
            
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
        
        // Estado inicial crítico
        await this.loadCriticalState();
    }
    
    deferNonCriticalInit() {
        // Usar requestIdleCallback para sistemas no críticos
        const defer = window.requestIdleCallback || ((cb) => setTimeout(cb, 16));
        
        defer(() => {
            this.initializeDropdowns();
            this.initializeComponents();
            this.startLiveMetrics();
        });
    }
    
    // ===== COMPONENT MANAGEMENT OPTIMIZADO =====
    
    initializeComponents() {
        // Usar Intersection Observer para lazy loading
        this.componentObserver = new IntersectionObserver(
            this.handleComponentIntersection.bind(this),
            { rootMargin: '50px' }
        );
        
        // Observar todos los componentes lazy
        document.querySelectorAll('[data-component][data-lazy="true"]')
            .forEach(el => this.componentObserver.observe(el));
        
        // Inicializar componentes críticos inmediatamente
        document.querySelectorAll('[data-component]:not([data-lazy="true"])')
            .forEach(element => {
                const componentType = element.dataset.component;
                this.initComponent(componentType, element);
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
            // Lazy load del módulo del componente
            const ComponentClass = await this.moduleLoader.loadComponent(type);
            
            if (!ComponentClass) {
                this.log(`Unknown component type: ${type}`);
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
    
    // ===== LIVE METRICS OPTIMIZADO =====
    
    startLiveMetrics() {
        if (!this.options.user) return;
        
        this.liveMetricsManager = new LiveMetricsManager(this.api, {
            interval: this.options.updateInterval,
            retryAttempts: this.options.retryAttempts,
            backoffMultiplier: 2
        });
        
        this.liveMetricsManager.onUpdate = (metrics) => {
            this.batchUpdateMetrics(metrics);
        };
        
        this.liveMetricsManager.start();
    }
    
    batchUpdateMetrics(metrics) {
        // Batch multiple metric updates
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
            // Usar Web Animations API si está disponible
            if (element.animate) {
                element.animate([
                    { transform: 'scale(1)', opacity: 1 },
                    { transform: 'scale(1.05)', opacity: 0.8 },
                    { transform: 'scale(1)', opacity: 1 }
                ], {
                    duration: 300,
                    easing: 'ease-out'
                });
            } else {
                // Fallback para navegadores antiguos
                element.style.transition = 'all 0.3s ease';
                element.style.transform = 'scale(1.05)';
                setTimeout(() => {
                    element.style.transform = 'scale(1)';
                }, 300);
            }
            
            element.textContent = newValue;
        }
    }
    
    // ===== ACTIONS & FORMS OPTIMIZADO =====
    
    async handleFormSubmission(form, action) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Optimistic UI updates
        const optimisticUpdate = this.getOptimisticUpdate(action, data);
        if (optimisticUpdate) {
            this.state.batchSet(optimisticUpdate);
        }
        
        this.showLoading(true);
        
        try {
            const response = await this.executeFormAction(action, data);
            
            if (response.success) {
                this.handleFormSuccess(action, response.data);
            }
            
        } catch (error) {
            // Revert optimistic updates on error
            if (optimisticUpdate) {
                this.revertOptimisticUpdate(optimisticUpdate);
            }
            this.handleAPIError(error);
        } finally {
            this.showLoading(false);
        }
    }
    
    getOptimisticUpdate(action, data) {
        // Definir updates optimistas para mejorar percepción de velocidad
        switch (action) {
            case 'create-experiment':
                return {
                    'stats.active_tests': this.state.get('stats.active_tests', 0) + 1
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
        // Implementar revert logic
        Object.keys(update).forEach(key => {
            // Restore previous values (stored in state history)
            const history = this.state.getHistory(1);
            if (history.length > 0) {
                const previousValue = history[0].oldValue;
                this.state.set(key, previousValue);
            }
        });
    }
    
    // ===== MEMORY MANAGEMENT =====
    
    destroy() {
        // Cleanup detallado para evitar memory leaks
        
        // Clear intervals y timeouts
        if (this.liveMetricsManager) {
            this.liveMetricsManager.destroy();
        }
        
        // Disconnect observers
        if (this.componentObserver) {
            this.componentObserver.disconnect();
        }
        
        // Destroy components con cleanup propio
        this.components.forEach(component => {
            if (component.destroy) {
                component.destroy();
            }
        });
        this.components.clear();
        
        // Clear event bus
        this.eventBus.removeAllListeners();
        
        // Clear pending operations
        this.pendingUpdates.clear();
        if (this.updateScheduled) {
            // No hay forma directa de cancelar requestAnimationFrame sin el ID
            // pero sí podemos marcar que no debe ejecutarse
            this.updateScheduled = false;
        }
        
        // Clear state
        this.state.clear();
        
        this.log('MAB System destroyed and cleaned up');
    }
    
    // ===== PERFORMANCE MONITORING =====
    
    measureOperation(name, operation) {
        const start = performance.now();
        const result = operation();
        const end = performance.now();
        
        this.performanceMetrics.record(name, end - start);
        
        // Log operations lentas en desarrollo
        if (this.options.debug && (end - start) > 100) {
            this.log(`Slow operation detected: ${name} took ${(end - start).toFixed(2)}ms`);
        }
        
        return result;
    }
    
    async measureAsyncOperation(name, asyncOperation) {
        const start = performance.now();
        const result = await asyncOperation();
        const end = performance.now();
        
        this.performanceMetrics.record(name, end - start);
        return result;
    }
    
    // ===== ERROR HANDLING MEJORADO =====
    
    handleAPIError(error) {
        this.error('API Error:', error);
        this.performanceMetrics.recordError(error);
        
        let message = 'An error occurred. Please try again.';
        let shouldRetry = false;
        
        if (error.response) {
            const status = error.response.status;
            
            if (status === 401) {
                message = 'Please sign in to continue.';
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            } else if (status >= 500) {
                message = 'Server error. Retrying automatically...';
                shouldRetry = true;
            } else if (error.response.data?.detail) {
                message = error.response.data.detail;
            } else {
                message = `Error ${status}: ${error.response.statusText}`;
            }
        } else if (error.message) {
            message = error.message;
            shouldRetry = error.name === 'NetworkError';
        }
        
        this.showToast(message, shouldRetry ? 'warning' : 'error');
        
        // Auto-retry para errores de red
        if (shouldRetry) {
            this.scheduleRetry(() => {
                // Re-ejecutar la operación que falló
                this.eventBus.emit('retry:last-operation');
            });
        }
    }
    
    scheduleRetry(retryFn, delay = 2000) {
        setTimeout(retryFn, delay);
    }
    
    // ===== LEGACY COMPATIBILITY =====
    
    legacyAdapter(methodName) {
        // Mapear métodos antiguos a nuevos
        const methodMap = {
            'toggleSidebar': () => this.ui.sidebarExpanded ? this.collapseSidebar() : this.expandSidebar(),
            'refreshData': () => this.refresh(),
            'showModal': (id) => this.getComponent(id)?.show?.(),
        };
        
        return methodMap[methodName] || (() => {
            this.log(`Legacy method ${methodName} not implemented`);
        });
    }
    
    // ===== PUBLIC API OPTIMIZADO =====
    
    async refresh() {
        return this.measureAsyncOperation('refresh', async () => {
            const currentPage = this.options.currentPage;
            
            if (currentPage === '/') {
                await this.refreshDashboard();
            } else if (currentPage.startsWith('/experiment/')) {
                const experimentId = currentPage.split('/')[2];
                await this.refreshExperimentData(experimentId);
            }
        });
    }
    
    // Métodos de estado con batching automático
    getState(key) {
        return this.state.get(key);
    }
    
    setState(key, value) {
        // Auto-batch estado updates
        if (typeof key === 'object') {
            this.state.batchSet(key);
        } else {
            this.state.set(key, value);
        }
        return this;
    }
}

// ===== PERFORMANCE MONITOR =====

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
        
        // Solo mantener las últimas 100 métricas
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
        
        // Solo mantener los últimos 50 errores
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

// ===== LIVE METRICS MANAGER OPTIMIZADO =====

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
        this.scheduleNext(1000); // Primera ejecución rápida
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
            
            // Reset retry state on success
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
            // Exponential backoff
            this.currentInterval = Math.min(
                this.options.interval * Math.pow(this.options.backoffMultiplier, this.retryCount),
                this.options.maxBackoff
            );
        } else {
            // Max retries reached, stop and notify
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

// ===== MODULE LOADER =====

class ModuleLoader {
    constructor() {
        this.modules = new Map();
        this.loading = new Map();
        this.componentMap = {
            'chart': 'ChartComponent',
            'table': 'TableComponent', 
            'modal': 'ModalComponent',
            'form': 'FormComponent',
            'dashboard': 'DashboardModule',
            'analytics': 'AnalyticsModule'
        };
    }
    
    async loadComponent(type) {
        const componentName = this.componentMap[type];
        if (!componentName) {
            return null;
        }
        
        // Check if already loaded
        if (this.modules.has(componentName)) {
            return this.modules.get(componentName);
        }
        
        // Check if currently loading (prevent duplicate requests)
        if (this.loading.has(componentName)) {
            return await this.loading.get(componentName);
        }
        
        // Start loading
        const loadingPromise = this.loadModule(componentName);
        this.loading.set(componentName, loadingPromise);
        
        try {
            const ComponentClass = await loadingPromise;
            this.modules.set(componentName, ComponentClass);
            this.loading.delete(componentName);
            return ComponentClass;
        } catch (error) {
            this.loading.delete(componentName);
            throw error;
        }
    }
    
    async loadModule(componentName) {
        // Fallback a componentes existentes si no hay módulos separados
        const fallbackComponents = {
            'ChartComponent': () => window.ChartComponent,
            'TableComponent': () => window.TableComponent,
            'ModalComponent': () => window.ModalComponent,
            'FormComponent': () => window.FormComponent,
            'DashboardModule': () => window.DashboardPage,
            'AnalyticsModule': () => window.AnalyticsPage
        };
        
        try {
            // Intentar cargar como módulo ES6
            const module = await import(`/static/js/components/${componentName}.js`);
            return module.default || module[componentName];
        } catch (error) {
            // Fallback a componente global
            if (fallbackComponents[componentName]) {
                const Component = fallbackComponents[componentName]();
                if (Component) {
                    return Component;
                }
            }
            
            console.warn(`Failed to load component ${componentName}:`, error);
            return null;
        }
    }
}

// ===== EVENT BUS OPTIMIZADO =====

class EventBus {
    constructor() {
        this.events = new Map();
        this.onceEvents = new Set();
        this.debouncedCallbacks = new Map();
    }
    
    on(event, callback, options = {}) {
        if (!this.events.has(event)) {
            this.events.set(event, []);
        }
        
        const listener = { 
            callback, 
            options,
            id: Math.random().toString(36).substr(2, 9)
        };
        
        this.events.get(event).push(listener);
        
        // Return unsubscribe function
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
        
        listeners.forEach(({ callback, options, id }) => {
            if (options.once && this.onceEvents.has(id)) {
                return;
            }
            
            if (options.debounce) {
                this.debouncedEmit(callback, data, options.debounce, id);
            } else if (options.throttle) {
                this.throttledEmit(callback, data, options.throttle, id);
            } else {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            }
            
            if (options.once) {
                this.onceEvents.add(id);
            }
        });
    }
    
    debouncedEmit(callback, data, delay, id) {
        const key = `${id}-debounce`;
        
        if (this.debouncedCallbacks.has(key)) {
            clearTimeout(this.debouncedCallbacks.get(key));
        }
        
        const timeoutId = setTimeout(() => {
            callback(data);
            this.debouncedCallbacks.delete(key);
        }, delay);
        
        this.debouncedCallbacks.set(key, timeoutId);
    }
    
    throttledEmit(callback, data, delay, id) {
        const key = `${id}-throttle`;
        
        if (this.debouncedCallbacks.has(key)) {
            return; // Already throttled
        }
        
        callback(data);
        
        const timeoutId = setTimeout(() => {
            this.debouncedCallbacks.delete(key);
        }, delay);
        
        this.debouncedCallbacks.set(key, timeoutId);
    }
    
    removeAllListeners() {
        // Clear all timeouts
        this.debouncedCallbacks.forEach(timeoutId => {
            clearTimeout(timeoutId);
        });
        
        this.events.clear();
        this.onceEvents.clear();
        this.debouncedCallbacks.clear();
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
        
        // Persistence optimization
        this.persistenceQueue = new Set();
        this.persistenceTimeout = null;
        this.persistenceDelay = 1000;
        
        // Computed properties cache
        this.computedCache = new Map();
        this.computedDeps = new Map();
        
        // Debounce utilities
        this.debounceMap = new Map();
    }
    
    // Batch multiple updates for better performance
    batchSet(updates) {
        Object.entries(updates).forEach(([key, value]) => {
            this.batchUpdates.set(key, value);
            
            // Invalidate computed properties that depend on this key
            this.invalidateComputed(key);
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
        
        // Apply all updates
        updates.forEach(([key, value]) => {
            oldValues[key] = this.get(key);
            this.setNestedValue(this.data, key, value);
            this.addToHistory(key, oldValues[key], value);
        });
        
        // Notify all listeners at once
        updates.forEach(([key, value]) => {
            this.notifyListeners(key, value, oldValues[key]);
        });
        
        // Schedule persistence if needed
        if (updates.length > 0) {
            this.schedulePersistence();
        }
    }
    
    // Override set to use batching when beneficial
    set(key, value) {
        if (this.batchTimeout) {
            // Already batching, add to batch
            this.batchUpdates.set(key, value);
            this.invalidateComputed(key);
            return this;
        }
        
        // Single update, use original method
        return super.set(key, value);
    }
    
    // Smart persistence with debouncing
    schedulePersistence() {
        if (this.persistenceTimeout) {
            clearTimeout(this.persistenceTimeout);
        }
        
        this.persistenceTimeout = setTimeout(() => {
            this.saveToLocalStorage();
            this.persistenceTimeout = null;
        }, this.persistenceDelay);
    }
    
    // Computed properties with caching
    computed(key, computeFn, dependencies = []) {
        // Store computation function and dependencies
        this.computedCache.set(key, {
            fn: computeFn,
            value: null,
            valid: false
        });
        
        this.computedDeps.set(key, dependencies);
        
        // Subscribe to dependency changes
        const unsubscribers = dependencies.map(dep => 
            this.subscribe(dep, () => {
                this.invalidateComputed(key);
            })
        );
        
        // Initial computation
        this.getComputed(key);
        
        return () => unsubscribers.forEach(unsub => unsub());
    }
    
    getComputed(key) {
        const cached = this.computedCache.get(key);
        if (!cached) {
            return undefined;
        }
        
        if (!cached.valid) {
            cached.value = cached.fn();
            cached.valid = true;
        }
        
        return cached.value;
    }
    
    invalidateComputed(changedKey) {
        // Invalidate all computed properties that depend on this key
        this.computedDeps.forEach((deps, computedKey) => {
            if (deps.includes(changedKey) || deps.includes('*')) {
                const cached = this.computedCache.get(computedKey);
                if (cached) {
                    cached.valid = false;
                }
            }
        });
    }
    
    // Debounced operations
    debounce(key, fn, delay = 300) {
        if (this.debounceMap.has(key)) {
            clearTimeout(this.debounceMap.get(key));
        }
        
        const timeoutId = setTimeout(() => {
            fn();
            this.debounceMap.delete(key);
        }, delay);
        
        this.debounceMap.set(key, timeoutId);
    }
    
    // Memory cleanup override
    clear() {
        // Clear batch operations
        if (this.batchTimeout) {
            clearTimeout(this.batchTimeout);
            this.batchTimeout = null;
        }
        this.batchUpdates.clear();
        
        // Clear persistence
        if (this.persistenceTimeout) {
            clearTimeout(this.persistenceTimeout);
            this.persistenceTimeout = null;
        }
        
        // Clear computed cache
        this.computedCache.clear();
        this.computedDeps.clear();
        
        // Clear debounce timeouts
        this.debounceMap.forEach(timeoutId => clearTimeout(timeoutId));
        this.debounceMap.clear();
        
        return super.clear();
    }
    
    // Performance monitoring
    getPerformanceStats() {
        return {
            dataSize: JSON.stringify(this.data).length,
            historyLength: this.history.length,
            listenersCount: this.listeners.size,
            computedCount: this.computedCache.size,
            batchedUpdatesCount: this.batchUpdates.size
        };
    }
}

// ===== BACKWARD COMPATIBILITY =====

// Mantener compatibilidad con la implementación original
window.MABApp = MABAppOptimized;

// Wrapper para métodos legacy
if (typeof window !== 'undefined') {
    window.MAB = new Proxy({}, {
        get(target, prop) {
            // Lazy initialization del app
            if (!target._app) {
                const config = document.getElementById('page-config');
                const initialData = document.getElementById('initial-data');
                
                target._app = new MABAppOptimized({
                    initialData: initialData ? JSON.parse(initialData.textContent) : {},
                    user: config ? JSON.parse(config.textContent).user : null,
                    csrfToken: config ? JSON.parse(config.textContent).csrfToken : '',
                    currentPage: config ? JSON.parse(config.textContent).page : '/'
                });
            }
            
            // Redirigir a la instancia del app
            if (prop in target._app) {
                return target._app[prop];
            }
            
            // Métodos legacy
            return target._app.legacyAdapter(prop);
        }
    });
}
