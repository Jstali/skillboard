import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { PageHeader } from '../components/PageHeader';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Employee {
    id: number;
    employee_id: string;
    name: string;
    role: string;
    department: string;
    band: string;
}

interface Template {
    id: number;
    template_name: string;
    file_name: string;
}

interface Assignment {
    id: number;
    employee_id: number;
    employee_name: string;
    template_id: number;
    template_name: string;
    category_hr: string;
    status: string;
    assigned_at: string;
}

const TemplateAssignment: React.FC = () => {
    const navigate = useNavigate();
    const [employees, setEmployees] = useState<Employee[]>([]);
    const [templates, setTemplates] = useState<Template[]>([]);
    const [assignments, setAssignments] = useState<Assignment[]>([]);
    const [categories, setCategories] = useState<string[]>([]);

    const [selectedEmployee, setSelectedEmployee] = useState<number | null>(null);
    const [selectedTemplate, setSelectedTemplate] = useState<number | null>(null);
    const [selectedCategory, setSelectedCategory] = useState<string>('');

    const [loading, setLoading] = useState(false);
    const [assignmentLoading, setAssignmentLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const [filterStatus, setFilterStatus] = useState<string>('all');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const headers = { Authorization: `Bearer ${token}` };

            // Load employees
            const empRes = await axios.get(`${API_URL}/api/admin/employees`, { headers });
            setEmployees(empRes.data);

            // Load templates
            const tempRes = await axios.get(`${API_URL}/api/templates`, { headers });
            setTemplates(tempRes.data);

            // Load categories
            const catRes = await axios.get(`${API_URL}/api/categories`, { headers });
            setCategories(catRes.data.map((c: any) => c.name));

            // Load existing assignments
            const assignRes = await axios.get(`${API_URL}/api/admin/template-assignments`, { headers });
            setAssignments(assignRes.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load data');
        } finally {
            setLoading(false);
        }
    };

    const handleAssign = async () => {
        if (!selectedEmployee || !selectedTemplate || !selectedCategory) {
            setError('Please select employee, template, and category');
            return;
        }

        setAssignmentLoading(true);
        setError(null);
        setSuccess(null);

        try {
            const token = localStorage.getItem('token');
            const headers = { Authorization: `Bearer ${token}` };

            await axios.post(
                `${API_URL}/api/admin/template-assignments`,
                {
                    employee_id: selectedEmployee,
                    template_id: selectedTemplate,
                    category_hr: selectedCategory
                },
                { headers }
            );

            setSuccess('Template assigned successfully!');
            setSelectedEmployee(null);
            setSelectedTemplate(null);
            setSelectedCategory('');

            // Reload assignments
            const assignRes = await axios.get(`${API_URL}/api/admin/template-assignments`, { headers });
            setAssignments(assignRes.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to assign template');
        } finally {
            setAssignmentLoading(false);
        }
    };

    const handleDelete = async (assignmentId: number) => {
        if (!confirm('Are you sure you want to delete this assignment?')) return;

        try {
            const token = localStorage.getItem('token');
            const headers = { Authorization: `Bearer ${token}` };

            await axios.delete(`${API_URL}/api/admin/template-assignments/${assignmentId}`, { headers });

            setSuccess('Assignment deleted successfully');

            // Reload assignments
            const assignRes = await axios.get(`${API_URL}/api/admin/template-assignments`, { headers });
            setAssignments(assignRes.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to delete assignment');
        }
    };

    const filteredAssignments = assignments.filter(a => {
        if (filterStatus === 'all') return true;
        return a.status === filterStatus;
    });

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'Pending': return 'bg-yellow-100 text-yellow-800';
            case 'Completed': return 'bg-green-100 text-green-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    return (
        <div className="min-h-screen bg-[#F6F2F4]">
            <PageHeader
                title="Template Assignment"
                subtitle="Assign skill templates to employees with HR category selection"
            />

            <div className="max-w-7xl mx-auto px-4 py-6">
                {/* Assignment Form */}
                <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">Assign Template</h2>

                    {error && (
                        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-800 text-sm">
                            {error}
                        </div>
                    )}

                    {success && (
                        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md text-green-800 text-sm">
                            {success}
                        </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        {/* Employee Selector */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Select Employee *
                            </label>
                            <select
                                value={selectedEmployee || ''}
                                onChange={(e) => setSelectedEmployee(Number(e.target.value))}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                            >
                                <option value="">Choose employee...</option>
                                {employees.map(emp => (
                                    <option key={emp.id} value={emp.id}>
                                        {emp.name} - {emp.role} ({emp.band})
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Template Selector */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Select Template *
                            </label>
                            <select
                                value={selectedTemplate || ''}
                                onChange={(e) => setSelectedTemplate(Number(e.target.value))}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                            >
                                <option value="">Choose template...</option>
                                {templates.map(temp => (
                                    <option key={temp.id} value={temp.id}>
                                        {temp.template_name}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Category Selector */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                HR Category * <span className="text-xs text-gray-500">(Hidden from employee)</span>
                            </label>
                            <select
                                value={selectedCategory}
                                onChange={(e) => setSelectedCategory(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                            >
                                <option value="">Choose category...</option>
                                {categories.map(cat => (
                                    <option key={cat} value={cat}>{cat}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <button
                        onClick={handleAssign}
                        disabled={assignmentLoading || !selectedEmployee || !selectedTemplate || !selectedCategory}
                        className="px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                    >
                        {assignmentLoading ? 'Assigning...' : 'Assign Template'}
                    </button>
                </div>

                {/* Assignments List */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-bold text-gray-900">Assignment History</h2>

                        {/* Filter */}
                        <div className="flex items-center gap-2">
                            <label className="text-sm font-medium text-gray-700">Status:</label>
                            <select
                                value={filterStatus}
                                onChange={(e) => setFilterStatus(e.target.value)}
                                className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-purple-500"
                            >
                                <option value="all">All</option>
                                <option value="Pending">Pending</option>
                                <option value="Completed">Completed</option>
                            </select>
                        </div>
                    </div>

                    {loading ? (
                        <div className="text-center py-8 text-gray-500">Loading assignments...</div>
                    ) : filteredAssignments.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">No assignments found</div>
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
                                            Status
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Assigned Date
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Actions
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {filteredAssignments.map(assignment => (
                                        <tr key={assignment.id} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                {assignment.employee_name}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {assignment.template_name}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                                {assignment.category_hr}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(assignment.status)}`}>
                                                    {assignment.status}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {new Date(assignment.assigned_at).toLocaleDateString()}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                {assignment.status === 'Pending' && (
                                                    <button
                                                        onClick={() => handleDelete(assignment.id)}
                                                        className="text-red-600 hover:text-red-800 font-medium"
                                                    >
                                                        Delete
                                                    </button>
                                                )}
                                                {assignment.status === 'Completed' && (
                                                    <button
                                                        onClick={() => navigate(`/admin/skill-gaps/${assignment.id}/details`)}
                                                        className="text-purple-600 hover:text-purple-800 font-medium"
                                                    >
                                                        View Gaps
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default TemplateAssignment;
