import React, { useState, useEffect } from 'react';
import { AssignmentDetails, SkillResponseData, employeeAssignmentsApi } from '../services/api';

interface TemplateFillModalProps {
    assignmentId: number;
    onClose: () => void;
    onSuccess: () => void;
}

// Skill level buttons with colors
const SKILL_LEVEL_BUTTONS = [
    { key: 'B', label: 'Beginner', color: 'bg-green-100 text-green-700 border-green-300 hover:bg-green-200', activeColor: 'bg-green-500 text-white border-green-500' },
    { key: 'D', label: 'Developing', color: 'bg-yellow-100 text-yellow-700 border-yellow-300 hover:bg-yellow-200', activeColor: 'bg-yellow-500 text-white border-yellow-500' },
    { key: 'I', label: 'Intermediate', color: 'bg-blue-100 text-blue-700 border-blue-300 hover:bg-blue-200', activeColor: 'bg-blue-500 text-white border-blue-500' },
    { key: 'A', label: 'Advanced', color: 'bg-orange-100 text-orange-700 border-orange-300 hover:bg-orange-200', activeColor: 'bg-orange-500 text-white border-orange-500' },
    { key: 'E', label: 'Expert', color: 'bg-purple-100 text-purple-700 border-purple-300 hover:bg-purple-200', activeColor: 'bg-purple-500 text-white border-purple-500' },
];

