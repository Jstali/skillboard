import React from 'react';
import { useNavigate } from 'react-router-dom';

const HRMSTestPage: React.FC = () => {
    const navigate = useNavigate();

    const testPages = [
        {
            name: 'HRMS Organization',
            path: '/test/hrms-organization',
            description: 'View Locations, Delivery Managers, and Projects from HRMS.',
            icon: '🏢',
        },
        {
            name: 'Projects Management',
            path: '/test/projects',
            description: 'View and manage projects from HRMS. Assign employees to projects.',
            icon: '📁',
        },
        {
            name: 'Capability Owners',
            path: '/test/capability-owners',
            description: 'Manage capability groups and assign capability partners.',
            icon: '👥',
        },
        {
            name: 'Org Structure Upload',
            path: '/test/org-structure',
            description: 'Upload organizational hierarchy via Excel/CSV file.',
            icon: '📊',
        },
        {
            name: 'Level Movement Approvals',
            path: '/test/level-movement',
            description: 'Review and approve/reject employee promotion requests.',
            icon: '⬆️',
        },
        {
            name: 'Reconciliation',
            path: '/test/reconciliation',
            description: 'HRMS data reconciliation (placeholder for future integration).',
            icon: '🔄',
        },
    ];

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-6xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">
                        HRMS Pre-Integration - Component Testing
                    </h1>
                    <p className="text-gray-600">
                        Test each component individually before integration into the HR Dashboard
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {testPages.map((page) => (
                        <div
                            key={page.path}
                            className="bg-white rounded-lg shadow-md p-6 border border-gray-200 hover:shadow-lg transition cursor-pointer"
                            onClick={() => navigate(page.path)}
                        >
                            <div className="text-4xl mb-3">{page.icon}</div>
                            <h3 className="text-lg font-semibold text-gray-800 mb-2">
                                {page.name}
                            </h3>
                            <p className="text-sm text-gray-600 mb-4">{page.description}</p>
                            <button className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition">
                                Test Component
                            </button>
                        </div>
                    ))}
                </div>

                <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                    <h3 className="font-semibold text-yellow-900 mb-2">⚠️ Testing Notes</h3>
                    <ul className="text-sm text-yellow-800 space-y-1">
                        <li>• Backend server must be running on port 8000</li>
                        <li>• You must be logged in as an admin user</li>
                        <li>• Some features require existing data (employees, projects, etc.)</li>
                        <li>• Check browser console for any errors</li>
                        <li>• Test all CRUD operations (Create, Read, Update, Delete)</li>
                    </ul>
                </div>

                <div className="mt-6 flex gap-4">
                    <button
                        onClick={() => navigate('/hr/dashboard')}
                        className="flex-1 bg-gray-600 text-white px-4 py-3 rounded-lg hover:bg-gray-700 transition"
                    >
                        ← Back to HR Dashboard
                    </button>
                    <button
                        onClick={() => window.location.reload()}
                        className="flex-1 bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 transition"
                    >
                        🔄 Reload Page
                    </button>
                </div>
            </div>
        </div>
    );
};

export default HRMSTestPage;
