// backend/static/js/pages/Experiments.js

class ExperimentsPage {
    constructor() {
        this.app = window.MAB;
        this.currentView = 'grid'; // grid or list
        this.experiments = [];
        this.filteredExperiments = [];
        this.filters = {
            search: '',
            status: '',
            date: ''
        };
        this.sortBy = 'created_desc';
        
        this.init();
    }
    
    init() {
        this.loadInitialData();
        this.setupEventListeners();
        this.initializeFilters();
        
        console.log('Experiments page initialized');
    }
    
    loadInitialData() {
        // Get experiments from initial data
        const initialData = this.app.state.get('initialData') || this.app.options.initialData;
        if (initialData && initialData.experiments) {
            this.experiments = initialData.experiments;
            this.filteredExperiments = [...this.experiments];
        }
    }
    
    // ===== EVENT LISTENERS =====
    
    setupEventListeners() {
        // Search input
        const searchInput = document.getElementById('experiment-search');
        if (searchInput) {
            searchInput.addEventListener('input', this.app.utils.debounce((e) => {
                this.filters.search = e.target.value;
                this.applyFilters();
            }, 300));
        }
        
        // Status filter
        const statusFilter = document.getElementById('status-filter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.filters.status = e.target.value;
                this.applyFilters();
            });
        }
        
        // Date filter
        const dateFilter = document.getElementById('date-filter');
        if (dateFilter) {
            dateFilter.addEventListener('change', (e) => {
                this.filters.date = e.target.value;
                this.applyFilters();
            });
        }
        
        // Sort dropdown
        const sortSelect = document.getElementById('sort-experiments');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.sortBy = e.target.value;
                this.applySorting();
            });
        }
        
        // View toggles
        document.querySelectorAll('.view-toggle').forEach(button => {
            button.addEventListener('click', (e) => {
                const view = e.target.closest('.view-toggle').dataset.view;
                this.setView(view);
            });
        });
        
        // Listen for experiment updates
        document.addEventListener('experiment:updated', (event) => {
            this.handleExperimentUpdate(event.detail.experiment);
        });
        
        // Listen for experiment creation
        document.addEventListener('experiment:created', (event) => {
            this.handleExperimentCreated(event.detail.experiment);
        });
    }
    
    initializeFilters() {
        // Set up any default filters or restore from localStorage
        const savedFilters = this.app.utils.storage.get('experiments_filters');
        if (savedFilters) {
            this.filters = { ...this.filters, ...savedFilters };
            this.restoreFilterUI();
        }
    }
    
    restoreFilterUI() {
        // Restore filter values in UI
        const searchInput = document.getElementById('experiment-search');
        if (searchInput) searchInput.value = this.filters.search;
        
        const statusFilter = document.getElementById('status-filter');
        if (statusFilter) statusFilter.value = this.filters.status;
        
        const dateFilter = document.getElementById('date-filter');
        if (dateFilter) dateFilter.value = this.filters.date;
    }
    
    // ===== VIEW MANAGEMENT =====
    
    setView(view) {
        if (view === this.currentView) return;
        
        this.currentView = view;
        
        // Update toggle buttons
        document.querySelectorAll('.view-toggle').forEach(button => {
            if (button.dataset.view === view) {
                button.classList.add('active', 'bg-white', 'text-gray-900');
                button.classList.remove('text-gray-500');
            } else {
                button.classList.remove('active', 'bg-white', 'text-gray-900');
                button.classList.add('text-gray-500');
            }
        });
        
        // Show/hide views
        const gridView = document.getElementById('experiments-grid');
        const listView = document.getElementById('experiments-list');
        
        if (view === 'grid') {
            gridView.classList.remove('hidden');
            listView.classList.add('hidden');
        } else {
            gridView.classList.add('hidden');
            listView.classList.remove('hidden');
        }
        
        // Save preference
        this.app.utils.storage.set('experiments_view', view);
    }
    
    // ===== FILTERING & SORTING =====
    
    applyFilters() {
        this.filteredExperiments = this.experiments.filter(experiment => {
            // Search filter
            if (this.filters.search) {
                const searchTerm = this.filters.search.toLowerCase();
                const matchesSearch = 
                    experiment.name.toLowerCase().includes(searchTerm) ||
                    experiment.url.toLowerCase().includes(searchTerm) ||
                    (experiment.description && experiment.description.toLowerCase().includes(searchTerm));
                
                if (!matchesSearch) return false;
            }
            
            // Status filter
            if (this.filters.status && experiment.status !== this.filters.status) {
                return false;
            }
            
            // Date filter
            if (this.filters.date) {
                const createdAt = new Date(experiment.created_at);
                const now = new Date();
                
                switch (this.filters.date) {
                    case 'today':
                        if (!this.app.utils.isToday(createdAt)) return false;
                        break;
                    case 'week':
                        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                        if (createdAt < weekAgo) return false;
                        break;
                    case 'month':
                        const monthAgo = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());
                        if (createdAt < monthAgo) return false;
                        break;
                    case 'quarter':
                        const quarterAgo = new Date(now.getFullYear(), now.getMonth() - 3, now.getDate());
                        if (createdAt < quarterAgo) return false;
                        break;
                }
            }
            
            return true;
        });
        
        // Save filters
        this.app.utils.storage.set('experiments_filters', this.filters);
        
        // Apply sorting and render
        this.applySorting();
    }
    
    applySorting() {
        this.filteredExperiments.sort((a, b) => {
            switch (this.sortBy) {
                case 'created_desc':
                    return new Date(b.created_at) - new Date(a.created_at);
                case 'created_asc':
                    return new Date(a.created_at) - new Date(b.created_at);
                case 'name_asc':
                    return a.name.localeCompare(b.name);
                case 'name_desc':
                    return b.name.localeCompare(a.name);
                case 'status':
                    const statusOrder = { active: 1, paused: 2, draft: 3, completed: 4 };
                    return (statusOrder[a.status] || 5) - (statusOrder[b.status] || 5);
                case 'visitors_desc':
                    const aVisitors = a.stats?.total_users || 0;
                    const bVisitors = b.stats?.total_users || 0;
                    return bVisitors - aVisitors;
                default:
                    return 0;
            }
        });
        
        this.renderExperiments();
    }
    
    // ===== RENDERING =====
    
    renderExperiments() {
        if (this.currentView === 'grid') {
            this.renderGridView();
        } else {
            this.renderListView();
        }
        
        this.updateStatsCards();
    }
    
    renderGridView() {
        const container = document.getElementById('experiments-grid');
        if (!container) return;
        
        if (this.filteredExperiments.length === 0) {
            container.innerHTML = this.getEmptyStateHTML();
            return;
        }
        
        const experimentsHTML = this.filteredExperiments.map(experiment => 
            this.createExperimentCard(experiment)
        ).join('');
        
        container.innerHTML = experimentsHTML;
    }
    
    renderListView() {
        const tbody = document.querySelector('#experiments-list tbody');
        if (!tbody) return;
        
        if (this.filteredExperiments.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="px-6 py-12 text-center">
                        ${this.getEmptyStateHTML()}
                    </td>
                </tr>
            `;
            return;
        }
        
        const rowsHTML = this.filteredExperiments.map(experiment => 
            this.createExperimentRow(experiment)
        ).join('');
        
        tbody.innerHTML = rowsHTML;
    }
    
    createExperimentCard(experiment) {
        const stats = experiment.stats || {};
        
        return `
            <div class="card experiment-card" data-experiment-id="${experiment.id}" data-status="${experiment.status}">
                <div class="card-body">
                    <!-- Header -->
                    <div class="flex items-start justify-between mb-4">
                        <div class="flex-1">
                            <h3 class="font-semibold text-gray-900 mb-1 cursor-pointer hover:text-brand-600 transition-colors" 
                                onclick="MAB.viewExperiment('${experiment.id}')">
                                ${this.app.utils.escapeHtml(experiment.name)}
                            </h3>
                            <p class="text-sm text-gray-500">${this.extractDomain(experiment.url)}</p>
                            <p class="text-xs text-gray-400 mt-1">${this.app.formatTimeAgo(experiment.created_at)}</p>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="badge badge-${experiment.status}">
                                ${this.app.utils.capitalize(experiment.status)}
                            </span>
                            <div class="relative">
                                <button onclick="MAB.toggleExperimentMenu('${experiment.id}')" 
                                        class="p-1 hover:bg-gray-100 rounded">
                                    <svg class="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
                                    </svg>
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Stats -->
                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <div class="text-center">
                            <div class="text-lg font-bold text-gray-900" data-live-metric="visitors-${experiment.id}">
                                ${this.app.formatNumber(stats.total_users || 0)}
                            </div>
                            <div class="text-xs text-gray-500">Visitors</div>
                        </div>
                        <div class="text-center">
                            <div class="text-lg font-bold text-gray-900" data-live-metric="conversion-${experiment.id}">
                                ${this.app.formatPercentage(stats.conversion_rate || 0, 1)}
                            </div>
                            <div class="text-xs text-gray-500">Conversion</div>
                        </div>
                    </div>

                    ${experiment.status === 'active' ? `
                    <!-- Progress Bar -->
                    <div class="mb-4">
                        <div class="flex justify-between items-center mb-2">
                            <span class="text-xs text-gray-500">Confidence</span>
                            <span class="text-xs font-medium text-gray-700" data-live-metric="confidence-${experiment.id}">
                                ${Math.round(stats.confidence || 0)}%
                            </span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2">
                            <div class="bg-brand-500 h-2 rounded-full transition-all duration-300" 
                                 style="width: ${stats.confidence || 0}%"></div>
                        </div>
                    </div>
                    ` : ''}

                    <!-- Actions -->
                    <div class="flex gap-2">
                        <button onclick="MAB.viewExperiment('${experiment.id}')" 
                                class="flex-1 btn btn-sm btn-secondary">
                            View Details
                        </button>
                        ${this.getExperimentActionButton(experiment)}
                    </div>
                </div>
            </div>
        `;
    }
    
    createExperimentRow(experiment) {
        const stats = experiment.stats || {};
        
        return `
            <tr class="hover:bg-gray-50" data-experiment-id="${experiment.id}">
                <td class="px-6 py-4">
                    <div>
                        <div class="font-medium text-gray-900 cursor-pointer hover:text-brand-600 transition-colors"
                             onclick="MAB.viewExperiment('${experiment.id}')">
                            ${this.app.utils.escapeHtml(experiment.name)}
                        </div>
                        <div class="text-sm text-gray-500">${this.extractDomain(experiment.url)}</div>
                        ${experiment.description ? `<div class="text-xs text-gray-400 mt-1">${this.app.utils.truncate(experiment.description, 60)}</div>` : ''}
                    </div>
                </td>
                <td class="px-6 py-4">
                    <span class="badge badge-${experiment.status}">
                        ${this.app.utils.capitalize(experiment.status)}
                    </span>
                </td>
                <td class="px-6 py-4 text-sm text-gray-900" data-live-metric="visitors-${experiment.id}">
                    ${this.app.formatNumber(stats.total_users || 0)}
                </td>
                <td class="px-6 py-4 text-sm text-gray-900" data-live-metric="conversion-${experiment.id}">
                    ${this.app.formatPercentage(stats.conversion_rate || 0, 1)}
                </td>
                <td class="px-6 py-4 text-sm text-gray-900" data-live-metric="confidence-${experiment.id}">
                    ${experiment.status === 'active' ? Math.round(stats.confidence || 0) + '%' : '<span class="text-gray-400">-</span>'}
                </td>
                <td class="px-6 py-4 text-sm text-gray-500">
                    ${this.app.formatTimeAgo(experiment.created_at)}
                </td>
                <td class="px-6 py-4 text-right">
                    <div class="flex items-center justify-end gap-2">
                        <button onclick="MAB.viewExperiment('${experiment.id}')" 
                                class="btn btn-sm btn-secondary">
                            View
                        </button>
                        ${this.getExperimentActionButton(experiment)}
                    </div>
                </td>
            </tr>
        `;
    }
    
    getExperimentActionButton(experiment) {
        switch (experiment.status) {
            case 'draft':
                return `<button data-action="start-experiment" data-target="${experiment.id}" class="btn btn-sm btn-primary">Start</button>`;
            case 'active':
                return `<button data-action="pause-experiment" data-target="${experiment.id}" class="btn btn-sm btn-secondary">Pause</button>`;
            case 'paused':
                return `<button data-action="start-experiment" data-target="${experiment.id}" class="btn btn-sm btn-primary">Resume</button>`;
            default:
                return '';
        }
    }
    
    getEmptyStateHTML() {
        const isFiltered = this.filters.search || this.filters.status || this.filters.date;
        
        if (isFiltered) {
            return `
                <div class="col-span-full text-center py-12">
                    <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                    </svg>
                    <h3 class="text-xl font-medium text-gray-900 mb-2">No experiments found</h3>
                    <p class="text-gray-500 mb-6">Try adjusting your search or filter criteria</p>
                    <button onclick="MAB.clearFilters()" class="btn btn-secondary">
                        Clear Filters
                    </button>
                </div>
            `;
        }
        
        return `
            <div class="col-span-full text-center py-12">
                <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
                </svg>
                <h3 class="text-xl font-medium text-gray-900 mb-2">No experiments found</h3>
                <p class="text-gray-500 mb-6">Get started by creating your first A/B test experiment</p>
                <button onclick="MAB.createExperiment()" class="btn btn-primary">
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                    </svg>
                    Create Your First Test
                </button>
            </div>
        `;
    }
    
    updateStatsCards() {
        // Update the stats cards based on filtered experiments
        const totalCount = this.filteredExperiments.length;
        const activeCount = this.filteredExperiments.filter(e => e.status === 'active').length;
        const draftCount = this.filteredExperiments.filter(e => e.status === 'draft').length;
        
        // Update the display (if we want to show filtered stats)
        // For now, keep original stats from initial data
    }
    
    // ===== EVENT HANDLERS =====
    
    handleExperimentUpdate(experiment) {
        // Update experiment in our arrays
        const index = this.experiments.findIndex(e => e.id === experiment.id);
        if (index !== -1) {
            this.experiments[index] = { ...this.experiments[index], ...experiment };
            this.applyFilters(); // Re-render
        }
    }
    
    handleExperimentCreated(experiment) {
        // Add new experiment to the beginning
        this.experiments.unshift(experiment);
        this.applyFilters(); // Re-render
        
        // Show success message
        this.app.showToast('Experiment created successfully!', 'success');
    }
    
    // ===== EXPERIMENT ACTIONS =====
    
    toggleExperimentMenu(experimentId) {
        // Simple implementation - could be expanded with proper dropdown
        this.app.showToast('Experiment menu coming soon!', 'info');
    }
    
    clearFilters() {
        // Reset all filters
        this.filters = {
            search: '',
            status: '',
            date: ''
        };
        
        // Clear UI
        const searchInput = document.getElementById('experiment-search');
        if (searchInput) searchInput.value = '';
        
        const statusFilter = document.getElementById('status-filter');
        if (statusFilter) statusFilter.value = '';
        
        const dateFilter = document.getElementById('date-filter');
        if (dateFilter) dateFilter.value = '';
        
        // Apply filters (will show all experiments)
        this.applyFilters();
    }
    
    exportExperiments() {
        // Prepare data for export
        const exportData = this.filteredExperiments.map(experiment => ({
            name: experiment.name,
            url: experiment.url,
            status: experiment.status,
            visitors: experiment.stats?.total_users || 0,
            conversion_rate: experiment.stats?.conversion_rate || 0,
            confidence: experiment.stats?.confidence || 0,
            created_at: experiment.created_at
        }));
        
        // Create CSV
        const csvContent = this.convertToCSV(exportData);
        
        // Download
        this.downloadCSV(csvContent, 'experiments.csv');
    }
    
    convertToCSV(data) {
        if (data.length === 0) return '';
        
        const headers = Object.keys(data[0]).join(',');
        const rows = data.map(row => 
            Object.values(row).map(value => 
                typeof value === 'string' ? `"${value.replace(/"/g, '""')}"` : value
            ).join(',')
        );
        
        return [headers, ...rows].join('\n');
    }
    
    downloadCSV(content, filename) {
        const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }
    }
    
    // ===== UTILITIES =====
    
    extractDomain(url) {
        try {
            return new URL(url).hostname;
        } catch {
            return url;
        }
    }
    
    // ===== REFRESH DATA =====
    
    async refreshExperiments() {
        try {
            this.app.showLoading(true);
            
            const response = await this.app.api.get('/api/experiments');
            if (response.success) {
                this.experiments = response.data;
                this.applyFilters();
            }
            
        } catch (error) {
            this.app.handleAPIError(error);
        } finally {
            this.app.showLoading(false);
        }
    }
    
    // ===== CLEANUP =====
    
    destroy() {
        // Clear any intervals or cleanup resources
        console.log('Experiments page destroyed');
    }
}

// Extend MAB app with experiments-specific methods
if (window.MAB) {
    window.MAB.setExperimentsView = function(view) {
        if (window.experimentsPage) {
            window.experimentsPage.setView(view);
        }
    };
    
    window.MAB.toggleExperimentMenu = function(experimentId) {
        if (window.experimentsPage) {
            window.experimentsPage.toggleExperimentMenu(experimentId);
        }
    };
    
    window.MAB.clearFilters = function() {
        if (window.experimentsPage) {
            window.experimentsPage.clearFilters();
        }
    };
    
    window.MAB.exportExperiments = function() {
        if (window.experimentsPage) {
            window.experimentsPage.exportExperiments();
        }
    };
}

// Make available globally
window.ExperimentsPage = ExperimentsPage;