export const TemplateFillModal: React.FC<TemplateFillModalProps> = ({
    assignmentId,
    onClose,
    onSuccess
}) => {
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [assignment, setAssignment] = useState<AssignmentDetails | null>(null);
    const [responses, setResponses] = useState<Record<number, SkillResponseData>>({});
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadAssignment();
    }, [assignmentId]);

    const loadAssignment = async () => {
        try {
            setLoading(true);
            const data = await employeeAssignmentsApi.getAssignmentDetails(assignmentId);
            setAssignment(data);

            // Initialize responses for all skills
            const initialResponses: Record<number, SkillResponseData> = {};
            data.template.skills.forEach(skill => {
                initialResponses[skill.id] = {
                    skill_id: skill.id,
                    level: undefined,
                    years_experience: undefined,
                    notes: ''
                };
            });
            setResponses(initialResponses);
        } catch (err: any) {
            const errorMsg = err.response?.data?.detail;
            setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to load assignment');
        } finally {
            setLoading(false);
        }
    };

    const handleLevelChange = (skillId: number, levelKey: string) => {
        // Map key to full level name
        const levelMap: Record<string, string> = {
            'B': 'Beginner',
            'D': 'Developing',
            'I': 'Intermediate',
            'A': 'Advanced',
            'E': 'Expert'
        };
        const level = levelMap[levelKey];

        // Toggle off if clicking the same level
        const currentLevel = responses[skillId]?.level;
        const newLevel = currentLevel === level ? undefined : level;

        setResponses(prev => ({
            ...prev,
            [skillId]: { ...prev[skillId], level: newLevel }
        }));
    };

    const handleNotesChange = (skillId: number, notes: string) => {
        setResponses(prev => ({
            ...prev,
            [skillId]: { ...prev[skillId], notes }
        }));
    };

    const getFilledCount = () => {
        return Object.values(responses).filter(r => r.level).length;
    };

    const canSubmit = () => {
        return getFilledCount() > 0;
    };

    const getLevelKey = (level: string | undefined): string | undefined => {
        if (!level) return undefined;
        const keyMap: Record<string, string> = {
            'Beginner': 'B',
            'Developing': 'D',
            'Intermediate': 'I',
            'Advanced': 'A',
            'Expert': 'E'
        };
        return keyMap[level];
    };

    const handleSubmit = async () => {
        if (!canSubmit()) return;

        try {
            setSubmitting(true);
            setError(null);

            // Filter out skills without levels and format properly
            const filledResponses = Object.values(responses)
                .filter(r => r.level)
                .map(r => ({
                    skill_id: r.skill_id,
                    level: r.level,
                    years_experience: r.years_experience || 0,
                    notes: r.notes || ''
                }));

            console.log('DEBUG: Submitting responses:', filledResponses);

            await employeeAssignmentsApi.submitTemplate(assignmentId, {
                employee_category: 'General',
                responses: filledResponses
            });

            onSuccess();
            onClose();
        } catch (err: any) {
            const errorMsg = err.response?.data?.detail;
            setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg) || 'Failed to submit template');
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-xl p-8">
                    <div className="flex items-center gap-3">
                        <svg className="animate-spin h-6 w-6 text-purple-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span className="text-gray-700">Loading template...</span>
                    </div>
                </div>
            </div>
        );
    }

    if (!assignment) {
        return null;
    }

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-purple-600 to-purple-700">
                    <div className="flex justify-between items-start">
                        <div>
                            <h2 className="text-xl font-semibold text-white">{assignment.template.name}</h2>
                            <p className="text-purple-100 text-sm mt-1">
                                {getFilledCount()} of {assignment.template.skills.length} skills filled
                            </p>
                        </div>
                        <button
                            onClick={onClose}
                            className="text-white hover:text-purple-100 transition-colors"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    {error && (
                        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                            {error}
                        </div>
                    )}

                    {/* Legend */}
                    <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                        <h3 className="text-sm font-medium text-gray-700 mb-3">Skill Level Legend</h3>
                        <div className="flex flex-wrap gap-4">
                            {SKILL_LEVEL_BUTTONS.map(btn => (
                                <div key={btn.key} className="flex items-center gap-2">
                                    <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm border-2 ${btn.color}`}>
                                        {btn.key}
                                    </span>
                                    <span className="text-sm text-gray-600">{btn.label}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Skills List */}
                    <div className="space-y-3">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4">Skills Assessment</h3>

                        {assignment.template.skills.map((skill, index) => {
                            const selectedKey = getLevelKey(responses[skill.id]?.level);

                            return (
                                <div key={skill.id} className="border border-gray-200 rounded-lg p-4 hover:border-purple-300 transition-colors">
                                    <div className="flex flex-col md:flex-row md:items-center gap-4">
                                        {/* Skill Name */}
                                        <div className="flex-1 min-w-0">
                                            <span className="font-medium text-gray-900">
                                                {index + 1}. {skill.name}
                                            </span>
                                            {skill.category && (
                                                <span className="ml-2 text-xs text-gray-500">({skill.category})</span>
                                            )}
                                        </div>

                                        {/* Level Buttons */}
                                        <div className="flex items-center gap-2">
                                            {SKILL_LEVEL_BUTTONS.map(btn => {
                                                const isSelected = selectedKey === btn.key;
                                                return (
                                                    <button
                                                        key={btn.key}
                                                        onClick={() => handleLevelChange(skill.id, btn.key)}
                                                        className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm border-2 transition-all duration-200 ${isSelected ? btn.activeColor : btn.color
                                                            }`}
                                                        title={btn.label}
                                                    >
                                                        {btn.key}
                                                    </button>
                                                );
                                            })}
                                        </div>

                                        {/* Notes - Compact */}
                                        <div className="md:w-48">
                                            <input
                                                type="text"
                                                value={responses[skill.id]?.notes || ''}
                                                onChange={(e) => handleNotesChange(skill.id, e.target.value)}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                                                placeholder="Notes (optional)"
                                            />
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-between items-center">
                    <div className="text-sm text-gray-600">
                        {getFilledCount() === 0 && <span className="text-red-500">Please fill at least one skill</span>}
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={onClose}
                            className="px-5 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 font-medium transition-colors"
                            disabled={submitting}
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSubmit}
                            disabled={!canSubmit() || submitting}
                            className="px-5 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors flex items-center gap-2"
                        >
                            {submitting && (
                                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                            )}
                            Submit Template
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
