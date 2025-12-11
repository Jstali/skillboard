import React from 'react';

const ReconciliationPlaceholder: React.FC = () => {
    return (
        <div className="p-6 max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">HRMS Reconciliation</h2>

            <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-8 text-center">
                <div className="text-6xl mb-4">🔄</div>
                <h3 className="text-2xl font-semibold text-blue-900 mb-3">Coming Soon</h3>
                <p className="text-blue-800 mb-6 max-w-2xl mx-auto">
                    This module will be available after HRMS integration is complete. It will allow you to:
                </p>

                <div className="bg-white rounded-lg p-6 text-left max-w-2xl mx-auto mb-6">
                    <h4 className="font-semibold text-gray-800 mb-3">Planned Features:</h4>
                    <ul className="space-y-2 text-gray-700">
                        <li className="flex items-start">
                            <span className="text-green-600 mr-2">✓</span>
                            <span>Compare Skillboard data with HRMS data</span>
                        </li>
                        <li className="flex items-start">
                            <span className="text-green-600 mr-2">✓</span>
                            <span>Identify discrepancies in employee information</span>
                        </li>
                        <li className="flex items-start">
                            <span className="text-green-600 mr-2">✓</span>
                            <span>Sync project assignments from HRMS</span>
                        </li>
                        <li className="flex items-start">
                            <span className="text-green-600 mr-2">✓</span>
                            <span>Reconcile organizational structure changes</span>
                        </li>
                        <li className="flex items-start">
                            <span className="text-green-600 mr-2">✓</span>
                            <span>View reconciliation reports and logs</span>
                        </li>
                        <li className="flex items-start">
                            <span className="text-green-600 mr-2">✓</span>
                            <span>Automated data synchronization scheduling</span>
                        </li>
                    </ul>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 max-w-2xl mx-auto">
                    <p className="text-sm text-yellow-800">
                        <strong>Note:</strong> HRMS integration is currently in the planning phase. This reconciliation
                        module will be activated once the HRMS API connection is established.
                    </p>
                </div>
            </div>

            <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                    <div className="text-3xl mb-2">📊</div>
                    <h4 className="font-semibold text-gray-800 mb-2">Data Comparison</h4>
                    <p className="text-sm text-gray-600">
                        Automatically compare employee data between Skillboard and HRMS
                    </p>
                </div>
                <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                    <div className="text-3xl mb-2">🔄</div>
                    <h4 className="font-semibold text-gray-800 mb-2">Auto Sync</h4>
                    <p className="text-sm text-gray-600">
                        Schedule automatic synchronization of project and org data
                    </p>
                </div>
                <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                    <div className="text-3xl mb-2">📝</div>
                    <h4 className="font-semibold text-gray-800 mb-2">Audit Trail</h4>
                    <p className="text-sm text-gray-600">
                        Track all reconciliation activities and data changes
                    </p>
                </div>
            </div>
        </div>
    );
};

export default ReconciliationPlaceholder;
