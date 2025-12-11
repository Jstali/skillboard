import React, { useState, useEffect } from 'react';
import { capabilityOwnersApi, CapabilityOwner, CapabilityOwnerCreate, Employee, adminDashboardApi } from '../../services/api';

const CapabilityOwners: React.FC = () => {
    const [capabilityOwners, setCapabilityOwners] = useState<CapabilityOwner[]>([]);
    const [employees, setEmployees] = useState<Employee[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showTeamModal, setShowTeamModal] = useState(false);
    const [selectedCapability, setSelectedCapability] = useState<CapabilityOwner | null>(null);
    const [teamMembers, setTeamMembers] = useState<Employee[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const [newCapability, setNewCapability] = useState<CapabilityOwnerCreate>({
        capability_name: '',
        owner_employee_id: undefined,
    });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [caps, emps] = await Promise.all([
                capabilityOwnersApi.list(),
                adminDashboardApi.getEmployees(),
            ]);
            setCapabilityOwners(caps);
            setEmployees(emps);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load data');
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await capabilityOwnersApi.create(newCapability);
            setSuccess('Capability owner created successfully!');
            setShowCreateModal(false);
            setNewCapability({ capability_name: '', owner_employee_id: undefined });
            loadData();
            setTimeout(() => setSuccess(null), 3000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to create capability owner');
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('Are you sure you want to delete this capability owner?')) return;

        try {
            await capabilityOwnersApi.delete(id);
            setSuccess('Capability owner deleted successfully!');
            loadData();
            setTimeout(() => setSuccess(null), 3000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to delete capability owner');
        }
    };

    const viewTeam = async (capability: CapabilityOwner) => {
        try {
            const team = await capabilityOwnersApi.getEmployees(capability.id);
            setTeamMembers(team);
            setSelectedCapability(capability);
            setShowTeamModal(true);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load team members');
        }
    };

    const getOwnerName = (ownerId?: number) => {
        if (!ownerId) return 'Unassigned';
        const owner = employees.find(e => e.id === ownerId);
        return owner ? owner.name : 'Unknown';
    };

    if (loading) {
        return <div className="flex justify-center items-center h-64">Loading...</div>;
    }

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">Capability Owners</h2>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
                >
                    + Create Capability Owner
                </button>
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

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {capabilityOwners.length === 0 ? (
                    <div className="col-span-full text-center py-12 text-gray-500">
                        No capability owners found. Create one to get started.
                    </div>
                ) : (
                    capabilityOwners.map((cap) => (
                        <div key={cap.id} className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                            <h3 className="text-lg font-semibold text-gray-800 mb-2">{cap.capability_name}</h3>
                            <div className="text-sm text-gray-600 mb-4">
                                <strong>Owner:</strong> {getOwnerName(cap.owner_employee_id)}
                            </div>
                            <div className="text-xs text-gray-500 mb-4">
                                Created: {new Date(cap.created_at).toLocaleDateString()}
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => viewTeam(cap)}
                                    className="flex-1 bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700 transition"
                                >
                                    View Team
                                </button>
                                <button
                                    onClick={() => handleDelete(cap.id)}
                                    className="bg-red-600 text-white px-3 py-2 rounded text-sm hover:bg-red-700 transition"
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Create Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h3 className="text-xl font-bold mb-4">Create Capability Owner</h3>
                        <form onSubmit={handleCreate}>
                            <div className="mb-4">
                                <label className="block text-gray-700 text-sm font-bold mb-2">
                                    Capability Name *
                                </label>
                                <input
                                    type="text"
                                    required
                                    value={newCapability.capability_name}
                                    onChange={(e) => setNewCapability({ ...newCapability, capability_name: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                                    placeholder="e.g., Cloud & DevOps"
                                />
                            </div>
                            <div className="mb-4">
                                <label className="block text-gray-700 text-sm font-bold mb-2">
                                    Assign Owner (Optional)
                                </label>
                                <select
                                    value={newCapability.owner_employee_id || ''}
                                    onChange={(e) => setNewCapability({ ...newCapability, owner_employee_id: e.target.value ? parseInt(e.target.value) : undefined })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                                >
                                    <option value="">Select an owner</option>
                                    {employees.map((emp) => (
                                        <option key={emp.id} value={emp.id}>
                                            {emp.name} ({emp.employee_id})
                                        </option>
                                    ))}
                                </select>
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

            {/* Team Modal */}
            {showTeamModal && selectedCapability && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-2xl">
                        <h3 className="text-xl font-bold mb-4">{selectedCapability.capability_name} - Team Members</h3>
                        {teamMembers.length === 0 ? (
                            <p className="text-gray-500 text-center py-8">No employees assigned to this capability yet.</p>
                        ) : (
                            <div className="max-h-96 overflow-y-auto">
                                <table className="w-full">
                                    <thead className="bg-gray-100">
                                        <tr>
                                            <th className="px-4 py-2 text-left">Employee ID</th>
                                            <th className="px-4 py-2 text-left">Name</th>
                                            <th className="px-4 py-2 text-left">Department</th>
                                            <th className="px-4 py-2 text-left">Band</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {teamMembers.map((emp) => (
                                            <tr key={emp.id} className="border-b">
                                                <td className="px-4 py-2">{emp.employee_id}</td>
                                                <td className="px-4 py-2">{emp.name}</td>
                                                <td className="px-4 py-2">{emp.department || '-'}</td>
                                                <td className="px-4 py-2">{emp.band || '-'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                        <div className="mt-4">
                            <button
                                onClick={() => setShowTeamModal(false)}
                                className="w-full bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400 transition"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CapabilityOwners;
