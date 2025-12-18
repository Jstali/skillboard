import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { PageHeader } from '../components/PageHeader';
import { coursesApi, templateAssessmentApi, CourseDetails, AssessableEmployee } from '../services/api';
import { AssignCourseModal } from '../components/AssignCourseModal';
import { BookOpen, CheckCircle, X, AlertCircle } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface SkillGap {
    skill_id: number;
    skill_name: string;
    skill_category: string;
    required_level: string;
    employee_level: string | null;
    gap_status: string;
    gap_value: number;
}

interface GapDetails {
    assignment_id: number;
    employee_id: number;
    employee_name: string;
    template_id: number;
    template_name: string;
    category_hr: string;
    employee_category: string;
    gaps: SkillGap[];
}

const GapDetailsView: React.FC = () => {
    const { assignmentId } = useParams<{ assignmentId: string }>();
    const navigate = useNavigate();
    const [details, setDetails] = useState<GapDetails | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    
    // Course assignment state
    const [showCourseModal, setShowCourseModal] = useState(false);
    const [selectedSkillForCourse, setSelectedSkillForCourse] = useState<SkillGap | null>(null);
    const [coursesForSkill, setCoursesForSkill] = useState<CourseDetails[]>([]);
    const [selectedCourse, setSelectedCourse] = useState<CourseDetails | null>(null);
    const [employees, setEmployees] = useState<AssessableEmployee[]>([]);
    const [loadingCourses, setLoadingCourses] = useState(false);

    useEffect(() => {
        if (assignmentId) {
            loadGapDetails();
        }
        // Load assessable employees for course assignment
        loadEmployees();
    }, [assignmentId]);

    const loadEmployees = async () => {
        try {
            const emps = await templateAssessmentApi.getAssessableEmployees();
            setEmployees(emps);
        } catch (err) {
            console.error('Failed to load employees:', err);
        }
    };

    const handleAssignCourse = async (gap: SkillGap) => {
        setSelectedSkillForCourse(gap);
        setLoadingCourses(true);
        
        try {
            const courses = await coursesApi.getCoursesForSkill(gap.skill_id);
            setCoursesForSkill(courses);
            
            if (courses.length === 0) {
                setError(`No courses available for skill "${gap.skill_name}"`);
                setTimeout(() => setError(null), 5000);
            } else if (courses.length === 1) {
                // If only one course, select it directly
                setSelectedCourse(courses[0]);
                setShowCourseModal(true);
            } else {
                // Show course selection
                setShowCourseModal(true);
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load courses for this skill');
            setTimeout(() => setError(null), 5000);
        } finally {
            setLoadingCourses(false);
        }
    };

    const handleSelectCourse = (course: CourseDetails) => {
        setSelectedCourse(course);
    };

    const handleAssignSuccess = (message: string) => {
        setSuccessMessage(message);
        setShowCourseModal(false);
        setSelectedCourse(null);
        setSelectedSkillForCourse(null);
        setCoursesForSkill([]);
        setTimeout(() => setSuccessMessage(null), 5000);
    };

    const handleAssignError = (message: string) => {
        setError(message);
        setTimeout(() => setError(null), 5000);
    };

    const closeCourseModal = () => {
        setShowCourseModal(false);
        setSelectedCourse(null);
        setSelectedSkillForCourse(null);
        setCoursesForSkill([]);
    };

    const loadGapDetails = async () => {
        setLoading(true);
        setError(null);

        try {
            const token = localStorage.getItem('token');
            const headers = { Authorization: `Bearer ${token}` };

            const res = await axios.get(
                `${API_URL}/api/admin/skill-gaps/${assignmentId}/details`,
                { headers }
            );
            setDetails(res.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load gap details');
        } finally {
            setLoading(false);
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'Gap':
                return <span className="text-2xl">🔴</span>;
            case 'Met':
                return <span className="text-2xl">🟢</span>;
            case 'Exceeded':
                return <span className="text-2xl">🔵</span>;
            default:
                return <span className="text-2xl">⚪</span>;
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'Gap':
                return 'bg-red-50 border-red-200 text-red-800';
            case 'Met':
                return 'bg-green-50 border-green-200 text-green-800';
            case 'Exceeded':
                return 'bg-blue-50 border-blue-200 text-blue-800';
            default:
                return 'bg-gray-50 border-gray-200 text-gray-800';
        }
    };

    const getLevelBadgeColor = (level: string | null) => {
        if (!level) return 'bg-gray-100 text-gray-600';

        switch (level) {
            case 'Expert':
                return 'bg-purple-100 text-purple-800';
            case 'Advanced':
                return 'bg-orange-100 text-orange-800';
            case 'Intermediate':
                return 'bg-yellow-100 text-yellow-800';
            case 'Developing':
                return 'bg-blue-100 text-blue-800';
            case 'Beginner':
                return 'bg-green-100 text-green-800';
            default:
                return 'bg-gray-100 text-gray-600';
        }
    };

    // Group gaps by category
    const groupedGaps = details?.gaps.reduce((acc, gap) => {
        const category = gap.skill_category || 'Uncategorized';
        if (!acc[category]) {
            acc[category] = [];
        }
        acc[category].push(gap);
        return acc;
    }, {} as Record<string, SkillGap[]>) || {};

    // Calculate statistics
    const totalGaps = details?.gaps.filter(g => g.gap_status === 'Gap').length || 0;
    const totalMet = details?.gaps.filter(g => g.gap_status === 'Met').length || 0;
    const totalExceeded = details?.gaps.filter(g => g.gap_status === 'Exceeded').length || 0;
    const totalSkills = details?.gaps.length || 0;

    return (
        <div className="min-h-screen bg-[#F6F2F4]">
            <PageHeader
                title="Skill Gap Details"
                subtitle="Detailed skill-by-skill gap analysis"
            />

            <div className="max-w-7xl mx-auto px-4 py-6">
                {/* Back Button */}
                <button
                    onClick={() => navigate('/admin/skill-gaps')}
                    className="mb-4 text-purple-600 hover:text-purple-800 font-medium flex items-center gap-2"
                >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    Back to Gap Analysis
                </button>

                {/* Success Message */}
                {successMessage && (
                    <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-green-600" />
                        <span className="text-green-800">{successMessage}</span>
                        <button onClick={() => setSuccessMessage(null)} className="ml-auto">
                            <X className="w-4 h-4 text-green-600" />
                        </button>
                    </div>
                )}

                {/* Error Message */}
                {error && (
                    <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
                        <AlertCircle className="w-5 h-5 text-red-600" />
                        <span className="text-red-800">{error}</span>
                        <button onClick={() => setError(null)} className="ml-auto">
                            <X className="w-4 h-4 text-red-600" />
                        </button>
                    </div>
                )}

                {loading ? (
                    <div className="text-center py-12 text-gray-500">Loading gap details...</div>
                ) : !details ? (
                    <div className="text-center py-12 text-gray-500">No data found</div>
                ) : (
                    <>
                        {/* Employee Info Card */}
                        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <h3 className="text-lg font-bold text-gray-900 mb-4">Employee Information</h3>
                                    <dl className="space-y-2">
                                        <div className="flex justify-between">
                                            <dt className="text-sm font-medium text-gray-600">Name:</dt>
                                            <dd className="text-sm font-semibold text-gray-900">{details.employee_name}</dd>
                                        </div>
                                        <div className="flex justify-between">
                                            <dt className="text-sm font-medium text-gray-600">Template:</dt>
                                            <dd className="text-sm text-gray-900">{details.template_name}</dd>
                                        </div>
                                        <div className="flex justify-between">
                                            <dt className="text-sm font-medium text-gray-600">HR Category:</dt>
                                            <dd className="text-sm text-gray-900">{details.category_hr}</dd>
                                        </div>
                                        <div className="flex justify-between">
                                            <dt className="text-sm font-medium text-gray-600">Employee Category:</dt>
                                            <dd className={`text-sm font-medium ${details.category_hr !== details.employee_category ? 'text-orange-600' : 'text-gray-900'}`}>
                                                {details.employee_category}
                                                {details.category_hr !== details.employee_category && (
                                                    <span className="ml-2 text-xs bg-orange-100 px-2 py-0.5 rounded">Category Mismatch</span>
                                                )}
                                            </dd>
                                        </div>
                                    </dl>
                                </div>

                                <div>
                                    <h3 className="text-lg font-bold text-gray-900 mb-4">Gap Summary</h3>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="bg-gray-50 rounded-lg p-3">
                                            <p className="text-xs text-gray-600">Total Skills</p>
                                            <p className="text-2xl font-bold text-gray-900">{totalSkills}</p>
                                        </div>
                                        <div className="bg-red-50 rounded-lg p-3">
                                            <p className="text-xs text-red-600">Gaps</p>
                                            <p className="text-2xl font-bold text-red-600">{totalGaps}</p>
                                        </div>
                                        <div className="bg-green-50 rounded-lg p-3">
                                            <p className="text-xs text-green-600">Met</p>
                                            <p className="text-2xl font-bold text-green-600">{totalMet}</p>
                                        </div>
                                        <div className="bg-blue-50 rounded-lg p-3">
                                            <p className="text-xs text-blue-600">Exceeded</p>
                                            <p className="text-2xl font-bold text-blue-600">{totalExceeded}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Skill Gaps by Category */}
                        <div className="space-y-4">
                            {Object.entries(groupedGaps).map(([category, gaps]) => (
                                <div key={category} className="bg-white rounded-lg shadow-sm overflow-hidden">
                                    <div className="bg-gray-50 px-6 py-3 border-b border-gray-200">
                                        <h3 className="text-lg font-bold text-gray-900">{category}</h3>
                                        <p className="text-sm text-gray-500">{gaps.length} skills</p>
                                    </div>

                                    <div className="p-6">
                                        <div className="space-y-3">
                                            {gaps.map(gap => (
                                                <div
                                                    key={gap.skill_id}
                                                    className={`border rounded-lg p-4 ${getStatusColor(gap.gap_status)}`}
                                                >
                                                    <div className="flex items-start justify-between">
                                                        <div className="flex items-start gap-3 flex-1">
                                                            <div className="mt-1">
                                                                {getStatusIcon(gap.gap_status)}
                                                            </div>
                                                            <div className="flex-1">
                                                                <h4 className="font-semibold text-gray-900">{gap.skill_name}</h4>
                                                                <div className="mt-2 flex items-center gap-4 text-sm">
                                                                    <div>
                                                                        <span className="text-gray-600">Required: </span>
                                                                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${getLevelBadgeColor(gap.required_level)}`}>
                                                                            {gap.required_level}
                                                                        </span>
                                                                    </div>
                                                                    <div>
                                                                        <span className="text-gray-600">Employee: </span>
                                                                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${getLevelBadgeColor(gap.employee_level)}`}>
                                                                            {gap.employee_level || 'Not Rated'}
                                                                        </span>
                                                                    </div>
                                                                    {gap.gap_value !== 0 && (
                                                                        <div>
                                                                            <span className="text-gray-600">Gap: </span>
                                                                            <span className={`font-semibold ${gap.gap_value < 0 ? 'text-red-600' : 'text-blue-600'}`}>
                                                                                {gap.gap_value > 0 ? '+' : ''}{gap.gap_value}
                                                                            </span>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            {/* Assign Course Button - Only show for gaps */}
                                                            {gap.gap_status === 'Gap' && (
                                                                <button
                                                                    onClick={() => handleAssignCourse(gap)}
                                                                    disabled={loadingCourses && selectedSkillForCourse?.skill_id === gap.skill_id}
                                                                    className="px-3 py-1 bg-blue-600 text-white text-xs font-medium rounded-full hover:bg-blue-700 transition-colors flex items-center gap-1 disabled:opacity-50"
                                                                    title="Assign a course to address this skill gap"
                                                                >
                                                                    {loadingCourses && selectedSkillForCourse?.skill_id === gap.skill_id ? (
                                                                        <svg className="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                                        </svg>
                                                                    ) : (
                                                                        <BookOpen className="w-3 h-3" />
                                                                    )}
                                                                    Assign Course
                                                                </button>
                                                            )}
                                                            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${gap.gap_status === 'Gap' ? 'bg-red-100 text-red-800' :
                                                                gap.gap_status === 'Met' ? 'bg-green-100 text-green-800' :
                                                                    'bg-blue-100 text-blue-800'
                                                                }`}>
                                                                {gap.gap_status}
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </div>

            {/* Course Selection Modal - When multiple courses available */}
            {showCourseModal && !selectedCourse && coursesForSkill.length > 1 && selectedSkillForCourse && (
                <div className="fixed inset-0 z-50 overflow-y-auto">
                    <div 
                        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
                        onClick={closeCourseModal}
                    />
                    <div className="flex min-h-full items-center justify-center p-4">
                        <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full">
                            <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-blue-600 to-blue-700 rounded-t-lg">
                                <div>
                                    <h2 className="text-lg font-semibold text-white">Select Course</h2>
                                    <p className="text-sm text-blue-100">For skill: {selectedSkillForCourse.skill_name}</p>
                                </div>
                                <button onClick={closeCourseModal} className="text-white hover:text-blue-200">
                                    <X className="w-6 h-6" />
                                </button>
                            </div>
                            <div className="p-4 max-h-96 overflow-y-auto">
                                <div className="space-y-3">
                                    {coursesForSkill.map(course => (
                                        <div
                                            key={course.id}
                                            onClick={() => handleSelectCourse(course)}
                                            className="p-4 border rounded-lg cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-colors"
                                        >
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <h3 className="font-medium text-gray-900">{course.title}</h3>
                                                    {course.description && (
                                                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">{course.description}</p>
                                                    )}
                                                </div>
                                                {course.is_mandatory && (
                                                    <span className="px-2 py-0.5 bg-red-100 text-red-800 text-xs rounded-full">
                                                        Mandatory
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <div className="p-4 border-t bg-gray-50 rounded-b-lg">
                                <button
                                    onClick={closeCourseModal}
                                    className="w-full px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Assign Course Modal */}
            {showCourseModal && selectedCourse && (
                <AssignCourseModal
                    course={selectedCourse}
                    employees={employees}
                    skillId={selectedSkillForCourse?.skill_id}
                    onClose={closeCourseModal}
                    onSuccess={handleAssignSuccess}
                    onError={handleAssignError}
                />
            )}
        </div>
    );
};

export default GapDetailsView;
