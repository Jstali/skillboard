/**
 * Reconciliation View Component
 * 
 * Displays assignment comparison between skill board and HRMS,
 * highlights discrepancies, and provides export functionality.
 */
import React, { useEffect, useState } from 'react';
import { reconciliationApi, ReconciliationReportData, DiscrepancyInfo } from '../services/api';

const DiscrepancyBadge: React.FC<{ type: string }> = ({ type }) => {
  const colors = {
    Missing: 'bg-red-100 text-red-700',
    Extra: 'bg-yellow-100 text-yellow-700',
    Allocation_Mismatch: 'bg-orange-100 text-orange-700',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-700'}`}>
      {type.replace('_', ' ')}
    </span>
  );
};

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const colors = {
    Match: 'bg-green-100 text-green-700',
    Partial: 'bg-yellow-100 text-yellow-700',
    Mismatch: 'bg-red-100 text-red-700',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-700'}`}>
      {status}
    </span>
  );
};

export const ReconciliationView: React.FC = () => {
  const [report, setReport] = useState<ReconciliationReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await reconciliationApi.getReconciliationReport();
        setReport(data);
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load reconciliation data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleExport = async () => {
    try {
      setExporting(true);
      const blob = await reconciliationApi.exportReconciliationData('json');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'reconciliation_export.json';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert('Failed to export data');
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        {error}
      </div>
    );
  }

  if (!report) return null;

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold">Reconciliation Report</h2>
            <p className="text-sm text-gray-500">Generated: {new Date(report.generated_at).toLocaleString()}</p>
          </div>
          <button
            onClick={handleExport}
            disabled={exporting}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {exporting ? 'Exporting...' : 'Export Data'}
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-3xl font-bold text-gray-800">{report.total_employees}</p>
            <p className="text-sm text-gray-500">Total Employees</p>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <p className="text-3xl font-bold text-green-600">{report.employees_matched}</p>
            <p className="text-sm text-gray-500">Matched</p>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <p className="text-3xl font-bold text-red-600">{report.employees_with_discrepancies}</p>
            <p className="text-sm text-gray-500">With Discrepancies</p>
          </div>
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <p className="text-3xl font-bold text-yellow-600">{report.total_discrepancies}</p>
            <p className="text-sm text-gray-500">Total Discrepancies</p>
          </div>
        </div>

        {/* Discrepancy Breakdown */}
        <div className="mt-6">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Discrepancy Breakdown</h3>
          <div className="flex gap-4">
            {Object.entries(report.discrepancy_breakdown).map(([type, count]) => (
              <div key={type} className="flex items-center gap-2">
                <DiscrepancyBadge type={type} />
                <span className="font-medium">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Results Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b">
          <h3 className="text-lg font-semibold">Employee Results</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Skill Board</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">HRMS</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Discrepancies</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {report.results.map((result) => (
                <tr key={result.employee_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <p className="font-medium">{result.employee_name}</p>
                    <p className="text-xs text-gray-500">{result.employee_id}</p>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={result.match_status} />
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {result.skill_board_assignments.length} assignments
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {result.hrms_assignments.length} assignments
                  </td>
                  <td className="px-4 py-3">
                    {result.discrepancies.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {result.discrepancies.slice(0, 2).map((d, idx) => (
                          <DiscrepancyBadge key={idx} type={d.discrepancy_type} />
                        ))}
                        {result.discrepancies.length > 2 && (
                          <span className="text-xs text-gray-500">+{result.discrepancies.length - 2} more</span>
                        )}
                      </div>
                    ) : (
                      <span className="text-green-600 text-sm">✓ All matched</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ReconciliationView;
