// API Configuration
const API_BASE_URL = (() => {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:5000/api';
    }
    // Always use the main API domain, not the admin subdomain
    return 'https://efishery.acerkecil.my.id/api';
})();


// Debug: Log the API URL being used
console.log('Current hostname:', window.location.hostname);
console.log('Current origin:', window.location.origin);
console.log('API_BASE_URL:', API_BASE_URL);

// Authentication utilities
class Auth {
    static setToken(token) {
        localStorage.setItem('admin_token', token);
    }

    static getToken() {
        return localStorage.getItem('admin_token');
    }

    static removeToken() {
        localStorage.removeItem('admin_token');
    }

    static isAuthenticated() {
        return !!this.getToken();
    }

    static redirectToLogin() {
        window.location.href = 'index.html';
    }

    static redirectToDashboard() {
        window.location.href = 'dashboard.html';
    }

    static getCurrentUserPhone() {
        // For admin, we'll use a fixed phone number or get it from token
        // This is a simplified approach - in production you'd decode the JWT
        return 'admin'; // or extract from JWT token
    }
}

// API utilities
class API {
    static getBaseUrl() {
        // Always ensure we use the correct API base URL
        return window.API_BASE_URL || API_BASE_URL || 'https://efishery.acerkecil.my.id/api';
    }

    static async request(endpoint, options = {}) {
        const token = Auth.getToken();
        const baseUrl = this.getBaseUrl();
        
        console.log('Making API request to:', `${baseUrl}${endpoint}`);
        
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` })
            },
            ...options
        };

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(`${baseUrl}${endpoint}`, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            console.error('Request URL:', `${baseUrl}${endpoint}`);
            throw error;
        }
    }

    static async get(endpoint) {
        return this.request(endpoint);
    }

    static async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: data
        });
    }

    static async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: data
        });
    }

    static async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }
}

// Modal utilities
class Modal {
    static show(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            // Set display none first to reset any previous state
            modal.style.display = 'none';
            // Force a reflow
            modal.offsetHeight;
            // Then set to flex
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    }

    static hide(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    }

    static showLoading() {
        this.show('loadingModal');
    }

    static hideLoading() {
        this.hide('loadingModal');
    }
}

// Utility functions
function showError(message, elementId = 'loginError') {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
}

function hideError(elementId = 'loginError') {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.style.display = 'none';
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('id-ID', {
        style: 'currency',
        currency: 'IDR'
    }).format(amount);
}

// Login functionality
document.addEventListener('DOMContentLoaded', function() {
    // Check if already authenticated
    if (Auth.isAuthenticated() && window.location.pathname.includes('index.html')) {
        Auth.redirectToDashboard();
        return;
    }

    // Login form handler
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const phone = document.getElementById('phone').value;
            const password = document.getElementById('password').value;

            if (!phone || !password) {
                showError('Nomor HP dan password harus diisi');
                return;
            }

            try {
                Modal.showLoading();
                hideError();

                const response = await API.post('/login', {
                    nomor_hp: phone,
                    password: password
                });

                if (response.access_token) {
                    Auth.setToken(response.access_token);
                    Auth.redirectToDashboard();
                } else {
                    throw new Error('Token tidak ditemukan dalam response');
                }
            } catch (error) {
                showError(error.message || 'Login gagal. Periksa nomor HP dan password Anda.');
            } finally {
                Modal.hideLoading();
            }
        });
    }

    // Close modal when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            Modal.hide(e.target.id);
        }
    });

    // Close modal with close button
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal-close')) {
            const modal = e.target.closest('.modal');
            if (modal) {
                Modal.hide(modal.id);
            }
        }
    });
});

// Export for use in other files
window.Auth = Auth;
window.API = API;
window.Modal = Modal;
window.showError = showError;
window.hideError = hideError;
window.formatDate = formatDate;
window.formatCurrency = formatCurrency;
window.API_BASE_URL = API_BASE_URL;
