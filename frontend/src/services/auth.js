// src/services/auth.js
const API_BASE_URL = 'http://localhost:8001'; // API Gateway

class AuthService {
    constructor() {
        this.token = localStorage.getItem('token');
        this.user = JSON.parse(localStorage.getItem('user') || 'null');
    }

    // Set authorization header
    getAuthHeaders() {
        return this.token ? {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        } : {
            'Content-Type': 'application/json'
        };
    }

    // Login user
    async login(username, password, rememberMe = false) {
        try {
            const response = await fetch(`${API_BASE_URL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username,
                    password,
                    remember_me: rememberMe
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Login failed');
            }

            const data = await response.json();

            // Store token and user info
            this.token = data.access_token;
            this.user = data.user;

            localStorage.setItem('token', this.token);
            localStorage.setItem('user', JSON.stringify(this.user));

            return data;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    // Register user
    async register(username, email, password, role = 'user') {
        try {
            const response = await fetch(`${API_BASE_URL}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username,
                    email,
                    password,
                    role
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Registration failed');
            }

            const data = await response.json();

            // Store token and user info
            this.token = data.access_token;
            this.user = data.user;

            localStorage.setItem('token', this.token);
            localStorage.setItem('user', JSON.stringify(this.user));

            return data;
        } catch (error) {
            console.error('Registration error:', error);
            throw error;
        }
    }

    // Logout user
    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
    }

    // Get current user info
    async getCurrentUser() {
        if (!this.token) {
            throw new Error('No token found');
        }

        try {
            const response = await fetch(`${API_BASE_URL}/users/me`, {
                method: 'GET',
                headers: this.getAuthHeaders(),
            });

            if (!response.ok) {
                if (response.status === 401) {
                    this.logout(); // Token expired
                    throw new Error('Session expired');
                }
                throw new Error('Failed to get user info');
            }

            const userData = await response.json();
            this.user = userData;
            localStorage.setItem('user', JSON.stringify(this.user));

            return userData;
        } catch (error) {
            console.error('Get user error:', error);
            throw error;
        }
    }

    // Check if user is authenticated
    isAuthenticated() {
        return !!this.token;
    }

    // Check if user has specific role
    hasRole(role) {
        return this.user && this.user.role === role;
    }

    // Check if user is admin
    isAdmin() {
        return this.hasRole('admin');
    }

    // Get user info
    getUser() {
        return this.user;
    }

    // Make authenticated API calls
    async authenticatedFetch(url, options = {}) {
        if (!this.token) {
            throw new Error('No authentication token');
        }

        const response = await fetch(`${API_BASE_URL}${url}`, {
            ...options,
            headers: {
                ...this.getAuthHeaders(),
                ...options.headers,
            },
        });

        if (response.status === 401) {
            this.logout();
            throw new Error('Session expired');
        }

        return response;
    }

    // Get user profile
    async getUserProfile(userId) {
        try {
            const response = await this.authenticatedFetch(`/users/profile/${userId}`);
            return await response.json();
        } catch (error) {
            console.error('Get profile error:', error);
            throw error;
        }
    }

    // Update user profile
    async updateUserProfile(userId, profileData) {
        try {
            const response = await this.authenticatedFetch(`/users/profile/${userId}`, {
                method: 'PUT',
                body: JSON.stringify(profileData)
            });
            return await response.json();
        } catch (error) {
            console.error('Update profile error:', error);
            throw error;
        }
    }

    // Check service health
    async checkHealth() {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            return await response.json();
        } catch (error) {
            console.error('Health check error:', error);
            throw error;
        }
    }
}

// Create and export singleton instance
const authService = new AuthService();
export default authService;