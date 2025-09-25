// backend/static/js/pages/Dashboard.js

class DashboardPage {
    constructor() {
        this.app = window.MAB;
        this.chart = null;
        this.refreshInterval = null;
        
        this.init();
    }
    
    init() {
        this.initializeChart();
        this.setupEventListeners();
        this.startAutoRefresh();
        
        console.log('Dashboard page initialized');
    }
    
    // ===== EVENT LISTENERS =====
    
    setupEventListeners() {
        // Listen for data updates
        document.addEventListener('dashboard:refreshed', (event) => {
            this.handleDataRefresh(event.detail.data);
        });
        
        // Listen for experiment updates
        document.addEventListener('experiment:updated', (event) => {
            this.handleExperimentUpdate(event.detail.experiment);
        });
        
        // Handle table row clicks
        this.app.utils.delegate(document, '[data-experiment-id]', 'click', (event) => {
            if (!event.target.closest('button')) {
                const experimentId = event.currentTarget.dataset.experimentId;
                this.app.viewExperiment(experimentId);
            }
        });
    }
    
    // ===== CHART INITIALIZATION =====
    
    initializeChart() {
        const chartContainer = document.getElementById('performance-chart');
        if (!chartContainer) return;
        
        // Sample data for the chart - in a real app this would come from your API
        const chartData = this.generateSampleChartData();
        
        this.renderChart(chartContainer, chartData);
    }
    
    generateSampleChartData() {
        const days = 30;
        const data = [];
        const baseDate = new Date();
        baseDate.setDate(baseDate.getDate() - days);
        
        for (let i = 0; i < days; i++) {
            const date = new Date(baseDate);
            date.setDate(baseDate.getDate() + i);
            
            // Generate sample conversion rates
            const controlRate = 0.025 + (Math.random() - 0.5) * 0.01;
            const variantRate = 0.032 + (Math.random() - 0.5) * 0.012;
            
            data.push({
                date: date.toISOString().split('T')[0],
                control: Math.max(0, controlRate * 100),
                variant: Math.max(0, variantRate * 100)
            });
        }
        
        return data;
    }
    
    renderChart(container, data) {
        // Simple SVG chart implementation
        // In a real app, you might use Chart.js, D3.js, or another charting library
        
        const width = container.offsetWidth;
        const height = 320;
        const margin = { top: 20, right: 30, bottom: 40, left: 50 };
        const chartWidth = width - margin.left - margin.right;
        const chartHeight = height - margin.top - margin.bottom;
        
        // Clear container
        container.innerHTML = '';
        
        // Create SVG
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', width);
        svg.setAttribute('height', height);
        svg.classList.add('w-full', 'h-full');
        
        // Calculate scales
        const xStep = chartWidth / (data.length - 1);
        const maxY = Math.max(...data.map(d => Math.max(d.control, d.variant))) * 1.1;
        const yScale = chartHeight / maxY;
        
        // Create chart group
        const chartGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        chartGroup.setAttribute('transform', `translate(${margin.left},${margin.top})`);
        
        // Draw grid lines
        this.drawGridLines(chartGroup, chartWidth, chartHeight, maxY);
        
        // Draw axes
        this.drawAxes(chartGroup, chartWidth, chartHeight, data, maxY);
        
        // Draw lines
        this.drawLine(chartGroup, data, 'control', '#465fff', xStep, yScale, chartHeight);
        this.drawLine(chartGroup, data, 'variant', '#12b76a', xStep, yScale, chartHeight);
        
        // Add dots
        this.drawDots(chartGroup, data, 'control', '#465fff', xStep, yScale, chartHeight);
        this.drawDots(chartGroup, data, 'variant', '#12b76a', xStep, yScale, chartHeight);
        
        svg.appendChild(chartGroup);
        container.appendChild(svg);
        
        this.chart = { svg, data };
    }
    
    drawGridLines(group, width, height, maxY) {
        const gridGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        gridGroup.setAttribute('stroke', '#f3f4f7');
        gridGroup.setAttribute('stroke-width', '1');
        
        // Horizontal grid lines
        for (let i = 0; i <= 5; i++) {
            const y = (height / 5) * i;
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', '0');
            line.setAttribute('x2', width);
            line.setAttribute('y1', y);
            line.setAttribute('y2', y);
            gridGroup.appendChild(line);
        }
        
        group.appendChild(gridGroup);
    }
    
