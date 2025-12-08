import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { PageHeader } from '../components/PageHeader';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface EmployeeWithGaps {
    assignment_id: number;
    employee_id: number;
    employee_name: string;
    template_id: number;
    template_name: string;
    category_hr: string;
    employee_category: string;
    total_gaps: number;
    submitted_at: string;
}

interface EmployeeWithoutGaps {
    assignment_id: number;
    employee_id: number;
    employee_name: string;
    template_id: number;
    template_name: string;
    category_hr: string;
    employee_category: string;
    submitted_at: string;
}

const SkillGapAnalysis: React.FC = () => {
    const navigate = useNavigate();
    const [employeesWithGaps, setEmployeesWithGaps] = useState<EmployeeWithGaps[]>([]);
    const [employeesWithoutGaps, setEmployeesWithoutGaps] = useState<EmployeeWithoutGaps[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [activePanel, setActivePanel] = useState<'with-gaps' | 'without-gaps'>('with-gaps');

    useEffect(() => {
        loadGapData();
    }, []);

    const loadGapData = async () => {
        console.log('DEBUG: loadGapData function called');
        setLoading(true);
        setError(null);

        try {
            const token = localStorage.getItem('token');
            console.log('DEBUG: Token exists:', !!token);

            if (!token) {
                throw new Error('No authentication token found');
            }

            const headers = { Authorization: `Bearer ${token}` };
            const apiUrl = API_URL || 'http://localhost:8000';

            console.log('DEBUG: API URL:', apiUrl);
            console.log('DEBUG: Calling with-gaps endpoint...');

            // Load employees with gaps
            try {
                const withGapsRes = await axios.get(`${apiUrl}/api/admin/skill-gaps/with-gaps`, { headers });
                console.log('DEBUG: With gaps response status:', withGapsRes.status);
                console.log('DEBUG: With gaps response data:', withGapsRes.data);
                console.log('DEBUG: With gaps data type:', typeof withGapsRes.data);
                console.log('DEBUG: With gaps is array:', Array.isArray(withGapsRes.data));
                console.log('DEBUG: With gaps length:', withGapsRes.data?.length);
                setEmployeesWithGaps(withGapsRes.data || []);
            } catch (withGapsErr: any) {
                console.error('DEBUG: Error fetching with-gaps:', withGapsErr);
                console.error('DEBUG: Error response:', withGapsErr.response?.data);
                console.error('DEBUG: Error status:', withGapsErr.response?.status);
                throw withGapsErr;
            }

            console.log('DEBUG: Calling without-gaps endpoint...');

            // Load employees without gaps
            try {
                const withoutGapsRes = await axios.get(`${apiUrl}/api/admin/skill-gaps/without-gaps`, { headers });
                console.log('DEBUG: Without gaps response status:', withoutGapsRes.status);
                console.log('DEBUG: Without gaps response data:', withoutGapsRes.data);
                console.log('DEBUG: Without gaps data type:', typeof withoutGapsRes.data);
                console.log('DEBUG: Without gaps is array:', Array.isArray(withoutGapsRes.data));
                console.log('DEBUG: Without gaps length:', withoutGapsRes.data?.length);
                setEmployeesWithoutGaps(withoutGapsRes.data || []);
            } catch (withoutGapsErr: any) {
                console.error('DEBUG: Error fetching without-gaps:', withoutGapsErr);
                console.error('DEBUG: Error response:', withoutGapsErr.response?.data);
                console.error('DEBUG: Error status:', withoutGapsErr.response?.status);
                throw withoutGapsErr;
            }

            console.log('DEBUG: Successfully loaded all gap data');
        } catch (err: any) {
            console.error('DEBUG: Error in loadGapData:', err);
            console.error('DEBUG: Error message:', err.message);
            console.error('DEBUG: Error response:', err.response);
            setError(err.response?.data?.detail || err.message || 'Failed to load gap analysis data');
        } finally {
            setLoading(false);
            console.log('DEBUG: loadGapData completed');
        }
    };

    const handleViewDetails = (assignmentId: number) => {
        navigate(`/admin/skill-gaps/${assignmentId}/details`);
    };

    const getCategoryMismatch = (hrCategory: string, empCategory: string) => {
        return hrCategory !== empCategory;
    };

    return (
        <div className="min-h-screen bg-[#F6F2F4]">
            <PageHeader
                title="Skill Gap Analysis"
                subtitle="View employees with and without skill gaps"
            />

            <div className="max-w-7xl mx-auto px-4 py-6">
                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Total Analyzed</p>
                                <p className="text-3xl font-bold text-gray-900 mt-1">
                                    {employeesWithGaps.length + employeesWithoutGaps.length}
                                </p>
                            </div>
                            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                                <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">With Gaps</p>
                                <p className="text-3xl font-bold text-red-600 mt-1">{employeesWithGaps.length}</p>
                            </div>
                            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                                <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Without Gaps</p>
                                <p className="text-3xl font-bold text-green-600 mt-1">{employeesWithoutGaps.length}</p>
                            </div>
                            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                                <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                        </div>
                    </div>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-800 text-sm">
                        {error}
                    </div>
                )}

                {/* Two-Panel Layout */}
                <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                    {/* Tabs */}
                    <div className="border-b border-gray-200">
                        <nav className="flex -mb-px">
                            <button
                                onClick={() => setActivePanel('with-gaps')}
                                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${activePanel === 'with-gaps'
                                    ? 'border-red-500 text-red-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                            >
                                <span className="flex items-center gap-2">
                                    Employees WITH Gaps
                                    <span className="px-2 py-0.5 bg-red-100 text-red-800 rounded-full text-xs font-semibold">
                                        {employeesWithGaps.length}
                                    </span>
                                </span>
                            </button>
                            <button
                                onClick={() => setActivePanel('without-gaps')}
                                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${activePanel === 'without-gaps'
                                    ? 'border-green-500 text-green-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                            >
                                <span className="flex items-center gap-2">
                                    Employees WITHOUT Gaps
                                    <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded-full text-xs font-semibold">
                                        {employeesWithoutGaps.length}
                                    </span>
                                </span>
                            </button>
                        </nav>
                    </div>

                    {/* Panel Content */}
                    <div className="p-6">
                        {loading ? (
                            <div className="text-center py-12 text-gray-500">Loading gap analysis...</div>
                        ) : activePanel === 'with-gaps' ? (
                            /* Employees WITH Gaps Panel */
                            employeesWithGaps.length === 0 ? (
                                <div className="text-center py-12 text-gray-500">
                                    <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    <p className="text-lg font-medium">No employees with skill gaps!</p>
                                    <p className="text-sm mt-1">All analyzed employees meet their requirements.</p>
                                </div>
                            ) : (
                                <div className="overflow-x-auto">
                                    <table className="min-w-full divide-y divide-gray-200">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Employee
                                                </th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Template
                                                </th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    HR Category
                                                </th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Employee Category
                                                </th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Total Gaps
                                                </th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Submitted
                                                </th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Actions
                                                </th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                            {employeesWithGaps.map(emp => (
                                                <tr key={emp.assignment_id} className="hover:bg-gray-50">
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                        {emp.employee_name}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                        {emp.template_name}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                                        {emp.category_hr}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                        <span className={getCategoryMismatch(emp.category_hr, emp.employee_category) ? 'text-orange-600 font-medium' : 'text-gray-600'}>
                                                            {emp.employee_category}
                                                            {getCategoryMismatch(emp.category_hr, emp.employee_category) && (
                                                                <span className="ml-1 text-xs">⚠️</span>
                                                            )}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className="px-3 py-1 inline-flex text-sm leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                                                            {emp.total_gaps} gaps
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                        {new Date(emp.submitted_at).toLocaleDateString()}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                        <button
                                                            onClick={() => handleViewDetails(emp.assignment_id)}
                                                            className="text-purple-600 hover:text-purple-800 font-medium"
                                                        >
                                                            View Details →
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )
                        ) : (
                            /* Employees WITHOUT Gaps Panel */
                            employeesWithoutGaps.length === 0 ? (
                                <div className="text-center py-12 text-gray-500">
                                    <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                    </svg>
                                    <p className="text-lg font-medium">No employees without gaps yet</p>
                                    <p className="text-sm mt-1">Employees who meet all requirements will appear here.</p>
                                </div>
                            ) : (
                                <div className="overflow-x-auto">
                                    <table className="min-w-full divide-y divide-gray-200">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Employee
                                                </th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Template
                                                </th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    HR Category
                                                </th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Employee Category
                                                </th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Status
                                                </th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Submitted
                                                </th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                            {employeesWithoutGaps.map(emp => (
                                                <tr key={emp.assignment_id} className="hover:bg-gray-50">
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                        {emp.employee_name}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                        {emp.template_name}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                                        {emp.category_hr}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                        <span className={getCategoryMismatch(emp.category_hr, emp.employee_category) ? 'text-orange-600 font-medium' : 'text-gray-600'}>
                                                            {emp.employee_category}
                                                            {getCategoryMismatch(emp.category_hr, emp.employee_category) && (
                                                                <span className="ml-1 text-xs">⚠️</span>
                                                            )}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className="px-3 py-1 inline-flex text-sm leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                                                            ✓ No Gaps
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                        {new Date(emp.submitted_at).toLocaleDateString()}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SkillGapAnalysis;
