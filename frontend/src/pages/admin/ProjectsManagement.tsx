import React, { useState, useEffect } from 'react';
import { projectsApi, Project, ProjectCreate, Employee, adminDashboardApi, AssignEmployeeToProject, EmployeeProjectAssignment } from '../../services/api';

const ProjectsManagement: React.FC = () => {
    const [projects, setProjects] = useState<Project[]>([]);
    const [employees, setEmployees] = useState<Employee[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showAssignModal, setShowAssignModal] = useState(false);
    const [selectedProject, setSelectedProject] = useState<Project | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Form states
    const [newProject, setNewProject] = useState<ProjectCreate>({
        name: '',
        description: '',
        capability_required: '',
    });

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
            const data = await projectsApi.list();
            setProjects(data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load projects');
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

    const handleCreateProject = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await projectsApi.create(newProject);
            setSuccess('Project created successfully!');
            setShowCreateModal(false);
            setNewProject({ name: '', description: '', capability_required: '' });
            loadProjects();
            setTimeout(() => setSuccess(null), 3000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to create project');
        }
    };

    const handleDeleteProject = async (id: number) => {
        if (!confirm('Are you sure you want to delete this project?')) return;

        try {
            await projectsApi.delete(id);
            setSuccess('Project deleted successfully!');
            loadProjects();
            setTimeout(() => setSuccess(null), 3000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to delete project');
        }
    };

    const handleAssignEmployee = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedProject) return;

        try {
            await projectsApi.assignEmployee(selectedProject.id, assignmentData);
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

    const openAssignModal = (project: Project) => {
        setSelectedProject(project);
        setAssignmentData({
            ...assignmentData,
            project_id: project.id,
        });
        setShowAssignModal(true);
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="text-gray-600">Loading projects...</div>
            </div>
        );
    }

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">Projects Management</h2>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
                >
                    + Create Project
                </button>
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

            {/* Projects List */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {projects.length === 0 ? (
                    <div className="col-span-full text-center py-12 text-gray-500">
                        No projects found. Create your first project to get started.
                    </div>
                ) : (
                    projects.map((project) => (
                        <div key={project.id} className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                            <h3 className="text-lg font-semibold text-gray-800 mb-2">{project.name}</h3>
                            <p className="text-gray-600 text-sm mb-3">{project.description || 'No description'}</p>
                            {project.capability_required && (
                                <div className="mb-3">
                                    <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                                        {project.capability_required}
                                    </span>
                                </div>
                            )}
                            <div className="text-xs text-gray-500 mb-4">
                                Created: {new Date(project.created_at).toLocaleDateString()}
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => openAssignModal(project)}
                                    className="flex-1 bg-green-600 text-white px-3 py-2 rounded text-sm hover:bg-green-700 transition"
                                >
                                    Assign Employee
                                </button>
                                <button
                                    onClick={() => handleDeleteProject(project.id)}
                                    className="bg-red-600 text-white px-3 py-2 rounded text-sm hover:bg-red-700 transition"
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Create Project Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h3 className="text-xl font-bold mb-4">Create New Project</h3>
                        <form onSubmit={handleCreateProject}>
                            <div className="mb-4">
                                <label className="block text-gray-700 text-sm font-bold mb-2">
                                    Project Name *
                                </label>
                                <input
                                    type="text"
                                    required
                                    value={newProject.name}
                                    onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                                    placeholder="Enter project name"
                                />
                            </div>
                            <div className="mb-4">
                                <label className="block text-gray-700 text-sm font-bold mb-2">
                                    Description
                                </label>
                                <textarea
                                    value={newProject.description}
                                    onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                                    placeholder="Enter project description"
                                    rows={3}
                                />
                            </div>
                            <div className="mb-4">
                                <label className="block text-gray-700 text-sm font-bold mb-2">
                                    Capability Required
                                </label>
                                <input
                                    type="text"
                                    value={newProject.capability_required}
                                    onChange={(e) => setNewProject({ ...newProject, capability_required: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                                    placeholder="e.g., Cloud & DevOps"
                                />
                            </div>
                            <div className="flex gap-2">
                                <button
                                    type="submit"
                                    className="flex-1 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
                                >
                                    Create
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setShowCreateModal(false)}
                                    className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400 transition"
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
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
