import React from 'react';
import { AssignedTemplate } from '../services/api';

interface AssignedTemplateCardProps {
    assignment: AssignedTemplate;
    onFill: () => void;
}

export const AssignedTemplateCard: React.FC<AssignedTemplateCardProps> = ({
    assignment,
    onFill
}) => {
    const statusColors: Record<string, string> = {
        'Pending': 'bg-yellow-100 text-yellow-800',
        'In Progress': 'bg-blue-100 text-blue-800',
        'Completed': 'bg-green-100 text-green-800',
    };

    const statusColor = statusColors[assignment.status] || 'bg-gray-100 text-gray-800';

    // Format template name by replacing underscores with spaces
    const formatTemplateName = (name: string) => {
        return name.replace(/_/g, ' ');
    };

    return (
        <div className="border border-gray-200 rounded-lg p-4 hover:border-purple-300 transition-colors">
            <div className="flex justify-between items-start">
                <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{formatTemplateName(assignment.template_name)}</h3>
                    <p className="text-sm text-gray-500 mt-1">
                        Assigned: {new Date(assignment.assigned_at).toLocaleDateString()}
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusColor}`}>
                        {assignment.status}
                    </span>
                    {assignment.status !== 'Completed' && (
                        <button
                            onClick={onFill}
                            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm font-medium transition-colors"
                        >
                            {assignment.status === 'Pending' ? 'Start' : 'Continue'}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};
