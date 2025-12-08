import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { PageHeader } from '../components/PageHeader';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Skill {
    id: number;
    name: string;
    category: string;
    description: string;
}

interface Template {
    id: number;
    name: string;
    skills: Skill[];
}

interface AssignmentDetail {
    id: number;
    template: Template;
    status: string;
    assigned_at: string;
}

interface SkillResponse {
    skill_id: number;
    level: string;
    years_experience: number;
    notes: string;
}

const SKILL_LEVELS = ['Beginner', 'Developing', 'Intermediate', 'Advanced', 'Expert'];

const FillTemplate: React.FC = () => {
    const { assignmentId } = useParams<{ assignmentId: string }>();
    const navigate = useNavigate();

    const [assignment, setAssignment] = useState<AssignmentDetail | null>(null);
    const [categories, setCategories] = useState<string[]>([]);
    const [selectedCategory, setSelectedCategory] = useState<string>('');
    const [skillResponses, setSkillResponses] = useState<Record<number, SkillResponse>>({});

    const [loading, setLoading] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showConfirmDialog, setShowConfirmDialog] = useState(false);

    useEffect(() => {
        if (assignmentId) {
            loadAssignment();
            loadCategories();
        }
    }, [assignmentId]);

    const loadAssignment = async () => {
        setLoading(true);
        setError(null);

        try {
            const token = localStorage.getItem('auth_token');
            const headers = { Authorization: `Bearer ${token}` };

            const res = await axios.get(
                `${API_URL}/api/employee/assignments/${assignmentId}`,
                { headers }
            );
            setAssignment(res.data);

            // Initialize skill responses
            const initialResponses: Record<number, SkillResponse> = {};
            res.data.template.skills.forEach((skill: Skill) => {
                initialResponses[skill.id] = {
                    skill_id: skill.id,
                    level: '',
                    years_experience: 0,
                    notes: ''
                };
            });
            setSkillResponses(initialResponses);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load assignment');
        } finally {
            setLoading(false);
        }
    };

    const loadCategories = async () => {
        try {
            const token = localStorage.getItem('auth_token');
            const headers = { Authorization: `Bearer ${token}` };

            const res = await axios.get(`${API_URL}/api/categories`, { headers });
            setCategories(res.data.map((c: any) => c.name));
        } catch (err) {
            console.error('Failed to load categories:', err);
        }
    };

    const handleSkillChange = (skillId: number, field: keyof SkillResponse, value: any) => {
        setSkillResponses(prev => ({
            ...prev,
            [skillId]: {
                ...prev[skillId],
                [field]: value
            }
        }));
    };

    const validateForm = (): boolean => {

        // Check if at least some skills have levels
        const hasAnyLevel = Object.values(skillResponses).some(r => r.level !== '');
        if (!hasAnyLevel) {
            setError('Please rate at least one skill');
            return false;
        }

        return true;
    };

    const handleSubmit = () => {
        if (!validateForm()) return;
        setShowConfirmDialog(true);
    };

    const confirmSubmit = async () => {
        setSubmitting(true);
        setError(null);
        setShowConfirmDialog(false);

        try {
            const token = localStorage.getItem('auth_token');
            const headers = { Authorization: `Bearer ${token}` };

            // Filter out skills without levels
            const responses = Object.values(skillResponses).filter(r => r.level !== '');

            await axios.post(
                `${API_URL}/api/employee/assignments/${assignmentId}/submit`,
                {
                    employee_category: 'General',
                    responses: responses
                },
                { headers }
            );

            // Success - navigate back to assignments
            navigate('/assignments', {
                state: { message: 'Template submitted successfully!' }
            });
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to submit template');
            setSubmitting(false);
        }
    };

    // Group skills by category
    const groupedSkills = assignment?.template.skills.reduce((acc, skill) => {
        const category = skill.category || 'Uncategorized';
        if (!acc[category]) {
            acc[category] = [];
        }
        acc[category].push(skill);
        return acc;
    }, {} as Record<string, Skill[]>) || {};

    const getCompletionPercentage = () => {
        const total = Object.keys(skillResponses).length;
        const filled = Object.values(skillResponses).filter(r => r.level !== '').length;
        return total > 0 ? Math.round((filled / total) * 100) : 0;
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#F6F2F4] flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading template...</p>
                </div>
            </div>
        );
    }

    if (!assignment) {
        return (
            <div className="min-h-screen bg-[#F6F2F4] flex items-center justify-center">
                <div className="text-center">
                    <p className="text-gray-600">Assignment not found</p>
                    <button
                        onClick={() => navigate('/assignments')}
                        className="mt-4 text-purple-600 hover:text-purple-800 font-medium"
                    >
                        Back to Assignments
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#F6F2F4]">
            <PageHeader
                title={`Fill Template: ${assignment.template.name}`}
                subtitle="Rate your skills and select your category"
            />

            <div className="max-w-5xl mx-auto px-4 py-6">
                {/* Back Button */}
                <button
                    onClick={() => navigate('/assignments')}
                    className="mb-4 text-purple-600 hover:text-purple-800 font-medium flex items-center gap-2"
                >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    Back to Assignments
                </button>

                {error && (
                    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-800 text-sm">
                        {error}
                    </div>
                )}

                {/* Progress Bar */}
                <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">Completion Progress</span>
                        <span className="text-sm font-semibold text-purple-600">{getCompletionPercentage()}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                            className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${getCompletionPercentage()}%` }}
                        ></div>
                    </div>
                </div>



                {/* Skills by Category */}
                <div className="space-y-4 mb-6">
                    {Object.entries(groupedSkills).map(([category, skills]) => (
                        <div key={category} className="bg-white rounded-lg shadow-sm overflow-hidden">
                            <div className="bg-purple-50 px-6 py-3 border-b border-purple-100">
                                <h3 className="text-lg font-bold text-gray-900">{category}</h3>
                                <p className="text-sm text-gray-600">{skills.length} skills</p>
                            </div>

                            <div className="p-6 space-y-4">
                                {skills.map(skill => (
                                    <div key={skill.id} className="border border-gray-200 rounded-lg p-4">
                                        <div className="mb-3">
                                            <h4 className="font-semibold text-gray-900 mb-1">{skill.name}</h4>
                                            {skill.description && (
                                                <p className="text-sm text-gray-600">{skill.description}</p>
                                            )}
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            {/* Skill Level */}
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                                    Skill Level *
                                                </label>
                                                <select
                                                    value={skillResponses[skill.id]?.level || ''}
                                                    onChange={(e) => handleSkillChange(skill.id, 'level', e.target.value)}
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                                                >
                                                    <option value="">Not Rated</option>
                                                    {SKILL_LEVELS.map(level => (
                                                        <option key={level} value={level}>{level}</option>
                                                    ))}
                                                </select>
                                            </div>

                                            {/* Notes */}
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                                    Notes (Optional)
                                                </label>
                                                <input
                                                    type="text"
                                                    value={skillResponses[skill.id]?.notes || ''}
                                                    onChange={(e) => handleSkillChange(skill.id, 'notes', e.target.value)}
                                                    placeholder="Add notes..."
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Submit Button */}
                <div className="bg-white rounded-lg shadow-sm p-6 sticky bottom-4">
                    <div className="flex items-center justify-between">
                        <div className="text-sm text-gray-600">
                            <span className="font-medium">{Object.values(skillResponses).filter(r => r.level !== '').length}</span> of{' '}
                            <span className="font-medium">{Object.keys(skillResponses).length}</span> skills rated
                        </div>
                        <button
                            onClick={handleSubmit}
                            disabled={submitting}
                            className="px-6 py-3 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center gap-2"
                        >
                            {submitting ? (
                                <>
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                    Submitting...
                                </>
                            ) : (
                                <>
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                    Submit Template
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {/* Confirmation Dialog */}
            {showConfirmDialog && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">Confirm Submission</h3>
                        <p className="text-gray-600 mb-6">
                            Are you sure you want to submit this template? You have rated{' '}
                            <span className="font-semibold">{Object.values(skillResponses).filter(r => r.level !== '').length}</span>{' '}
                            skills.
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowConfirmDialog(false)}
                                className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 font-medium"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={confirmSubmit}
                                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 font-medium"
                            >
                                Confirm Submit
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default FillTemplate;
