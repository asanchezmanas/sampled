// backend/static/js/components/index.js - Sistema de componentes para MAB

/**
 * MAB Components System
 * Maneja la inicialización y funcionalidad de todos los componentes UI
 */

class MABComponents {
    constructor() {
        this.components = new Map();
        this.init();
    }
    
    init() {
        this.initializeDropdowns();
        this.initializeModals();
        this.initializeTables();
        this.initializeFormElements();
        this.initializeTooltips();
        
        // Auto-inicializar componentes cuando se agregue contenido dinámico
        this.observeForNewContent();
        
        console.log('MAB Components initialized');
    }
    
    // ===== DROPDOWN COMPONENTS =====
    
    initializeDropdowns() {
        document.querySelectorAll('[data-dropdown]').forEach(dropdown => {
            this.initializeDropdown(dropdown);
        });
    }
    
    initializeDropdown(element) {
        const trigger = element.querySelector('[data-dropdown-toggle]');
        const menu = element.querySelector('.dropdown-menu');
        
        if (!trigger || !menu) return;
        
        // Toggle dropdown
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.toggleDropdown(element);
        });
        
        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!element.contains(e.target)) {
                this.closeDropdown(element);
            }
        });
        
        // Close on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeDropdown(element);
            }
        });
    }
    
    toggleDropdown(element) {
        const menu = element.querySelector('.dropdown-menu');
        const isOpen = !menu.classList.contains('hidden');
        
        if (isOpen) {
            this.closeDropdown(element);
        } else {
            this.openDropdown(element);
        }
    }
    
    openDropdown(element) {
        const menu = element.querySelector('.dropdown-menu');
        menu.classList.remove('hidden');
        menu.classList.add('show');
        
        // Close other dropdowns
        document.querySelectorAll('[data-dropdown] .dropdown-menu.show').forEach(otherMenu => {
            if (otherMenu !== menu) {
                otherMenu.classList.add('hidden');
                otherMenu.classList.remove('show');
            }
        });
    }
    
    closeDropdown(element) {
        const menu = element.querySelector('.dropdown-menu');
        menu.classList.add('hidden');
        menu.classList.remove('show');
    }
    
    // ===== MODAL COMPONENTS =====
    
    initializeModals() {
        document.querySelectorAll('[data-modal]').forEach(modal => {
            this.initializeModal(modal);
        });
        
        // Global modal triggers
        document.addEventListener('click', (e) => {
            const modalTrigger = e.target.closest('[data-modal-target]');
            if (modalTrigger) {
                e.preventDefault();
                const targetId = modalTrigger.dataset.modalTarget;
                const modal = document.getElementById(targetId);
                if (modal) {
                    this.openModal(modal);
                }
            }
        });
    }
    
    initializeModal(modal) {
        // Close buttons
        modal.querySelectorAll('[data-modal-close]').forEach(closeBtn => {
            closeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.closeModal(modal);
            });
        });
        
        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal(modal);
            }
        });
        
        // Close on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                this.closeModal(modal);
            }
        });
    }
    
    openModal(modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        
        // Trigger show animation
        requestAnimationFrame(() => {
            modal.classList.add('show');
        });
        
        // Focus first input
        const firstInput = modal.querySelector('input, select, textarea, button');
        if (firstInput) {
            firstInput.focus();
        }
    }
    
    closeModal(modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
        
        // Wait for animation before hiding
        setTimeout(() => {
            modal.classList.add('hidden');
        }, 200);
    }
    
    // ===== TABLE COMPONENTS =====
    
    initializeTables() {
        document.querySelectorAll('.table-sortable').forEach(table => {
            this.initializeSortableTable(table);
        });
    }
    
    initializeSortableTable(table) {
        const headers = table.querySelectorAll('th[data-sortable]');
        
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                this.sortTable(table, header);
            });
        });
    }
    
    sortTable(table, header) {
        const column = Array.from(header.parentNode.children).indexOf(header);
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const isAscending = !header.classList.contains('sort-asc');
        
        // Remove sort classes from all headers
        table.querySelectorAll('th').forEach(h => {
            h.classList.remove('sort-asc', 'sort-desc');
        });
        
        // Add sort class to current header
        header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
        
        // Sort rows
        rows.sort((a, b) => {
            const aText = a.children[column]?.textContent?.trim() || '';
            const bText = b.children[column]?.textContent?.trim() || '';
            
            // Try to parse as numbers
            const aNum = parseFloat(aText.replace(/[^\d.-]/g, ''));
            const bNum = parseFloat(bText.replace(/[^\d.-]/g, ''));
            
            let comparison = 0;
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                comparison = aNum - bNum;
            } else {
                comparison = aText.localeCompare(bText);
            }
            
            return isAscending ? comparison : -comparison;
        });
        
        // Reorder rows in DOM
        rows.forEach(row => tbody.appendChild(row));
    }
    
    // ===== FORM ELEMENTS =====
    
    initializeFormElements() {
        // File inputs
        document.querySelectorAll('input[type="file"]').forEach(input => {
            this.initializeFileInput(input);
        });
        
        // Search inputs with debounce
        document.querySelectorAll('.search-input').forEach(input => {
            this.initializeSearchInput(input);
        });
    }
    
    initializeFileInput(input) {
        const label = input.closest('label') || input.nextElementSibling;
        if (label) {
            input.addEventListener('change', () => {
                const fileName = input.files[0]?.name || 'Choose file...';
                const textElement = label.querySelector('.file-text') || label;
                textElement.textContent = fileName;
            });
        }
    }
    
    initializeSearchInput(input) {
        let timeout;
        input.addEventListener('input', (e) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                this.handleSearch(input, e.target.value);
            }, 300);
        });
    }
    
    handleSearch(input, value) {
        const event = new CustomEvent('search', {
            detail: { input, value }
        });
        document.dispatchEvent(event);
    }
    
    // ===== TOOLTIPS =====
    
    initializeTooltips() {
        document.querySelectorAll('[data-tooltip]').forEach(element => {
            this.initializeTooltip(element);
        });
    }
    
    initializeTooltip(element) {
        const tooltipText = element.dataset.tooltip;
        if (!tooltipText) return;
        
        let tooltip = null;
        
        element.addEventListener('mouseenter', () => {
            tooltip = this.createTooltip(tooltipText);
            document.body.appendChild(tooltip);
            this.positionTooltip(tooltip, element);
        });
        
        element.addEventListener('mouseleave', () => {
            if (tooltip) {
                tooltip.remove();
                tooltip = null;
            }
        });
        
        element.addEventListener('mousemove', (e) => {
            if (tooltip) {
                this.positionTooltip(tooltip, element, e);
            }
        });
    }
    
    createTooltip(text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'chart-tooltip show';
        tooltip.textContent = text;
        tooltip.style.position = 'absolute';
        tooltip.style.zIndex = '1000';
        return tooltip;
    }
    
    positionTooltip(tooltip, element, event = null) {
        const rect = element.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        let x, y;
        
        if (event) {
            x = event.clientX;
            y = event.clientY;
        } else {
            x = rect.left + rect.width / 2;
            y = rect.top;
        }
        
        // Adjust for viewport bounds
        if (x + tooltipRect.width > window.innerWidth) {
            x = window.innerWidth - tooltipRect.width - 10;
        }
        if (y - tooltipRect.height < 0) {
            y = rect.bottom + 10;
        } else {
            y = y - tooltipRect.height - 10;
        }
        
        tooltip.style.left = x + 'px';
        tooltip.style.top = y + 'px';
    }
    
    // ===== PROGRESS BARS =====
    
    animateProgress(element, targetValue, duration = 1000) {
        const progressBar = element.querySelector('.progress-bar');
        if (!progressBar) return;
        
        const startValue = 0;
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const currentValue = startValue + (targetValue - startValue) * this.easeOutCubic(progress);
            progressBar.style.width = currentValue + '%';
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }
    
    // ===== LOADING STATES =====
    
    showLoading(element, text = 'Loading...') {
        const loadingHTML = `
            <div class="loading-state flex items-center justify-center py-8">
                <div class="loading-spinner mr-3"></div>
                <span class="text-gray-500">${text}</span>
            </div>
        `;
        
        element.dataset.originalContent = element.innerHTML;
        element.innerHTML = loadingHTML;
    }
    
    hideLoading(element) {
        if (element.dataset.originalContent) {
            element.innerHTML = element.dataset.originalContent;
            delete element.dataset.originalContent;
        }
    }
    
    // ===== ANIMATIONS =====
    
    fadeIn(element, duration = 300) {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        let start = null;
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = (timestamp - start) / duration;
            
            element.style.opacity = Math.min(progress, 1);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    fadeOut(element, duration = 300) {
        let start = null;
        const initialOpacity = parseFloat(getComputedStyle(element).opacity);
        
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = (timestamp - start) / duration;
            
            element.style.opacity = initialOpacity * (1 - Math.min(progress, 1));
            
            if (progress >= 1) {
                element.style.display = 'none';
            } else {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    slideDown(element, duration = 300) {
        element.style.height = '0';
        element.style.overflow = 'hidden';
        element.style.display = 'block';
        
        const fullHeight = element.scrollHeight;
        let start = null;
        
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = (timestamp - start) / duration;
            
            element.style.height = (fullHeight * Math.min(progress, 1)) + 'px';
            
            if (progress >= 1) {
                element.style.height = 'auto';
                element.style.overflow = 'visible';
            } else {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    // ===== CONTENT OBSERVER =====
    
    observeForNewContent() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) { // Element node
                        this.initializeNewContent(node);
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    initializeNewContent(element) {
        // Initialize dropdowns
        if (element.matches('[data-dropdown]') || element.querySelector('[data-dropdown]')) {
            const dropdowns = element.matches('[data-dropdown]') ? [element] : element.querySelectorAll('[data-dropdown]');
            dropdowns.forEach(dropdown => this.initializeDropdown(dropdown));
        }
        
        // Initialize modals
        if (element.matches('[data-modal]') || element.querySelector('[data-modal]')) {
            const modals = element.matches('[data-modal]') ? [element] : element.querySelectorAll('[data-modal]');
            modals.forEach(modal => this.initializeModal(modal));
        }
        
        // Initialize tooltips
        if (element.matches('[data-tooltip]') || element.querySelector('[data-tooltip]')) {
            const tooltips = element.matches('[data-tooltip]') ? [element] : element.querySelectorAll('[data-tooltip]');
            tooltips.forEach(tooltip => this.initializeTooltip(tooltip));
        }
    }
    
    // ===== UTILITY METHODS =====
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    // ===== PUBLIC API =====
    
    // Expose methods for external use
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) this.openModal(modal);
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) this.closeModal(modal);
    }
    
    showToast(message, type = 'info', duration = 5000) {
        const toast = this.createToast(message, type);
        document.body.appendChild(toast);
        
        // Show toast
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // Auto remove
        setTimeout(() => {
            this.removeToast(toast);
        }, duration);
        
        return toast;
    }
    
    createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span>${message}</span>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Position toast
        const existingToasts = document.querySelectorAll('.toast');
        const offset = existingToasts.length * 80;
        toast.style.top = (20 + offset) + 'px';
        
        return toast;
    }
    
    removeToast(toast) {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }
}

// Initialize components when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.MABComponents = new MABComponents();
    });
} else {
    window.MABComponents = new MABComponents();
}

// Extend MAB app with component methods
if (window.MAB) {
    window.MAB.components = window.MABComponents;
    
    // Add component methods to MAB
    window.MAB.openModal = function(modalId) {
        return window.MABComponents.openModal(modalId);
    };
    
    window.MAB.closeModal = function(modalId) {
        return window.MABComponents.closeModal(modalId);
    };
    
    window.MAB.showToast = function(message, type, duration) {
        return window.MABComponents.showToast(message, type, duration);
    };
    
    window.MAB.showLoading = function(element, text) {
        return window.MABComponents.showLoading(element, text);
    };
    
    window.MAB.hideLoading = function(element) {
        return window.MABComponents.hideLoading(element);
    };
}
