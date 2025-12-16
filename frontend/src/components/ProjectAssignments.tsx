import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

interface Assignment {
  id: number;
  employee_id: number;
  project_id: number;
  project_name: string | null;
  is_primary: boolean;
  percentage_allocation: number | null;
  line_manager_id: number | null;
  start_date: string | null;
  end_date: string | null;
}

interface ProjectAssignmentsProps {
  employeeId?: number;
  showTitle?: boolean;
}

export const ProjectAssignments: React.FC<ProjectAssignmentsProps> = ({
  employeeId,
  showTitle = true,
}) => {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAssignments();
  }, [employeeId]);

  const fetchAssignments = async () => {
    try {
      setLoading(true);
      const endpoint = employeeId
        ? `/api/assignments/employee/${employeeId}`
        : '/api/assignments/my-assignments';
      const response = await api.get(endpoint);
      setAssignments(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load assignments');
    } finally {
      setLoading(false);
    }
  };

  const getTotalAllocation = () => {
    return assignments.reduce(
      (sum, a) => sum + (a.percentage_allocation || 0),
      0
    );
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
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

  const totalAllocation = getTotalAllocation();
  const isOverAllocated = totalAllocation > 100;

  return (
    <div className="bg-white rounded-lg shadow">
      {showTitle && (
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Project Assignments
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Total Allocation:{' '}
            <span
              className={`font-medium ${
                isOverAllocated ? 'text-red-600' : 'text-green-600'
              }`}
            >
              {totalAllocation}%
            </span>
            {isOverAllocated && (
              <span className="ml-2 text-red-600">(Over-allocated!)</span>
            )}
          </p>
        </div>
      )}

      {assignments.length === 0 ? (
        <div className="p-6 text-center text-gray-500">
          No project assignments found.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Project
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Allocation
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Start Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  End Date
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {assignments.map((assignment) => (
                <tr key={assignment.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {assignment.project_name || `Project ${assignment.project_id}`}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {assignment.is_primary ? (
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        Primary
                      </span>
                    ) : (
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                        Secondary
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                        <div
                          className={`h-2 rounded-full ${
                            (assignment.percentage_allocation || 0) > 50
                              ? 'bg-blue-600'
                              : 'bg-blue-400'
                          }`}
                          style={{
                            width: `${Math.min(
                              assignment.percentage_allocation || 0,
                              100
                            )}%`,
                          }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-900">
                        {assignment.percentage_allocation || 0}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(assignment.start_date)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(assignment.end_date)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default ProjectAssignments;
