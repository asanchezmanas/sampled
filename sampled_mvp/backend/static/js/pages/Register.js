// backend/static/js/pages/Register.js

class RegisterPage {
    constructor() {
        this.app = window.MAB;
        this.form = null;
        this.isSubmitting = false;
        this.passwordStrength = 0;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupPasswordToggle();
        this.setupPasswordStrength();
        this.setupFormValidation();
        
        console.log('Register page initialized');
    }
    
    setupEventListeners() {
        // Form submission
        const form = document.getElementById('register-form');
        if (form) {
            this.form = form;
            form.addEventListener('submit', this.handleSubmit.bind(this));
        }
        
        // Real-time validation
        const fields = ['name', 'email', 'password', 'confirm-password'];
        fields.forEach(fieldName => {
            const input = document.getElementById(fieldName);
            if (input) {
                input.addEventListener('blur', () => this.validateField(fieldName));
                input.addEventListener('input', () => this.clearFieldError(fieldName));
            }
        });
        
        // Password confirmation
        const confirmPasswordInput = document.getElementById('confirm-password');
        if (confirmPasswordInput) {
            confirmPasswordInput.addEventListener('input', () => this.validatePasswordMatch());
        }
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
    
    setupPasswordStrength() {
        const passwordInput = document.getElementById('password');
        const strengthContainer = document.getElementById('password-strength');
        
        if (passwordInput && strengthContainer) {
            passwordInput.addEventListener('input', () => {
                const password = passwordInput.value;
                
                if (password.length === 0) {
                    strengthContainer.classList.add('hidden');
                    return;
                }
                
                strengthContainer.classList.remove('hidden');
                this.updatePasswordStrength(password);
            });
        }
    }
    
    updatePasswordStrength(password) {
        const strength = this.calculatePasswordStrength(password);
        this.passwordStrength = strength;
        
        const bars = [
            document.getElementById('strength-bar-1'),
            document.getElementById('strength-bar-2'),
            document.getElementById('strength-bar-3'),
            document.getElementById('strength-bar-4')
        ];
        
        const strengthText = document.getElementById('strength-text');
        
        // Reset all bars
        bars.forEach(bar => {
            if (bar) bar.className = 'h-full rounded-full transition-colors';
        });
        
        let message = '';
        let textClass = '';
        
        if (strength >= 4) {
            bars.forEach(bar => bar && bar.classList.add('bg-success-500'));
            message = 'Very strong password';
            textClass = 'text-success-600';
        } else if (strength >= 3) {
            bars.slice(0, 3).forEach(bar => bar && bar.classList.add('bg-success-400'));
            message = 'Strong password';
            textClass = 'text-success-600';
        } else if (strength >= 2) {
            bars.slice(0, 2).forEach(bar => bar && bar.classList.add('bg-warning-500'));
            message = 'Medium password';
            textClass = 'text-warning-600';
        } else if (strength >= 1) {
            bars[0] && bars[0].classList.add('bg-error-500');
            message = 'Weak password';
            textClass = 'text-error-600';
        } else {
            message = 'Very weak password';
            textClass = 'text-error-600';
        }
        
        if (strengthText) {
            strengthText.textContent = message;
            strengthText.className = `text-xs mt-1 font-medium ${textClass}`;
        }
    }
    
    calculatePasswordStrength(password) {
        let score = 0;
        
        // Length check
        if (password.length >= 8) score++;
        if (password.length >= 12) score++;
        
        // Character diversity
        if (/[a-z]/.test(password)) score++;
        if (/[A-Z]/.test(password)) score++;
        if (/[0-9]/.test(password)) score++;
        if (/[^A-Za-z0-9]/.test(password)) score++;
        
        // Bonus for very long passwords
        if (password.length >= 16) score++;
        
        return Math.min(score, 4);
    }
    
    setupFormValidation() {
        const inputs = this.form.querySelectorAll('input[required]');
        inputs.forEach(input => {
            input.addEventListener('invalid', (e) => {
                e.preventDefault();
                this.showFieldError(input.name || input.id, this.getValidationMessage(input));
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
            const registerData = {
                name: formData.get('name'),
                email: formData.get('email'),
                password: formData.get('password'),
                company: formData.get('company') || '',
                marketing: formData.get('marketing') === 'on'
            };
            
            const response = await this.app.api.post('/auth/register', registerData);
            
            if (response.success) {
                this.handleRegisterSuccess(response.data);
            } else {
                this.handleRegisterError(response.detail || 'Registration failed');
            }
            
        } catch (error) {
            this.handleRegisterError(error.message || 'Network error occurred');
        } finally {
            this.isSubmitting = false;
            this.setLoadingState(false);
        }
    }
    
    validateForm() {
        let isValid = true;
        
        // Name validation
        if (!this.validateField('name')) {
            isValid = false;
        }
        
        // Email validation
        if (!this.validateField('email')) {
            isValid = false;
        }
        
        // Password validation
        if (!this.validateField('password')) {
            isValid = false;
        }
        
        // Confirm password validation
        if (!this.validateField('confirm-password')) {
            isValid = false;
        }
        
        // Password match validation
        if (!this.validatePasswordMatch()) {
            isValid = false;
        }
        
        // Terms validation
        if (!this.validateField('terms')) {
            isValid = false;
        }
        
        return isValid;
    }
    
    validateField(fieldName) {
        const input = document.getElementById(fieldName);
        if (!input) return true;
        
        const value = input.value.trim();
        let errorMessage = '';
        
        switch (fieldName) {
            case 'name':
                if (!value) {
                    errorMessage = 'Full name is required';
                } else if (value.length < 2) {
                    errorMessage = 'Name must be at least 2 characters';
                }
                break;
                
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
                } else if (value.length < 8) {
                    errorMessage = 'Password must be at least 8 characters';
                } else if (this.passwordStrength < 2) {
                    errorMessage = 'Please choose a stronger password';
                }
                break;
                
            case 'confirm-password':
                if (!value) {
                    errorMessage = 'Please confirm your password';
                }
                break;
                
            case 'terms':
                if (!input.checked) {
                    errorMessage = 'You must agree to the Terms of Service';
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
    
    validatePasswordMatch() {
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        
        if (confirmPassword && password !== confirmPassword) {
            this.showFieldError('confirm-password', 'Passwords do not match');
            return false;
        } else {
            this.clearFieldError('confirm-password');
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
            // Special handling for checkbox
            if (input.type === 'checkbox') {
                input.parentElement.parentElement.classList.add('text-error-600');
            } else {
                input.classList.add('border-error-500', 'focus:border-error-500', 'focus:ring-error-500');
                input.classList.remove('border-gray-300', 'focus:border-brand-500', 'focus:ring-brand-500');
            }
            
            errorElement.textContent = message;
            errorElement.classList.remove('hidden');
        }
    }
    
    clearFieldError(fieldName) {
        const input = document.getElementById(fieldName);
        const errorElement = document.getElementById(`${fieldName}-error`);
        
        if (input && errorElement) {
            // Special handling for checkbox
            if (input.type === 'checkbox') {
                input.parentElement.parentElement.classList.remove('text-error-600');
            } else {
                input.classList.remove('border-error-500', 'focus:border-error-500', 'focus:ring-error-500');
                input.classList.add('border-gray-300', 'focus:border-brand-500', 'focus:ring-brand-500');
            }
            
            errorElement.classList.add('hidden');
        }
    }
    
    clearAllErrors() {
        const fields = ['name', 'email', 'password', 'confirm-password', 'terms'];
        fields.forEach(field => this.clearFieldError(field));
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
        const button = document.getElementById('register-button');
        const text = document.getElementById('register-text');
        const spinner = document.getElementById('register-loading');
        
        if (button && text && spinner) {
            button.disabled = loading;
            
            if (loading) {
                text.textContent = 'Creating account...';
                spinner.classList.remove('hidden');
            } else {
                text.textContent = 'Create account';
                spinner.classList.add('hidden');
            }
        }
    }
    
    handleRegisterSuccess(data) {
        // Store token
        localStorage.setItem('mab_token', data.token);
        
        // Store user info
        if (data.user) {
            this.app.state.set('user', data.user);
        }
        
        // Show success message
        this.showTemporaryMessage('Account created successfully! Redirecting...', 'success');
        
        // Redirect after short delay
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 1500);
    }
    
    handleRegisterError(message) {
        // Show error in form
        this.showFormError(message);
        
        // Focus on first field with error or first field
        this.focusFirstEmptyField();
        
        // Special handling for common errors
        if (message.toLowerCase().includes('email')) {
            const emailInput = document.getElementById('email');
            if (emailInput) emailInput.focus();
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
    
    focusFirstEmptyField() {
        const inputs = this.form.querySelectorAll('input[required]');
        for (const input of inputs) {
            if (!input.value.trim() && input.type !== 'checkbox') {
                input.focus();
                break;
            }
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
    
    destroy() {
        console.log('Register page destroyed');
    }
}

// Make available globally
window.RegisterPage = RegisterPage;
