/** Assign Course Modal Component
 * 
 * Modal for assigning a course to an employee.
 * Allows managers to:
 * - Select an employee from assessable employees
 * - Set optional due date
 * - Add optional notes
 * 
 * Requirements: 3.1, 3.3, 3.5
 */
import React, { useState } from 'react';
import { coursesApi, CourseDetails, AssessableEmployee } from '../services/api';
import { X, Calendar, FileText, Users, AlertCircle, BookOpen } from 'lucide-react';

interface AssignCourseModalProps {
  course: CourseDetails;
  employees: AssessableEmployee[];
  skillId?: number; // Pre-filled skill_id for gap linkage
  onClose: () => void;
  onSuccess: (message: string) => void;
  onError: (message: string) => void;
}

export const AssignCourseModal: React.FC<AssignCourseModalProps> = ({
  course,
  employees,
  skillId,
  onClose,
  onSuccess,
  onError
}) => {
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null);
  const [dueDate, setDueDate] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredEmployees = employees.filter(emp => {
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    return (
      emp.name.toLowerCase().includes(search) ||
      emp.employee_id.toLowerCase().includes(search) ||
      (emp.department?.toLowerCase().includes(search))
    );
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedEmployeeId) {
      onError('Please select an employee');
      return;
    }

    setSubmitting(true);
    
    try {
      await coursesApi.assignCourse({
        course_id: course.id,
        employee_id: selectedEmployeeId,
        due_date: dueDate || undefined,
        notes: notes || undefined,
        skill_id: skillId || course.skill_id
      });
      
      const selectedEmployee = employees.find(e => e.id === selectedEmployeeId);
      onSuccess(`Successfully assigned "${course.title}" to ${selectedEmployee?.name || 'employee'}`);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to assign course';
      onError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  // Get minimum date (today)
  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-blue-600 to-blue-700 rounded-t-lg">
            <div className="flex items-center gap-3">
              <BookOpen className="w-6 h-6 text-white" />
              <div>
                <h2 className="text-lg font-semibold text-white">Assign Course</h2>
                <p className="text-sm text-blue-100">{course.title}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-blue-200 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-4 space-y-4">
            {/* Course Info */}
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="flex items-start gap-2">
                <BookOpen className="w-5 h-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="font-medium text-gray-900">{course.title}</p>
                  {course.description && (
                    <p className="text-sm text-gray-600 mt-1 line-clamp-2">{course.description}</p>
                  )}
                  <div className="flex items-center gap-2 mt-2">
                    {course.is_mandatory && (
                      <span className="px-2 py-0.5 bg-red-100 text-red-800 text-xs rounded-full">
                        Mandatory
                      </span>
                    )}
                    {course.skill_name && (
                      <span className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
                        {course.skill_name}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Employee Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Users className="w-4 h-4 inline mr-1" />
                Select Employee *
              </label>
              
              {/* Search */}
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search employees..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              
              {/* Employee List */}
              <div className="max-h-48 overflow-y-auto border border-gray-300 rounded-lg">
                {filteredEmployees.length === 0 ? (
                  <div className="p-4 text-center text-gray-500">
                    <AlertCircle className="w-5 h-5 mx-auto mb-2" />
                    <p className="text-sm">No employees found</p>
                  </div>
                ) : (
                  filteredEmployees.map(employee => (
                    <div
                      key={employee.id}
                      onClick={() => setSelectedEmployeeId(employee.id)}
                      className={`p-3 cursor-pointer border-b last:border-b-0 transition-colors ${
                        selectedEmployeeId === employee.id
                          ? 'bg-blue-50 border-l-4 border-l-blue-600'
                          : 'hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-gray-900">{employee.name}</p>
                          <p className="text-sm text-gray-500">
                            {employee.employee_id}
                            {employee.department && ` • ${employee.department}`}
                            {employee.band && ` • ${employee.band}`}
                          </p>
                        </div>
                        {selectedEmployeeId === employee.id && (
                          <div className="w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center">
                            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Due Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 inline mr-1" />
                Due Date (Optional)
              </label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                min={today}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <FileText className="w-4 h-4 inline mr-1" />
                Notes (Optional)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add notes explaining why this course was assigned..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              />
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!selectedEmployeeId || submitting}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {submitting && (
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                )}
                Assign Course
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AssignCourseModal;
