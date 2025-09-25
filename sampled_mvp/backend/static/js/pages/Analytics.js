// backend/static/js/pages/Analytics.js

class AnalyticsPage {
    constructor() {
        this.app = window.MAB;
        this.charts = {};
        this.dateRange = '30_days';
        this.performanceMetric = 'conversion';
        
        this.init();
    }
    
    init() {
        this.loadInitialData();
        this.setupEventListeners();
        this.initializeCharts();
        
        console.log('Analytics page initialized');
    }
    
    loadInitialData() {
        const initialData = this.app.state.get('initialData') || this.app.options.initialData;
        if (initialData) {
            this.analyticsData = initialData;
        }
    }
    
    // ===== EVENT LISTENERS =====
    
    setupEventListeners() {
        // Date range selector
        const dateRangeSelect = document.getElementById('date-range-select');
        if (dateRangeSelect) {
            dateRangeSelect.addEventListener('change', (e) => {
                this.dateRange = e.target.value;
                this.handleDateRangeChange();
            });
        }
        
        // Performance metric selector
        const performanceMetric = document.getElementById('performance-metric');
        if (performanceMetric) {
            performanceMetric.addEventListener('change', (e) => {
                this.performanceMetric = e.target.value;
                this.updatePerformanceChart();
            });
        }
        
        // Listen for data updates
        document.addEventListener('analytics:updated', (event) => {
            this.handleDataUpdate(event.detail);
        });
    }
    
    // ===== CHART INITIALIZATION =====
    
    initializeCharts() {
        this.initConversionTrendsChart();
        this.initPerformanceChart();
    }
    
    initConversionTrendsChart() {
        const container = document.getElementById('conversion-trends-chart');
        if (!container) return;
        
        // Generate sample trend data
        const trendData = this.generateTrendData();
        this.renderLineChart(container, trendData, 'conversion-trends');
    }
    
    initPerformanceChart() {
        const container = document.getElementById('performance-chart');
        if (!container) return;
        
        // Generate sample performance data
        const performanceData = this.generatePerformanceData();
        this.renderBarChart(container, performanceData, 'performance');
    }
    
    generateTrendData() {
        const days = this.getDaysForRange();
        const data = [];
        const baseDate = new Date();
        baseDate.setDate(baseDate.getDate() - days);
        
        for (let i = 0; i < days; i++) {
            const date = new Date(baseDate);
            date.setDate(baseDate.getDate() + i);
            
            // Generate trend data with some seasonality
            const dayOfWeek = date.getDay();
            const weekendFactor = (dayOfWeek === 0 || dayOfWeek === 6) ? 0.8 : 1.0;
            
            const controlRate = (2.5 + Math.sin(i / 7) * 0.5 + Math.random() * 0.8) * weekendFactor;
            const variantRate = (3.2 + Math.sin(i / 7) * 0.6 + Math.random() * 0.9) * weekendFactor;
            
            data.push({
                date: date.toISOString().split('T')[0],
                control: Math.max(0, controlRate),
                variants: Math.max(0, variantRate),
                visitors: Math.floor(800 + Math.random() * 400) * weekendFactor
            });
        }
        
        return data;
    }
    
    generatePerformanceData() {
        // Sample experiment performance data
        return [
            { name: 'Homepage Hero', lift: 23.4, confidence: 95, visitors: 5200 },
            { name: 'Checkout Flow', lift: 12.1, confidence: 78, visitors: 3100 },
            { name: 'Product CTA', lift: -5.2, confidence: 67, visitors: 2800 },
            { name: 'Navigation Test', lift: 8.7, confidence: 89, visitors: 4100 },
            { name: 'Pricing Page', lift: 15.3, confidence: 92, visitors: 2200 },
            { name: 'Footer Links', lift: 3.1, confidence: 45, visitors: 1800 }
        ];
    }
    
