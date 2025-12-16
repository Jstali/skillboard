import React, { useState, useEffect } from 'react';
import { levelMovementApi, LevelMovementRequest, ApprovalRequest, adminDashboardApi, Employee } from '../../services/api';

const LevelMovementApprovals: React.FC = () => {
    const [requests, setRequests] = useState<LevelMovementRequest[]>([]);
    const [employees, setEmployees] = useState<Record<number, Employee>>({});
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>('all');
    const [showApprovalModal, setShowApprovalModal] = useState(false);
    const [selectedRequest, setSelectedRequest] = useState<LevelMovementRequest | null>(null);
    const [approvalData, setApprovalData] = useState<ApprovalRequest>({ comments: '' });
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    useEffect(() => {
        loadData();
    }, [filter]);

    const loadData = async () => {
        try {
            setLoading(true);
            const [reqs, emps] = await Promise.all([
                filter === 'all' ? levelMovementApi.listRequests() : levelMovementApi.listRequests(filter),
                adminDashboardApi.getEmployees(),
            ]);
            setRequests(reqs);

            // Create employee lookup map
            const empMap: Record<number, Employee> = {};
            emps.forEach(emp => empMap[emp.id] = emp);
            setEmployees(empMap);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load requests');
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async () => {
        if (!selectedRequest) return;

        try {
            await levelMovementApi.approve(selectedRequest.id, approvalData);
            setSuccess('Request approved successfully!');
            setShowApprovalModal(false);
            setApprovalData({ comments: '' });
            loadData();
            setTimeout(() => setSuccess(null), 3000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to approve request');
        }
    };

    const handleReject = async () => {
        if (!selectedRequest) return;
        if (!approvalData.comments?.trim()) {
            setError('Please provide a reason for rejection');
            return;
        }

        try {
            await levelMovementApi.reject(selectedRequest.id, approvalData);
            setSuccess('Request rejected');
            setShowApprovalModal(false);
            setApprovalData({ comments: '' });
            loadData();
            setTimeout(() => setSuccess(null), 3000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to reject request');
        }
    };

    const openApprovalModal = (request: LevelMovementRequest) => {
        setSelectedRequest(request);
        setShowApprovalModal(true);
        setApprovalData({ comments: '' });
    };

    const getStatusBadge = (status: string) => {
        const colors: Record<string, string> = {
            pending: 'bg-yellow-100 text-yellow-800',
            manager_approved: 'bg-blue-100 text-blue-800',
            cp_approved: 'bg-purple-100 text-purple-800',
            hr_approved: 'bg-green-100 text-green-800',
            rejected: 'bg-red-100 text-red-800',
        };
        return colors[status] || 'bg-gray-100 text-gray-800';
    };

    const getStatusLabel = (status: string) => {
        const labels: Record<string, string> = {
            pending: 'Pending Manager',
            manager_approved: 'Manager Approved',
            cp_approved: 'CP Approved',
            hr_approved: 'HR Approved',
            rejected: 'Rejected',
        };
        return labels[status] || status;
    };

    if (loading) {
        return <div className="flex justify-center items-center h-64">Loading...</div>;
    }

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">Level Movement Approvals</h2>
                <select
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                >
                    <option value="all">All Requests</option>
                    <option value="pending">Pending</option>
                    <option value="manager_approved">Manager Approved</option>
                    <option value="cp_approved">CP Approved</option>
                    <option value="hr_approved">HR Approved</option>
                    <option value="rejected">Rejected</option>
                </select>
            </div>

            {success && (
                <div className="mb-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded">
                    {success}
                </div>
            )}
            {error && (
                <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
                    {error}
                    <button onClick={() => setError(null)} className="float-right font-bold">×</button>
                </div>
            )}

            <div className="bg-white rounded-lg shadow-md overflow-hidden">
                {requests.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                        No level movement requests found.
                    </div>
                ) : (
                    <table className="w-full">
                        <thead className="bg-gray-100">
                            <tr>
                                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Employee</th>
                                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Current Level</th>
                                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Requested Level</th>
                                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Readiness</th>
                                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Status</th>
                                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Submitted</th>
                                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {requests.map((req) => (
                                <tr key={req.id} className="border-b hover:bg-gray-50">
                                    <td className="px-4 py-3">
                                        {employees[req.employee_id]?.name || `Employee #${req.employee_id}`}
                                    </td>
                                    <td className="px-4 py-3">{req.current_level || '-'}</td>
                                    <td className="px-4 py-3 font-semibold">{req.requested_level}</td>
                                    <td className="px-4 py-3">
                                        {req.readiness_score !== undefined && req.readiness_score !== null ? (
                                            <span className={`font-medium ${req.readiness_score >= 70 ? 'text-green-600' : 'text-orange-600'}`}>
                                                {req.readiness_score.toFixed(1)}%
                                            </span>
                                        ) : '-'}
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusBadge(req.status)}`}>
                                            {getStatusLabel(req.status)}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-600">
                                        {new Date(req.submission_date).toLocaleDateString()}
                                    </td>
                                    <td className="px-4 py-3">
                                        {req.status !== 'rejected' && req.status !== 'hr_approved' && (
                                            <button
                                                onClick={() => openApprovalModal(req)}
                                                className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition"
                                            >
                                                Review
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Approval Modal */}
            {showApprovalModal && selectedRequest && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-lg">
                        <h3 className="text-xl font-bold mb-4">Review Level Movement Request</h3>

                        <div className="mb-4 p-4 bg-gray-50 rounded">
                            <p><strong>Employee:</strong> {employees[selectedRequest.employee_id]?.name}</p>
                            <p><strong>Current Level:</strong> {selectedRequest.current_level || 'N/A'}</p>
                            <p><strong>Requested Level:</strong> {selectedRequest.requested_level}</p>
                            <p><strong>Readiness Score:</strong> {selectedRequest.readiness_score?.toFixed(1)}%</p>
                            <p><strong>Status:</strong> {getStatusLabel(selectedRequest.status)}</p>
                        </div>

                        <div className="mb-4">
                            <label className="block text-gray-700 text-sm font-bold mb-2">
                                Comments {selectedRequest.status === 'pending' ? '(Optional)' : '(Required for rejection)'}
                            </label>
                            <textarea
                                value={approvalData.comments}
                                onChange={(e) => setApprovalData({ comments: e.target.value })}
                                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                                rows={4}
                                placeholder="Add your comments here..."
                            />
                        </div>

                        <div className="flex gap-2">
                            <button
                                onClick={handleApprove}
                                className="flex-1 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition"
                            >
                                Approve
                            </button>
                            <button
                                onClick={handleReject}
                                className="flex-1 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition"
                            >
                                Reject
                            </button>
                            <button
                                onClick={() => setShowApprovalModal(false)}
                                className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400 transition"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LevelMovementApprovals;
