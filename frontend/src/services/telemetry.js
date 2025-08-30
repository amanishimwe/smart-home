// src/services/telemetry.js
const API_BASE_URL = 'http://localhost:8003'; // Telemetry service

class TelemetryService {
    constructor() {
        this.token = localStorage.getItem('token');
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

    // Get telemetry data
    async getTelemetryData(deviceId = null, limit = 50) {
        try {
            let url = `${API_BASE_URL}/telemetry?limit=${limit}`;
            if (deviceId) {
                url += `&device_id=${deviceId}`;
            }

            const response = await fetch(url, {
                method: 'GET',
                headers: this.getAuthHeaders(),
            });

            if (!response.ok) {
                throw new Error('Failed to fetch telemetry data');
            }

            return await response.json();
        } catch (error) {
            console.error('Get telemetry error:', error);
            throw error;
        }
    }

    // Create telemetry data point
    async createTelemetryData(telemetryData) {
        try {
            const response = await fetch(`${API_BASE_URL}/telemetry`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(telemetryData),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create telemetry data');
            }

            return await response.json();
        } catch (error) {
            console.error('Create telemetry error:', error);
            throw error;
        }
    }

    // Get device analytics
    async getDeviceAnalytics(deviceId) {
        try {
            const response = await fetch(`${API_BASE_URL}/telemetry/${deviceId}/analytics`, {
                method: 'GET',
                headers: this.getAuthHeaders(),
            });

            if (!response.ok) {
                throw new Error('Failed to fetch device analytics');
            }

            return await response.json();
        } catch (error) {
            console.error('Get analytics error:', error);
            throw error;
        }
    }

    // Get device health
    async getDeviceHealth(deviceId) {
        try {
            const response = await fetch(`${API_BASE_URL}/telemetry/${deviceId}/health`, {
                method: 'GET',
                headers: this.getAuthHeaders(),
            });

            if (!response.ok) {
                throw new Error('Failed to fetch device health');
            }

            return await response.json();
        } catch (error) {
            console.error('Get health error:', error);
            throw error;
        }
    }

    // Get devices summary
    async getDevicesSummary() {
        try {
            const response = await fetch(`${API_BASE_URL}/telemetry/devices/summary`, {
                method: 'GET',
                headers: this.getAuthHeaders(),
            });

            if (!response.ok) {
                throw new Error('Failed to fetch devices summary');
            }

            return await response.json();
        } catch (error) {
            console.error('Get summary error:', error);
            throw error;
        }
    }

    // Get user devices
    async getUserDevices() {
        try {
            const response = await fetch(`${API_BASE_URL}/devices`, {
                method: 'GET',
                headers: this.getAuthHeaders(),
            });

            if (!response.ok) {
                throw new Error('Failed to fetch user devices');
            }

            return await response.json();
        } catch (error) {
            console.error('Get user devices error:', error);
            throw error;
        }
    }

    // Create user device
    async createUserDevice(deviceData) {
        try {
            const response = await fetch(`${API_BASE_URL}/devices`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(deviceData),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create device');
            }

            return await response.json();
        } catch (error) {
            console.error('Create device error:', error);
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
const telemetryService = new TelemetryService();
export default telemetryService;
