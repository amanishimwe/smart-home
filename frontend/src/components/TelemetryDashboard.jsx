import { useState, useEffect } from 'react';
import telemetryService from '../services/telemetry';

const TelemetryDashboard = ({ user, onLogout }) => {
  const [telemetryData, setTelemetryData] = useState([]);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedDevice, setSelectedDevice] = useState('all');
  const [refreshInterval, setRefreshInterval] = useState(null);

  // Fetch telemetry data from the service
  const fetchTelemetryData = async () => {
    try {
      setLoading(true);
      const data = await telemetryService.getTelemetryData(selectedDevice === 'all' ? null : selectedDevice, 100);
      setTelemetryData(data);
      
      // Extract unique devices from telemetry data
      const uniqueDevices = [...new Set(data.map(item => item.device_id))];
      const deviceList = uniqueDevices.map(deviceId => ({
        id: deviceId,
        name: `Device ${deviceId.slice(0, 8)}...`,
        type: 'Smart Device',
        status: 'active'
      }));
      setDevices(deviceList);
      
    } catch (err) {
      setError('Failed to fetch telemetry data: ' + err.message);
      console.error('Telemetry fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch devices summary
  const fetchDevicesSummary = async () => {
    try {
      const summary = await telemetryService.getDevicesSummary();
      if (summary && summary.devices) {
        setDevices(summary.devices);
      }
    } catch (err) {
      console.error('Devices summary error:', err);
      // Fallback to extracting from telemetry data
    }
  };

  // Fetch user devices
  const fetchUserDevices = async () => {
    try {
      const userDevices = await telemetryService.getUserDevices();
      if (userDevices && userDevices.length > 0) {
        setDevices(userDevices);
      }
    } catch (err) {
      console.error('User devices error:', err);
      // Fallback to devices summary
      fetchDevicesSummary();
    }
  };

  // Initial data fetch
  useEffect(() => {
    fetchTelemetryData();
    fetchUserDevices(); // Try user devices first
    
    // Set up auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchTelemetryData();
    }, 30000);
    
    setRefreshInterval(interval);
    
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [selectedDevice]);

  // Manual refresh function
  const handleRefresh = () => {
    fetchTelemetryData();
  };

  // Calculate statistics from telemetry data
  const getTotalEnergyUsage = () => {
    return telemetryData.reduce((total, data) => total + (data.energy_usage || 0), 0).toFixed(3);
  };

  const getAverageTemperature = () => {
    const temps = telemetryData.map(data => data.temperature).filter(temp => temp !== null && temp !== undefined);
    return temps.length > 0 ? (temps.reduce((a, b) => a + b, 0) / temps.length).toFixed(1) : 'N/A';
  };

  const getActiveDevices = () => {
    return devices.length;
  };

  const getLatestTimestamp = () => {
    if (telemetryData.length > 0) {
      return new Date(telemetryData[0].timestamp).toLocaleString();
    }
    return 'No data';
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  if (loading && telemetryData.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-r from-cyan-500 from-10% via-indigo-500 via-50% to-sky-500 to-100% flex items-center justify-center">
        <div className="text-white text-2xl">Loading telemetry data...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-r from-cyan-500 from-10% via-indigo-500 via-50% to-sky-500 to-100% p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-2xl shadow-2xl p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Smart Home Telemetry Dashboard</h1>
              <p className="text-gray-600">Welcome back, {user.username}!</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleRefresh}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md transition-colors"
              >
                🔄 Refresh
              </button>
              <button
                onClick={onLogout}
                className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-md transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            <strong>Error:</strong> {error}
            <button 
              onClick={() => setError('')} 
              className="float-right text-red-700 hover:text-red-900"
            >
              ×
            </button>
          </div>
        )}

        {/* Device Filter */}
        <div className="bg-white rounded-2xl shadow-2xl p-6 mb-6">
          <div className="flex items-center gap-4">
            <label className="text-lg font-medium text-gray-700">Filter by Device:</label>
            <select
              value={selectedDevice}
              onChange={(e) => setSelectedDevice(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Devices</option>
              {devices.map((device) => (
                <option key={device.id} value={device.id}>
                  {device.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-blue-100">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Energy Usage</p>
                <p className="text-2xl font-bold text-gray-900">{getTotalEnergyUsage()} kWh</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-green-100">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Devices</p>
                <p className="text-2xl font-bold text-gray-900">{getActiveDevices()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-yellow-100">
                <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg Temperature</p>
                <p className="text-2xl font-bold text-gray-900">{getAverageTemperature()}°C</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-purple-100">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Last Update</p>
                <p className="text-lg font-bold text-gray-900">{getLatestTimestamp()}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Device List */}
        <div className="bg-white rounded-2xl shadow-2xl p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Connected Devices</h2>
          {devices.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {devices.map((device) => (
                <div key={device.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900">{device.name}</h3>
                      <p className="text-sm text-gray-600">{device.type}</p>
                    </div>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                      device.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {device.status}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No devices found</p>
          )}
        </div>

        {/* Telemetry Data Table */}
        <div className="bg-white rounded-2xl shadow-2xl p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Recent Telemetry Data</h2>
          {telemetryData.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Device</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Energy (kWh)</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Voltage (V)</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current (A)</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Temperature (°C)</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {telemetryData.map((data) => (
                    <tr key={data.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {data.device_id.slice(0, 8)}...
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{data.energy_usage || 'N/A'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{data.voltage || 'N/A'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{data.current || 'N/A'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{data.temperature || 'N/A'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatTimestamp(data.timestamp)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No telemetry data available</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default TelemetryDashboard;
