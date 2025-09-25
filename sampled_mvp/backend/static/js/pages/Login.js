// backend/static/js/pages/Login.js

class LoginPage {
    constructor() {
        this.app = window.MAB;
        this.form = null;
        this.isSubmitting = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupPasswordToggle();
        this.setupFormValidation();
        
        console.log('Login page initialized');
    }
    
    setupEventListeners() {
        // Form submission
        const form = document.getElementById('login-form');
        if (form) {
            this.form = form;
            form.addEventListener('submit', this.handleSubmit.bind(this));
        }
        
        // Real-time validation
        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');
        
        if (emailInput) {
            emailInput.addEventListener('blur', () => this.validateField('email'));
            emailInput.addEventListener('input', () => this.clearFieldError('email'));
        }
        
        if (passwordInput) {
            passwordInput.addEventListener('blur', () => this.validateField('password'));
            passwordInput.addEventListener('input', () => this.clearFieldError('password'));
        }
        
        // Enter key handling
        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !this.isSubmitting) {
                form.requestSubmit();
            }
        });
    }
    
    setupPasswordToggle() {
        const toggleButton = document.getElementById('toggle-password');
        const passwordInput = document.getElementById('password');
        const eyeClosed = document.getElementById('eye-closed');
        const eyeOpen = document.getElementById('eye-open');
        
        if (toggleButton && passwordInput && eyeClosed && eyeOpen) {
            toggleButton.addEventListener('click', () => {
                const isPassword = passwordInput.type === 'password';
                
                passwordInput.type = isPassword ? 'text' : 'password';
                eyeClosed.classList.toggle('hidden', isPassword);
                eyeOpen.classList.toggle('hidden', !isPassword);
            });
        }
    }
    
    setupFormValidation() {
        // Add live validation styles
        const inputs = this.form.querySelectorAll('input[required]');
        inputs.forEach(input => {
            input.addEventListener('invalid', (e) => {
                e.preventDefault();
                this.showFieldError(input.name, this.getValidationMessage(input));
            });
        });
    }
    
    async handleSubmit(event) {
        event.preventDefault();
        
        if (this.isSubmitting) return;
        
        // Clear previous errors
        this.clearAllErrors();
        
        // Validate form
        if (!this.validateForm()) {
            return;
        }
        
        this.isSubmitting = true;
        this.setLoadingState(true);
        
        try {
            const formData = new FormData(this.form);
            const loginData = {
                email: formData.get('email'),
                password: formData.get('password'),
                remember_me: formData.get('remember_me') === 'on'
            };
            
            const response = await this.app.api.post('/auth/login', loginData);
            
            if (response.success) {
                this.handleLoginSuccess(response.data);
            } else {
                this.handleLoginError(response.detail || 'Login failed');
            }
            
        } catch (error) {
            this.handleLoginError(error.message || 'Network error occurred');
        } finally {
            this.isSubmitting = false;
            this.setLoadingState(false);
        }
    }
    
    validateForm() {
        let isValid = true;
        
        // Email validation
        if (!this.validateField('email')) {
            isValid = false;
        }
        
        // Password validation
        if (!this.validateField('password')) {
            isValid = false;
        }
        
        return isValid;
    }
    
    validateField(fieldName) {
        const input = document.getElementById(fieldName);
        const value = input.value.trim();
        
        let errorMessage = '';
        
        switch (fieldName) {
            case 'email':
                if (!value) {
                    errorMessage = 'Email is required';
                } else if (!this.isValidEmail(value)) {
                    errorMessage = 'Please enter a valid email address';
                }
                break;
                
            case 'password':
                if (!value) {
                    errorMessage = 'Password is required';
                } else if (value.length < 6) {
                    errorMessage = 'Password must be at least 6 characters';
                }
                break;
        }
        
        if (errorMessage) {
            this.showFieldError(fieldName, errorMessage);
            return false;
        } else {
            this.clearFieldError(fieldName);
            return true;
        }
    }
    
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    showFieldError(fieldName, message) {
        const input = document.getElementById(fieldName);
        const errorElement = document.getElementById(`${fieldName}-error`);
        
        if (input && errorElement) {
            input.classList.add('border-error-500', 'focus:border-error-500', 'focus:ring-error-500');
            input.classList.remove('border-gray-300', 'focus:border-brand-500', 'focus:ring-brand-500');
            
            errorElement.textContent = message;
            errorElement.classList.remove('hidden');
        }
    }
    
    clearFieldError(fieldName) {
        const input = document.getElementById(fieldName);
        const errorElement = document.getElementById(`${fieldName}-error`);
        
        if (input && errorElement) {
            input.classList.remove('border-error-500', 'focus:border-error-500', 'focus:ring-error-500');
            input.classList.add('border-gray-300', 'focus:border-brand-500', 'focus:ring-brand-500');
            
            errorElement.classList.add('hidden');
        }
    }
    
    clearAllErrors() {
        this.clearFieldError('email');
        this.clearFieldError('password');
        this.hideFormError();
    }
    
    showFormError(message) {
        const errorElement = document.getElementById('form-error');
        const errorMessage = document.getElementById('form-error-message');
        
        if (errorElement && errorMessage) {
            errorMessage.textContent = message;
            errorElement.classList.remove('hidden');
        }
    }
    
    hideFormError() {
        const errorElement = document.getElementById('form-error');
        if (errorElement) {
            errorElement.classList.add('hidden');
        }
    }
    
    setLoadingState(loading) {
        const button = document.getElementById('login-button');
        const text = document.getElementById('login-text');
        const spinner = document.getElementById('login-loading');
        
        if (button && text && spinner) {
            button.disabled = loading;
            
            if (loading) {
                text.textContent = 'Signing in...';
                spinner.classList.remove('hidden');
            } else {
                text.textContent = 'Sign in';
                spinner.classList.add('hidden');
            }
        }
    }
    
    handleLoginSuccess(data) {
        // Store token
        localStorage.setItem('mab_token', data.token);
        
        // Store user info
        if (data.user) {
            this.app.state.set('user', data.user);
        }
        
        // Show success message briefly
        const successMessage = 'Welcome back! Redirecting...';
        this.showTemporaryMessage(successMessage, 'success');
        
        // Redirect after short delay
        setTimeout(() => {
            const returnUrl = new URLSearchParams(window.location.search).get('return') || '/dashboard';
            window.location.href = returnUrl;
        }, 1000);
    }
    
    handleLoginError(message) {
        // Show error in form
        this.showFormError(message);
        
        // Focus on email field for retry
        const emailInput = document.getElementById('email');
        if (emailInput) {
            emailInput.focus();
        }
        
        // Clear password field if credentials error
        if (message.toLowerCase().includes('password') || message.toLowerCase().includes('invalid')) {
            const passwordInput = document.getElementById('password');
            if (passwordInput) {
                passwordInput.value = '';
                passwordInput.focus();
            }
        }
    }
    
    showTemporaryMessage(message, type = 'success') {
        const formError = document.getElementById('form-error');
        const formErrorMessage = document.getElementById('form-error-message');
        
        if (formError && formErrorMessage) {
            // Change styling based on type
            if (type === 'success') {
                formError.className = 'p-3 rounded-lg bg-success-50 border border-success-200';
                formErrorMessage.className = 'text-sm text-success-800';
            }
            
            formErrorMessage.textContent = message;
            formError.classList.remove('hidden');
        }
    }
    
    getValidationMessage(input) {
        if (input.validity.valueMissing) {
            return `${input.name.charAt(0).toUpperCase() + input.name.slice(1)} is required`;
        } else if (input.validity.typeMismatch) {
            return `Please enter a valid ${input.type}`;
        } else if (input.validity.tooShort) {
            return `${input.name.charAt(0).toUpperCase() + input.name.slice(1)} must be at least ${input.minLength} characters`;
        }
        return 'Please check this field';
    }
    
    // Auto-focus first empty field
    focusFirstEmptyField() {
        const inputs = this.form.querySelectorAll('input[required]');
        for (const input of inputs) {
            if (!input.value.trim()) {
                input.focus();
                break;
            }
        }
    }
    
    // Handle social login (placeholder for future)
    handleSocialLogin(provider) {
        console.log(`Social login with ${provider} not implemented yet`);
    }
    
    destroy() {
        // Cleanup if needed
        console.log('Login page destroyed');
    }
}

// Make available globally
window.LoginPage = LoginPage;
