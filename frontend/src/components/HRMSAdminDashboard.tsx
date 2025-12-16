import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

interface ImportLog {
  id: number;
  import_type: string;
  import_timestamp: string;
  records_processed: number;
  records_created: number;
  records_updated: number;
  records_failed: number;
  status: string;
  error_details: string | null;
}

interface ScheduleConfig {
  import_type: string;
  interval: string;
  enabled: boolean;
  last_run: string | null;
  next_run: string | null;
}

interface HealthStatus {
  status: string;
  hrms_url: string;
  timestamp: string;
}

export const HRMSAdminDashboard: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [importLogs, setImportLogs] = useState<ImportLog[]>([]);
  const [schedules, setSchedules] = useState<ScheduleConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [healthRes] = await Promise.all([
        api.get('/api/admin/hrms/health').catch(() => ({ data: null })),
      ]);
      
      if (healthRes.data) {
        setHealth(healthRes.data);
      }
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load HRMS data');
    } finally {
      setLoading(false);
    }
  };

  const handleSyncEmployees = async () => {
    try {
      setSyncing(true);
      setError(null);
      setSuccessMessage(null);
      
      const response = await api.post('/api/admin/hrms/sync/employees');
      
      setSuccessMessage(
        `Sync completed: ${response.data.stats.created} created, ${response.data.stats.updated} updated`
      );
      await fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  const handleSyncWithUsers = async () => {
    try {
      setSyncing(true);
      setError(null);
      setSuccessMessage(null);
      
      const response = await api.post('/api/admin/hrms/sync/employees-with-users');
      
      setSuccessMessage(
        `Sync completed: ${response.data.stats.employees_created} employees, ${response.data.stats.users_created} users created`
      );
      await fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  const handleSetupTestAccounts = async () => {
    try {
      setSyncing(true);
      setError(null);
      setSuccessMessage(null);
      
      const response = await api.post('/api/admin/hrms/setup-test-accounts');
      
      const accounts = response.data.accounts || [];
      const accountList = accounts.map((a: any) => `${a.email} (${a.user_action})`).join(', ');
      
      setSuccessMessage(
        `Test accounts setup complete! Password: ${response.data.default_password}\n\nAccounts: ${accountList}`
      );
      await fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Setup failed');
    } finally {
      setSyncing(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'success':
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'unhealthy':
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'partial':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          HRMS Integration Dashboard
        </h2>
        
        {/* Health Status */}
        {health && (
          <div className="flex items-center gap-4 mb-4">
            <span className="text-sm text-gray-600">HRMS Status:</span>
            <span
              className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                health.status
              )}`}
            >
              {health.status}
            </span>
            <span className="text-xs text-gray-400">{health.hrms_url}</span>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-4">
          <button
            onClick={handleSyncEmployees}
            disabled={syncing}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            {syncing && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            )}
            Sync Employees
          </button>
          <button
            onClick={handleSyncWithUsers}
            disabled={syncing}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
          >
            {syncing && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            )}
            Sync with User Creation
          </button>
          <button
            onClick={handleSetupTestAccounts}
            disabled={syncing}
            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
          >
            {syncing && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            )}
            Setup Test Accounts (LM, DM, Employee)
          </button>
          <button
            onClick={fetchData}
            disabled={loading}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Messages */}
      {successMessage && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-700">
          {successMessage}
        </div>
      )}
      
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {/* Import Statistics */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Import Statistics
        </h3>
        
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <p className="text-sm text-blue-600">Total Processed</p>
            <p className="text-2xl font-bold text-blue-900">
              {importLogs.reduce((sum, l) => sum + l.records_processed, 0)}
            </p>
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <p className="text-sm text-green-600">Created</p>
            <p className="text-2xl font-bold text-green-900">
              {importLogs.reduce((sum, l) => sum + l.records_created, 0)}
            </p>
          </div>
          <div className="bg-yellow-50 rounded-lg p-4">
            <p className="text-sm text-yellow-600">Updated</p>
            <p className="text-2xl font-bold text-yellow-900">
              {importLogs.reduce((sum, l) => sum + l.records_updated, 0)}
            </p>
          </div>
          <div className="bg-red-50 rounded-lg p-4">
            <p className="text-sm text-red-600">Failed</p>
            <p className="text-2xl font-bold text-red-900">
              {importLogs.reduce((sum, l) => sum + l.records_failed, 0)}
            </p>
          </div>
        </div>
      </div>

      {/* Scheduled Imports */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Scheduled Imports
        </h3>
        
        {schedules.length === 0 ? (
          <p className="text-gray-500">No scheduled imports configured.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Interval
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Last Run
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Next Run
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {schedules.map((schedule) => (
                  <tr key={schedule.import_type}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {schedule.import_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {schedule.interval}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded-full ${
                          schedule.enabled
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {schedule.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {schedule.last_run
                        ? new Date(schedule.last_run).toLocaleString()
                        : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {schedule.next_run
                        ? new Date(schedule.next_run).toLocaleString()
                        : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Import Logs */}
      {importLogs.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Recent Import Logs
          </h3>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Processed
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Updated
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Failed
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {importLogs.map((log) => (
                  <tr key={log.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {log.import_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(log.import_timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                          log.status
                        )}`}
                      >
                        {log.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {log.records_processed}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                      {log.records_created}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-yellow-600">
                      {log.records_updated}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                      {log.records_failed}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default HRMSAdminDashboard;