    drawAxes(group, width, height, data, maxY) {
        const axesGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        
        // Y-axis
        const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        yAxis.setAttribute('x1', '0');
        yAxis.setAttribute('x2', '0');
        yAxis.setAttribute('y1', '0');
        yAxis.setAttribute('y2', height);
        yAxis.setAttribute('stroke', '#e4e7ec');
        yAxis.setAttribute('stroke-width', '1');
        axesGroup.appendChild(yAxis);
        
        // X-axis
        const xAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        xAxis.setAttribute('x1', '0');
        xAxis.setAttribute('x2', width);
        xAxis.setAttribute('y1', height);
        xAxis.setAttribute('y2', height);
        xAxis.setAttribute('stroke', '#e4e7ec');
        xAxis.setAttribute('stroke-width', '1');
        axesGroup.appendChild(xAxis);
        
        // Y-axis labels
        for (let i = 0; i <= 5; i++) {
            const value = (maxY / 5) * (5 - i);
            const y = (height / 5) * i + 4;
            
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', '-10');
            label.setAttribute('y', y);
            label.setAttribute('text-anchor', 'end');
            label.setAttribute('fill', '#667085');
            label.setAttribute('font-size', '12');
            label.textContent = value.toFixed(1) + '%';
            axesGroup.appendChild(label);
        }
        
        // X-axis labels (show every 5th day)
        data.forEach((d, i) => {
            if (i % 5 === 0) {
                const x = i * (width / (data.length - 1));
                const date = new Date(d.date);
                const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                label.setAttribute('x', x);
                label.setAttribute('y', height + 20);
                label.setAttribute('text-anchor', 'middle');
                label.setAttribute('fill', '#667085');
                label.setAttribute('font-size', '12');
                label.textContent = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                axesGroup.appendChild(label);
            }
        });
        
        group.appendChild(axesGroup);
    }
    
    drawLine(group, data, key, color, xStep, yScale, chartHeight) {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        
        let pathData = '';
        data.forEach((d, i) => {
            const x = i * xStep;
            const y = chartHeight - (d[key] * yScale);
            
            if (i === 0) {
                pathData += `M ${x} ${y}`;
            } else {
                pathData += ` L ${x} ${y}`;
            }
        });
        
        path.setAttribute('d', pathData);
        path.setAttribute('stroke', color);
        path.setAttribute('stroke-width', '2');
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('stroke-linejoin', 'round');
        
        group.appendChild(path);
    }
    
    drawDots(group, data, key, color, xStep, yScale, chartHeight) {
        const dotsGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        
        data.forEach((d, i) => {
            const x = i * xStep;
            const y = chartHeight - (d[key] * yScale);
            
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', x);
            circle.setAttribute('cy', y);
            circle.setAttribute('r', '3');
            circle.setAttribute('fill', color);
            circle.setAttribute('stroke', 'white');
            circle.setAttribute('stroke-width', '2');
            
            // Add hover effect
            circle.addEventListener('mouseenter', () => {
                this.showTooltip(x, y, d, key);
            });
            
            circle.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
            
            dotsGroup.appendChild(circle);
        });
        
        group.appendChild(dotsGroup);
    }
    
    showTooltip(x, y, data, key) {
        // Simple tooltip implementation
        let tooltip = document.getElementById('chart-tooltip');
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = 'chart-tooltip';
            tooltip.className = 'absolute bg-gray-900 text-white text-xs rounded px-2 py-1 pointer-events-none z-50';
            document.body.appendChild(tooltip);
        }
        
        const value = data[key].toFixed(2);
        const date = new Date(data.date).toLocaleDateString();
        tooltip.innerHTML = `${date}<br>${key}: ${value}%`;
        
