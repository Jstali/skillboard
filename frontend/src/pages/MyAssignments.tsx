import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { PageHeader } from '../components/PageHeader';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Assignment {
    id: number;
    template_name: string;
    assigned_at: string;
    status: string;
}

const MyAssignments: React.FC = () => {
    const navigate = useNavigate();
    const [pendingAssignments, setPendingAssignments] = useState<Assignment[]>([]);
    const [completedAssignments, setCompletedAssignments] = useState<Assignment[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadAssignments();
    }, []);

    const loadAssignments = async () => {
        setLoading(true);
        setError(null);

        try {
            const token = localStorage.getItem('token');
            const headers = { Authorization: `Bearer ${token}` };

            const res = await axios.get(`${API_URL}/api/employee/assignments/my-assignments`, { headers });
            setPendingAssignments(res.data.pending || []);
            setCompletedAssignments(res.data.completed || []);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load assignments');
        } finally {
            setLoading(false);
        }
    };

    const handleFillTemplate = (assignmentId: number) => {
        navigate(`/assignments/${assignmentId}/fill`);
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'Pending':
                return 'bg-yellow-100 text-yellow-800';
            case 'Completed':
                return 'bg-green-100 text-green-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    return (
        <div className="min-h-screen bg-[#F6F2F4]">
            <PageHeader
                title="My Assignments"
                subtitle="View and complete your skill template assignments"
            />

            <div className="max-w-6xl mx-auto px-4 py-6">
                {error && (
                    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-800 text-sm">
                        {error}
                    </div>
                )}

                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Pending Assignments</p>
                                <p className="text-3xl font-bold text-yellow-600 mt-1">{pendingAssignments.length}</p>
                            </div>
                            <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
                                <svg className="w-6 h-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Completed</p>
                                <p className="text-3xl font-bold text-green-600 mt-1">{completedAssignments.length}</p>
                            </div>
                            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                                <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                        </div>
                    </div>
                </div>

                {loading ? (
                    <div className="text-center py-12 text-gray-500">Loading assignments...</div>
                ) : (
                    <>
                        {/* Pending Assignments */}
                        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                                <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
                                Pending Assignments
                            </h2>

                            {pendingAssignments.length === 0 ? (
                                <div className="text-center py-8 text-gray-500">
                                    <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                    <p className="text-lg font-medium">No pending assignments</p>
                                    <p className="text-sm mt-1">You're all caught up!</p>
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {pendingAssignments.map(assignment => (
                                        <div
                                            key={assignment.id}
                                            className="border border-yellow-200 rounded-lg p-4 bg-yellow-50 hover:shadow-md transition-shadow"
                                        >
                                            <div className="flex items-start justify-between mb-3">
                                                <div className="flex-1">
                                                    <h3 className="font-semibold text-gray-900 mb-1">{assignment.template_name}</h3>
                                                    <p className="text-sm text-gray-600">
                                                        Assigned: {formatDate(assignment.assigned_at)}
                                                    </p>
                                                </div>
                                                <span className={`px-2 py-1 rounded text-xs font-semibold ${getStatusColor(assignment.status)}`}>
                                                    {assignment.status}
                                                </span>
                                            </div>
                                            <button
                                                onClick={() => handleFillTemplate(assignment.id)}
                                                className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 font-medium text-sm flex items-center justify-center gap-2"
                                            >
                                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                                </svg>
                                                Fill Template
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Completed Assignments */}
                        <div className="bg-white rounded-lg shadow-sm p-6">
                            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                                Completed Assignments
                            </h2>

                            {completedAssignments.length === 0 ? (
                                <div className="text-center py-8 text-gray-500">
                                    <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    <p className="text-lg font-medium">No completed assignments yet</p>
                                    <p className="text-sm mt-1">Complete your pending assignments to see them here</p>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {completedAssignments.map(assignment => (
                                        <div
                                            key={assignment.id}
                                            className="border border-green-200 rounded-lg p-4 bg-green-50 flex items-center justify-between"
                                        >
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                                                    <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                                    </svg>
                                                </div>
                                                <div>
                                                    <h3 className="font-semibold text-gray-900">{assignment.template_name}</h3>
                                                    <p className="text-sm text-gray-600">
                                                        Completed: {formatDate(assignment.assigned_at)}
                                                    </p>
                                                </div>
                                            </div>
                                            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(assignment.status)}`}>
                                                ✓ {assignment.status}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default MyAssignments;
