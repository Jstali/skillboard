import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

interface ReadinessScore {
  employee_id: number;
  current_level: string;
  target_level: string;
  score: number;
  criteria_met: number;
  criteria_total: number;
  skill_gaps: Array<{
    skill_id: number;
    required: string;
    current: string | null;
    gap: number;
  }>;
  is_ready: boolean;
}

interface WorkflowRequest {
  id: number;
  employee_id: number;
  current_level: string;
  target_level: string;
  status: string;
  readiness_score: number | null;
  current_approver_role: string | null;
  initiated_at: string;
  approvals: Array<{
    role: string;
    status: string;
    comments: string | null;
    timestamp: string;
  }>;
}

interface LevelMovementProps {
  employeeId: number;
  currentLevel?: string;
  isManager?: boolean;
}

export const LevelMovement: React.FC<LevelMovementProps> = ({
  employeeId,
  currentLevel = 'A',
  isManager = false,
}) => {
  const [readiness, setReadiness] = useState<ReadinessScore | null>(null);
  const [requests, setRequests] = useState<WorkflowRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<string>('');

  const levels = ['A', 'B', 'C', 'L1', 'L2'];

  useEffect(() => {
    fetchData();
  }, [employeeId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [readinessRes, requestsRes] = await Promise.all([
        api.get(`/api/level-movement/readiness/${employeeId}`).catch(() => null),
        api.get(`/api/level-movement/requests/${employeeId}`).catch(() => ({ data: [] })),
      ]);
      
      if (readinessRes) {
        setReadiness(readinessRes.data);
      }
      setRequests(requestsRes.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitRequest = async () => {
    if (!selectedLevel) return;

    try {
      setSubmitting(true);
      await api.post('/api/level-movement/request', {
        employee_id: employeeId,
        target_level: selectedLevel,
      });
      await fetchData();
      setSelectedLevel('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit request');
    } finally {
      setSubmitting(false);
    }
  };

  const handleApprove = async (requestId: number, approved: boolean) => {
    try {
      setSubmitting(true);
      await api.post(`/api/level-movement/approve/${requestId}`, {
        approved,
        comments: approved ? 'Approved' : 'Rejected',
      });
      await fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process approval');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'manager_approved':
      case 'cp_approved':
        return 'bg-blue-100 text-blue-800';
      case 'hr_approved':
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getNextLevel = (current: string) => {
    const idx = levels.indexOf(current);
    return idx < levels.length - 1 ? levels[idx + 1] : null;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const nextLevel = getNextLevel(currentLevel);

  return (
    <div className="space-y-6">
      {/* Readiness Assessment */}
      {readiness && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Level Progression Readiness
          </h3>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-sm text-gray-500">Current Level</p>
              <p className="text-xl font-bold text-gray-900">
                {readiness.current_level}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Target Level</p>
              <p className="text-xl font-bold text-gray-900">
                {readiness.target_level}
              </p>
            </div>
          </div>

          <div className="mb-4">
            <div className="flex justify-between mb-1">
              <span className="text-sm text-gray-600">Readiness Score</span>
              <span className="text-sm font-medium text-gray-900">
                {readiness.score.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full ${
                  readiness.is_ready ? 'bg-green-500' : 'bg-yellow-500'
                }`}
                style={{ width: `${Math.min(readiness.score, 100)}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {readiness.criteria_met} of {readiness.criteria_total} criteria met
            </p>
          </div>

          {readiness.skill_gaps.length > 0 && (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">
                Skill Gaps to Address:
              </p>
              <ul className="space-y-1">
                {readiness.skill_gaps.slice(0, 5).map((gap, idx) => (
                  <li
                    key={idx}
                    className="text-sm text-gray-600 flex justify-between"
                  >
                    <span>Skill #{gap.skill_id}</span>
                    <span className="text-red-600">
                      {gap.current || 'None'} → {gap.required}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {readiness.is_ready && (
            <div className="mt-4 p-3 bg-green-50 rounded-lg">
              <p className="text-sm text-green-700">
                ✓ You meet the criteria for level progression!
              </p>
            </div>
          )}
        </div>
      )}

      {/* Submit Request */}
      {!isManager && nextLevel && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Request Level Movement
          </h3>
          
          <div className="flex items-end gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target Level
              </label>
              <select
                value={selectedLevel}
                onChange={(e) => setSelectedLevel(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              >
                <option value="">Select level...</option>
                {levels
                  .filter((l) => levels.indexOf(l) > levels.indexOf(currentLevel))
                  .map((level) => (
                    <option key={level} value={level}>
                      {level}
                    </option>
                  ))}
              </select>
            </div>
            <button
              onClick={handleSubmitRequest}
              disabled={!selectedLevel || submitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? 'Submitting...' : 'Submit Request'}
            </button>
          </div>
        </div>
      )}

      {/* Existing Requests */}
      {requests.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Level Movement Requests
            </h3>
          </div>
          
          <div className="divide-y divide-gray-200">
            {requests.map((request) => (
              <div key={request.id} className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <p className="text-sm text-gray-500">
                      {request.current_level} → {request.target_level}
                    </p>
                    <p className="text-xs text-gray-400">
                      Submitted: {new Date(request.initiated_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                      request.status
                    )}`}
                  >
                    {request.status.replace('_', ' ')}
                  </span>
                </div>

                {request.readiness_score !== null && (
                  <p className="text-sm text-gray-600 mb-2">
                    Readiness: {request.readiness_score.toFixed(1)}%
                  </p>
                )}

                {request.approvals.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-medium text-gray-500 mb-1">
                      Approval History:
                    </p>
                    <div className="space-y-1">
                      {request.approvals.map((approval, idx) => (
                        <div
                          key={idx}
                          className="text-xs text-gray-600 flex justify-between"
                        >
                          <span>{approval.role}</span>
                          <span
                            className={
                              approval.status === 'approved'
                                ? 'text-green-600'
                                : 'text-red-600'
                            }
                          >
                            {approval.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {isManager &&
                  request.status !== 'rejected' &&
                  request.status !== 'hr_approved' && (
                    <div className="mt-4 flex gap-2">
                      <button
                        onClick={() => handleApprove(request.id, true)}
                        disabled={submitting}
                        className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => handleApprove(request.id, false)}
                        disabled={submitting}
                        className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:opacity-50"
                      >
                        Reject
                      </button>
                    </div>
                  )}
              </div>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}
    </div>
  );
};

export default LevelMovement;