    getDaysForRange() {
        switch (this.dateRange) {
            case '7_days': return 7;
            case '30_days': return 30;
            case '90_days': return 90;
            case '6_months': return 180;
            case '1_year': return 365;
            default: return 30;
        }
    }
    
    // ===== CHART RENDERING =====
    
    renderLineChart(container, data, chartId) {
        const width = container.offsetWidth;
        const height = 320;
        const margin = { top: 20, right: 30, bottom: 50, left: 60 };
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
        const maxY = Math.max(...data.map(d => Math.max(d.control, d.variants))) * 1.1;
        const yScale = chartHeight / maxY;
        
        // Create chart group
        const chartGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        chartGroup.setAttribute('transform', `translate(${margin.left},${margin.top})`);
        
        // Draw grid and axes
        this.drawChartGrid(chartGroup, chartWidth, chartHeight, maxY);
        this.drawChartAxes(chartGroup, chartWidth, chartHeight, data, maxY);
        
        // Draw lines
        this.drawTrendLine(chartGroup, data, 'control', '#465fff', xStep, yScale, chartHeight);
        this.drawTrendLine(chartGroup, data, 'variants', '#12b76a', xStep, yScale, chartHeight);
        
        // Draw dots with hover effects
        this.drawTrendDots(chartGroup, data, 'control', '#465fff', xStep, yScale, chartHeight);
        this.drawTrendDots(chartGroup, data, 'variants', '#12b76a', xStep, yScale, chartHeight);
        
        svg.appendChild(chartGroup);
        container.appendChild(svg);
        
        this.charts[chartId] = { svg, data, container };
    }
    
    renderBarChart(container, data, chartId) {
        const width = container.offsetWidth;
        const height = 320;
        const margin = { top: 20, right: 30, bottom: 80, left: 60 };
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
        const barWidth = chartWidth / data.length * 0.7;
        const barSpacing = chartWidth / data.length * 0.3;
        const maxLift = Math.max(...data.map(d => Math.abs(d.lift))) * 1.2;
        const yScale = chartHeight / (maxLift * 2);
        const zeroY = chartHeight / 2;
        
        // Create chart group
        const chartGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        chartGroup.setAttribute('transform', `translate(${margin.left},${margin.top})`);
        
        // Draw zero line
        const zeroLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        zeroLine.setAttribute('x1', '0');
        zeroLine.setAttribute('x2', chartWidth);
        zeroLine.setAttribute('y1', zeroY);
        zeroLine.setAttribute('y2', zeroY);
        zeroLine.setAttribute('stroke', '#e4e7ec');
        zeroLine.setAttribute('stroke-width', '2');
        chartGroup.appendChild(zeroLine);
        
        // Draw bars
        data.forEach((d, i) => {
            const x = i * (barWidth + barSpacing) + barSpacing / 2;
            const barHeight = Math.abs(d.lift) * yScale;
            const y = d.lift >= 0 ? zeroY - barHeight : zeroY;
            const color = d.lift >= 0 ? '#12b76a' : '#ef4444';
            
            // Bar
            const bar = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            bar.setAttribute('x', x);
            bar.setAttribute('y', y);
            bar.setAttribute('width', barWidth);
            bar.setAttribute('height', barHeight);
            bar.setAttribute('fill', color);
            bar.setAttribute('opacity', d.confidence >= 90 ? '1' : '0.6');
            bar.setAttribute('rx', '3');
            
            // Add hover effect
            bar.addEventListener('mouseenter', () => {
                this.showBarTooltip(x + barWidth / 2, y, d);
            });
            
            bar.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
            
            chartGroup.appendChild(bar);
            
            // Label
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', x + barWidth / 2);
            label.setAttribute('y', chartHeight + 20);
            label.setAttribute('text-anchor', 'middle');
            label.setAttribute('fill', '#667085');
            label.setAttribute('font-size', '11');
            label.setAttribute('transform', `rotate(-45, ${x + barWidth / 2}, ${chartHeight + 20})`);
            label.textContent = d.name;
            chartGroup.appendChild(label);
        });
        
        // Y-axis labels
        for (let i = -2; i <= 2; i++) {
            const y = zeroY - (i * maxLift / 2 * yScale);
            const value = (i * maxLift / 2).toFixed(1);
            
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', '-10');
            label.setAttribute('y', y + 4);
            label.setAttribute('text-anchor', 'end');
            label.setAttribute('fill', '#667085');
            label.setAttribute('font-size', '12');
            label.textContent = value + '%';
            chartGroup.appendChild(label);
        }
        
        svg.appendChild(chartGroup);
        container.appendChild(svg);
        
        this.charts[chartId] = { svg, data, container };
    }
    