        const rect = document.getElementById('performance-chart').getBoundingClientRect();
        tooltip.style.left = (rect.left + x + 10) + 'px';
        tooltip.style.top = (rect.top + y - 10) + 'px';
        tooltip.classList.remove('hidden');
    }
    
    hideTooltip() {
        const tooltip = document.getElementById('chart-tooltip');
        if (tooltip) {
            tooltip.classList.add('hidden');
        }
    }
    
    // ===== DATA HANDLING =====
    
    handleDataRefresh(data) {
        this.updateStats(data.stats);
        this.updateExperimentsTable(data.experiments);
        this.updateChart(data.chartData);
        this.updateActivity(data.recent_activity);
    }
    
    updateStats(stats) {
        // Update live metric elements
        Object.entries(stats).forEach(([key, value]) => {
            const elements = document.querySelectorAll(`[data-live-metric="${key}"]`);
            elements.forEach(element => {
                this.app.animateValueChange(element, this.formatStatValue(key, value));
            });
        });
    }
    
    formatStatValue(key, value) {
        switch (key) {
            case 'total_visitors':
                return this.app.formatNumber(value);
            case 'avg_conversion':
                return this.app.formatPercentage(value, 1);
            case 'revenue_impact':
                return ' + this.app.formatNumber(value);
            default:
                return value;
        }
    }
    
    updateExperimentsTable(experiments) {
        const tbody = document.querySelector('table tbody');
        if (!tbody) return;
        
        // Clear existing rows
        tbody.innerHTML = '';
        
        if (experiments.length === 0) {
            tbody.innerHTML = this.getEmptyStateHTML();
            return;
        }
        
        // Add experiment rows
        experiments.forEach(experiment => {
            tbody.appendChild(this.createExperimentRow(experiment));
        });
    }
    
    createExperimentRow(experiment) {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';
        row.setAttribute('data-experiment-id', experiment.id);
        
        row.innerHTML = `
            <td class="px-6 py-4">
                <div>
                    <div class="font-medium text-gray-900">${this.app.utils.escapeHtml(experiment.name)}</div>
                    <div class="text-sm text-gray-500">${this.extractDomain(experiment.url)}</div>
                </div>
            </td>
            <td class="px-6 py-4">
                <span class="badge badge-${experiment.status}">
                    ${this.app.utils.capitalize(experiment.status)}
                </span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-900" data-live-metric="visitors-${experiment.id}">
                ${this.app.formatNumber(experiment.total_users || 0)}
            </td>
            <td class="px-6 py-4 text-sm text-gray-900" data-live-metric="conversion-${experiment.id}">
                ${this.app.formatPercentage(experiment.conversion_rate || 0, 1)}
            </td>
            <td class="px-6 py-4 text-sm text-gray-900" data-live-metric="confidence-${experiment.id}">
                ${experiment.status === 'active' ? Math.round(experiment.confidence || 0) + '%' : '<span class="text-gray-400">-</span>'}
            </td>
            <td class="px-6 py-4 text-right">
                <div class="flex items-center justify-end gap-2">
                    <button onclick="MAB.viewExperiment('${experiment.id}')" class="btn btn-sm btn-secondary">
                        View
                    </button>
                    ${this.getExperimentActionButton(experiment)}
                </div>
            </td>
        `;
        
        return row;
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
        return `
            <tr>
                <td colspan="6" class="px-6 py-12 text-center">
                    <div class="text-center">
                        <svg class="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
                        </svg>
                        <h3 class="text-gray-900 font-medium mb-1">No experiments yet</h3>
                        <p class="text-gray-500 mb-4">Get started by creating your first A/B test</p>
                        <button onclick="MAB.createExperiment()" class="btn btn-primary">
                            Create First Test
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }
    
    handleExperimentUpdate(experiment) {
        // Update specific experiment row
        const row = document.querySelector(`[data-experiment-id="${experiment.id}"]`);
        if (row) {
            const newRow = this.createExperimentRow(experiment);
            row.parentNode.replaceChild(newRow, row);
        }
    }
    
    updateChart(chartData) {
        if (chartData && this.chart) {
            // Re-render chart with new data
            const container = document.getElementById('performance-chart');
            if (container) {
                this.renderChart(container, chartData);
            }
        }
    }
    
    updateActivity(activities) {
        const container = document.querySelector('.card:last-child .card-body');
        if (!container || !activities) return;
        
        if (activities.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <svg class="w-12 h-12 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <p class="text-gray-500">No recent activity</p>
                </div>
            `;
            return;
        }
        
        const activityHTML = activities.map(activity => `
            <div class="flex items-start gap-3">
                <div class="w-2 h-2 bg-brand-500 rounded-full mt-2 flex-shrink-0"></div>
                <div>
                    <p class="text-sm text-gray-900">${this.app.utils.escapeHtml(activity.description)}</p>
                    <p class="text-xs text-gray-500 mt-1">${this.app.formatTimeAgo(activity.created_at)}</p>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = `<div class="space-y-4">${activityHTML}</div>`;
    }
    
    // ===== AUTO REFRESH =====
    
    startAutoRefresh() {
        // Refresh data every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.app.refresh();
        }, 5 * 60 * 1000);
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
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
    
    // ===== DASHBOARD ACTIONS =====
    
    showDatePicker() {
        // Placeholder for date picker functionality
        this.app.showToast('Date picker coming soon!', 'info');
    }
    
    exportDashboard() {
        // Placeholder for export functionality
        this.app.showToast('Export functionality coming soon!', 'info');
    }
    
    // ===== CLEANUP =====
    
    destroy() {
        this.stopAutoRefresh();
        
        // Remove tooltips
        const tooltip = document.getElementById('chart-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
        
        // Clear chart reference
        this.chart = null;
        
        console.log('Dashboard page destroyed');
    }
}

// Make available globally
window.DashboardPage = DashboardPage;
