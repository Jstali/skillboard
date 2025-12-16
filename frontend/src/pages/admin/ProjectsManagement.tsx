import React, { useState, useEffect } from 'react';
import { api, Employee, adminDashboardApi, AssignEmployeeToProject } from '../../services/api';
import { RefreshCw, Users, Eye, Pencil, Trash2 } from 'lucide-react';

interface HRMSProject {
    id?: number;
    project_id?: string;
    name: string;
    client_name?: string;
    status?: string;
    manager_name?: string;
}

const ProjectsManagement: React.FC = () => {
    const [projects, setProjects] = useState<HRMSProject[]>([]);
    const [employees, setEmployees] = useState<Employee[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAssignModal, setShowAssignModal] = useState(false);
    const [showViewModal, setShowViewModal] = useState(false);
    const [selectedProject, setSelectedProject] = useState<HRMSProject | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Pagination
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);

    const [assignmentData, setAssignmentData] = useState<AssignEmployeeToProject>({
        employee_id: 0,
        project_id: 0,
        is_primary: false,
        percentage_allocation: 100,
    });

    useEffect(() => {
        loadProjects();
        loadEmployees();
    }, []);

    const loadProjects = async () => {
        try {
            setLoading(true);
            setError(null);
            // Fetch projects from HRMS via the DM dashboard endpoint
            const response = await api.get('/api/dashboard/dm/projects');
            setProjects(response.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load projects from HRMS');
            setProjects([]);
        } finally {
            setLoading(false);
        }
    };

    const loadEmployees = async () => {
        try {
            const data = await adminDashboardApi.getEmployees();
            setEmployees(data);
        } catch (err: any) {
            console.error('Failed to load employees:', err);
        }
    };

    const handleAssignEmployee = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedProject) return;

        try {
            // First, ensure the project exists in local DB by syncing it
            await api.post('/api/projects/sync-from-hrms', {
                hrms_project_id: selectedProject.project_id || String(selectedProject.id),
                name: selectedProject.name,
                client_name: selectedProject.client_name,
                status: selectedProject.status,
                manager_name: selectedProject.manager_name
            });

            // Then assign the employee
            const localProjectResponse = await api.get(`/api/projects/by-hrms-id/${selectedProject.project_id || selectedProject.id}`);
            const localProjectId = localProjectResponse.data.id;

            await api.post(`/api/projects/${localProjectId}/assign-employee`, assignmentData);
            
            setSuccess('Employee assigned successfully!');
            setShowAssignModal(false);
            setAssignmentData({
                employee_id: 0,
                project_id: 0,
                is_primary: false,
                percentage_allocation: 100,
            });
            setTimeout(() => setSuccess(null), 3000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to assign employee');
        }
    };

    const openAssignModal = (project: HRMSProject) => {
        setSelectedProject(project);
        setShowAssignModal(true);
    };

    const openViewModal = (project: HRMSProject) => {
        setSelectedProject(project);
        setShowViewModal(true);
    };

    // Pagination logic
    const totalPages = Math.ceil(projects.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const paginatedProjects = projects.slice(startIndex, startIndex + itemsPerPage);

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="text-gray-600">Loading projects from HRMS...</div>
            </div>
        );
    }

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">Projects Management</h2>
                <button
                    onClick={loadProjects}
                    className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
                >
                    <RefreshCw className="w-4 h-4" />
                    Refresh from HRMS
                </button>
            </div>

            {/* Info Banner */}
            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 text-blue-700 rounded-lg">
                <p className="text-sm">
                    Projects are managed in HRMS. This view shows all projects synced from the HRMS system.
                    You can assign employees to projects for skill tracking purposes.
                </p>
            </div>

            {/* Success/Error Messages */}
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

            {/* Projects Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="p-4 border-b flex justify-between items-center">
                    <span className="text-sm text-gray-600">
                        Showing {paginatedProjects.length} of {projects.length} projects
                    </span>
                    <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-600">Show:</span>
                        <select
                            value={itemsPerPage}
                            onChange={(e) => {
                                setItemsPerPage(Number(e.target.value));
                                setCurrentPage(1);
                            }}
                            className="border rounded px-2 py-1 text-sm"
                        >
                            <option value={10}>10</option>
                            <option value={25}>25</option>
                            <option value={50}>50</option>
                        </select>
                    </div>
                </div>

                {projects.length === 0 ? (
                    <div className="p-12 text-center text-gray-500">
                        No projects found in HRMS. Please check the HRMS connection.
                    </div>
                ) : (
                    <table className="w-full">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Project Name
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Client
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Manager
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Status
                                </th>
                                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {paginatedProjects.map((project, index) => (
                                <tr key={project.id || project.project_id || index} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                        {project.name}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {project.client_name || '-'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {project.manager_name || '-'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 py-1 text-xs rounded-full ${
                                            project.status === 'Active' 
                                                ? 'bg-green-100 text-green-800' 
                                                : 'bg-gray-100 text-gray-800'
                                        }`}>
                                            {project.status || 'Active'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                        <div className="flex justify-center gap-2">
                                            <button
                                                onClick={() => openViewModal(project)}
                                                className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded"
                                                title="View Details"
                                            >
                                                <Eye className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => openAssignModal(project)}
                                                className="p-2 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded"
                                                title="Assign Employees"
                                            >
                                                <Users className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="px-6 py-4 border-t flex justify-end items-center gap-2">
                        <button
                            onClick={() => setCurrentPage(1)}
                            disabled={currentPage === 1}
                            className="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                        >
                            «
                        </button>
                        <button
                            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                            disabled={currentPage === 1}
                            className="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                        >
                            ‹
                        </button>
                        <span className="px-4 py-1 bg-blue-600 text-white rounded">
                            {currentPage}
                        </span>
                        <button
                            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                            disabled={currentPage === totalPages}
                            className="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                        >
                            ›
                        </button>
                        <button
                            onClick={() => setCurrentPage(totalPages)}
                            disabled={currentPage === totalPages}
                            className="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                        >
                            »
                        </button>
                    </div>
                )}
            </div>

            {/* View Project Modal */}
            {showViewModal && selectedProject && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h3 className="text-xl font-bold mb-4">Project Details</h3>
                        <div className="space-y-3">
                            <div>
                                <label className="text-sm text-gray-500">Project Name</label>
                                <p className="font-medium">{selectedProject.name}</p>
                            </div>
                            <div>
                                <label className="text-sm text-gray-500">Project ID</label>
                                <p className="font-medium">{selectedProject.project_id || selectedProject.id || '-'}</p>
                            </div>
                            <div>
                                <label className="text-sm text-gray-500">Client</label>
                                <p className="font-medium">{selectedProject.client_name || '-'}</p>
                            </div>
                            <div>
                                <label className="text-sm text-gray-500">Manager</label>
                                <p className="font-medium">{selectedProject.manager_name || '-'}</p>
                            </div>
                            <div>
                                <label className="text-sm text-gray-500">Status</label>
                                <p className="font-medium">
                                    <span className={`px-2 py-1 text-xs rounded-full ${
                                        selectedProject.status === 'Active' 
                                            ? 'bg-green-100 text-green-800' 
                                            : 'bg-gray-100 text-gray-800'
                                    }`}>
                                        {selectedProject.status || 'Active'}
                                    </span>
                                </p>
                            </div>
                        </div>
                        <div className="mt-6">
                            <button
                                onClick={() => setShowViewModal(false)}
                                className="w-full bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400 transition"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Assign Employee Modal */}
            {showAssignModal && selectedProject && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h3 className="text-xl font-bold mb-4">Assign Employee to {selectedProject.name}</h3>
                        <form onSubmit={handleAssignEmployee}>
                            <div className="mb-4">
                                <label className="block text-gray-700 text-sm font-bold mb-2">
                                    Select Employee *
                                </label>
                                <select
                                    required
                                    value={assignmentData.employee_id}
                                    onChange={(e) => setAssignmentData({ ...assignmentData, employee_id: parseInt(e.target.value) })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                                >
                                    <option value="">Choose an employee</option>
                                    {employees.map((emp) => (
                                        <option key={emp.id} value={emp.id}>
                                            {emp.name} ({emp.employee_id})
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div className="mb-4">
                                <label className="block text-gray-700 text-sm font-bold mb-2">
                                    Allocation % *
                                </label>
                                <input
                                    type="number"
                                    required
                                    min="0"
                                    max="100"
                                    value={assignmentData.percentage_allocation}
                                    onChange={(e) => setAssignmentData({ ...assignmentData, percentage_allocation: parseInt(e.target.value) })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                                />
                            </div>
                            <div className="mb-4">
                                <label className="flex items-center">
                                    <input
                                        type="checkbox"
                                        checked={assignmentData.is_primary}
                                        onChange={(e) => setAssignmentData({ ...assignmentData, is_primary: e.target.checked })}
                                        className="mr-2"
                                    />
                                    <span className="text-gray-700 text-sm">Primary Project</span>
                                </label>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    type="submit"
                                    className="flex-1 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition"
                                >
                                    Assign
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setShowAssignModal(false)}
                                    className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400 transition"
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ProjectsManagement;