    drawChartGrid(group, width, height, maxY) {
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
    
    drawChartAxes(group, width, height, data, maxY) {
        // Y-axis
        const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        yAxis.setAttribute('x1', '0');
        yAxis.setAttribute('x2', '0');
        yAxis.setAttribute('y1', '0');
        yAxis.setAttribute('y2', height);
        yAxis.setAttribute('stroke', '#e4e7ec');
        yAxis.setAttribute('stroke-width', '1');
        group.appendChild(yAxis);
        
        // X-axis
        const xAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        xAxis.setAttribute('x1', '0');
        xAxis.setAttribute('x2', width);
        xAxis.setAttribute('y1', height);
        xAxis.setAttribute('y2', height);
        xAxis.setAttribute('stroke', '#e4e7ec');
        xAxis.setAttribute('stroke-width', '1');
        group.appendChild(xAxis);
        
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
            group.appendChild(label);
        }
        
        // X-axis labels (every few days)
        const step = Math.max(1, Math.floor(data.length / 8));
        data.forEach((d, i) => {
            if (i % step === 0) {
                const x = i * (width / (data.length - 1));
                const date = new Date(d.date);
                const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                label.setAttribute('x', x);
                label.setAttribute('y', height + 20);
                label.setAttribute('text-anchor', 'middle');
                label.setAttribute('fill', '#667085');
                label.setAttribute('font-size', '12');
                label.textContent = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                group.appendChild(label);
            }
        });
    }
    
    drawTrendLine(group, data, key, color, xStep, yScale, chartHeight) {
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
        path.setAttribute('stroke-width', '3');
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('stroke-linejoin', 'round');
        
        group.appendChild(path);
    }
    
    drawTrendDots(group, data, key, color, xStep, yScale, chartHeight) {
        data.forEach((d, i) => {
            const x = i * xStep;
            const y = chartHeight - (d[key] * yScale);
            
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', x);
            circle.setAttribute('cy', y);
            circle.setAttribute('r', '4');
            circle.setAttribute('fill', color);
            circle.setAttribute('stroke', 'white');
            circle.setAttribute('stroke-width', '2');
            
            circle.addEventListener('mouseenter', () => {
                this.showLineTooltip(x, y, d, key);
                circle.setAttribute('r', '6');
            });
            
            circle.addEventListener('mouseleave', () => {
                this.hideTooltip();
                circle.setAttribute('r', '4');
            });
            
            group.appendChild(circle);
        });
    }
    
    // ===== TOOLTIPS =====
    
    showLineTooltip(x, y, data, key) {
        this.showTooltip(x, y, `
            <div class="text-xs font-medium">${new Date(data.date).toLocaleDateString()}</div>
            <div class="text-xs">${key === 'control' ? 'Control' : 'Variants'}: ${data[key].toFixed(2)}%</div>
            <div class="text-xs">Visitors: ${data.visitors.toLocaleString()}</div>
        `);
    }
    
    showBarTooltip(x, y, data) {
        this.showTooltip(x, y, `
            <div class="text-xs font-medium">${data.name}</div>
            <div class="text-xs">Lift: ${data.lift > 0 ? '+' : ''}${data.lift.toFixed(1)}%</div>
            <div class="text-xs">Confidence: ${data.confidence}%</div>
            <div class
