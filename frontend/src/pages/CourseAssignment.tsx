/** Course Assignment Screen for Managers
 * 
 * Allows Line Managers and Delivery Managers to:
 * - View available courses with filters
 * - Assign courses to employees
 * - Track course assignments
 * 
 * Requirements: 2.1, 2.2, 2.4, 3.1, 3.3, 3.5
 */
import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authApi, coursesApi, templateAssessmentApi, CourseDetails, AssessableEmployee } from '../services/api';
import { PageHeader } from '../components/PageHeader';
import { BookOpen, Search, Filter, Users, ExternalLink, CheckCircle, AlertCircle, X, Calendar, FileText } from 'lucide-react';
import { AssignCourseModal } from '../components/AssignCourseModal';

export const CourseAssignment: React.FC = () => {
  const [courses, setCourses] = useState<CourseDetails[]>([]);
  const [employees, setEmployees] = useState<AssessableEmployee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [mandatoryFilter, setMandatoryFilter] = useState<boolean | undefined>(undefined);
  const [skillIdFilter, setSkillIdFilter] = useState<number | undefined>(undefined);
  
  // Modal state
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState<CourseDetails | null>(null);
  
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const user = authApi.getUser();

  useEffect(() => {
    loadData();
    
    // Check for skill_id in URL params (from skill gap view)
    const skillIdParam = searchParams.get('skill_id');
    if (skillIdParam) {
      setSkillIdFilter(parseInt(skillIdParam, 10));
    }
  }, [searchParams]);

  useEffect(() => {
    loadCourses();
  }, [mandatoryFilter, skillIdFilter]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [coursesRes, employeesRes] = await Promise.all([
        coursesApi.getCourses({
          mandatory: mandatoryFilter,
          skill_id: skillIdFilter,
          search: searchTerm || undefined
        }),
        templateAssessmentApi.getAssessableEmployees()
      ]);
      setCourses(coursesRes);
      setEmployees(employeesRes);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadCourses = async () => {
    try {
      const coursesRes = await coursesApi.getCourses({
        mandatory: mandatoryFilter,
        skill_id: skillIdFilter,
        search: searchTerm || undefined
      });
      setCourses(coursesRes);
    } catch (err: any) {
      console.error('Failed to load courses:', err);
    }
  };

  const handleSearch = () => {
    loadCourses();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleAssignClick = (course: CourseDetails) => {
    setSelectedCourse(course);
    setShowAssignModal(true);
  };

  const handleAssignSuccess = (message: string) => {
    setSuccessMessage(message);
    setShowAssignModal(false);
    setSelectedCourse(null);
    setTimeout(() => setSuccessMessage(null), 5000);
  };

  const handleAssignError = (message: string) => {
    setError(message);
    setTimeout(() => setError(null), 5000);
  };

  const handleLogout = () => {
    authApi.logout();
    navigate('/login');
  };

  const clearFilters = () => {
    setSearchTerm('');
    setMandatoryFilter(undefined);
    setSkillIdFilter(undefined);
  };

  const filteredCourses = courses.filter(course => {
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      return (
        course.title.toLowerCase().includes(search) ||
        (course.description?.toLowerCase().includes(search)) ||
        (course.skill_name?.toLowerCase().includes(search))
      );
    }
    return true;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center gap-3">
          <svg className="animate-spin h-6 w-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span className="text-gray-700">Loading courses...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <PageHeader
        title="Course Assignment"
        subtitle="Assign learning courses to your team members"
        onLogout={handleLogout}
      />

      <div className="max-w-7xl mx-auto px-4 py-6">
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

        {/* Filters Section */}
        <div className="bg-white rounded-lg shadow mb-6 p-4">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Search courses by title, description, or skill..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Mandatory Filter */}
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-400" />
              <select
                value={mandatoryFilter === undefined ? '' : mandatoryFilter.toString()}
                onChange={(e) => setMandatoryFilter(e.target.value === '' ? undefined : e.target.value === 'true')}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Courses</option>
                <option value="true">Mandatory Only</option>
                <option value="false">Optional Only</option>
              </select>
            </div>

            {/* Search Button */}
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Search
            </button>

            {/* Clear Filters */}
            {(searchTerm || mandatoryFilter !== undefined || skillIdFilter) && (
              <button
                onClick={clearFilters}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
              >
                Clear Filters
              </button>
            )}
          </div>

          {/* Active Filters Display */}
          {skillIdFilter && (
            <div className="mt-3 flex items-center gap-2">
              <span className="text-sm text-gray-600">Filtering by skill:</span>
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm flex items-center gap-1">
                Skill ID: {skillIdFilter}
                <button onClick={() => setSkillIdFilter(undefined)} className="ml-1">
                  <X className="w-3 h-3" />
                </button>
              </span>
            </div>
          )}
        </div>

        {/* Courses Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredCourses.length === 0 ? (
            <div className="col-span-full bg-white rounded-lg shadow p-8 text-center text-gray-500">
              <BookOpen className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="text-lg font-medium">No courses found</p>
              <p className="text-sm mt-1">Try adjusting your filters or search term</p>
            </div>
          ) : (
            filteredCourses.map(course => (
              <CourseCard
                key={course.id}
                course={course}
                onAssign={() => handleAssignClick(course)}
              />
            ))
          )}
        </div>
      </div>

      {/* Assign Course Modal */}
      {showAssignModal && selectedCourse && (
        <AssignCourseModal
          course={selectedCourse}
          employees={employees}
          onClose={() => {
            setShowAssignModal(false);
            setSelectedCourse(null);
          }}
          onSuccess={handleAssignSuccess}
          onError={handleAssignError}
        />
      )}
    </div>
  );
};

// Course Card Component
interface CourseCardProps {
  course: CourseDetails;
  onAssign: () => void;
}

const CourseCard: React.FC<CourseCardProps> = ({ course, onAssign }) => {
  return (
    <div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 line-clamp-2">{course.title}</h3>
            {course.skill_name && (
              <span className="inline-block mt-1 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
                {course.skill_name}
              </span>
            )}
          </div>
          {course.is_mandatory && (
            <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-medium rounded-full">
              Mandatory
            </span>
          )}
        </div>

        {/* Description */}
        {course.description && (
          <p className="text-sm text-gray-600 mb-3 line-clamp-3">{course.description}</p>
        )}

        {/* External URL */}
        {course.external_url && (
          <a
            href={course.external_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 mb-3"
          >
            <ExternalLink className="w-4 h-4" />
            View Course
          </a>
        )}

        {/* Actions */}
        <div className="pt-3 border-t">
          <button
            onClick={onAssign}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
          >
            <Users className="w-4 h-4" />
            Assign to Employee
          </button>
        </div>
      </div>
    </div>
  );
};

export default CourseAssignment;
