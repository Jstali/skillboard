/** Template Assessment Screen for Managers
 * 
 * Allows Line Managers and Delivery Managers to:
 * - View available skill templates
 * - Select an employee to assess
 * - Assess employee skills using a template
 * - Track assessment progress
 * 
 * Requirements: 1.1, 1.2, 1.3, 1.5
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, api, templateAssessmentApi, TemplateListItem, AssessableEmployee, TemplateAssessmentView, SkillAssessmentInput } from '../services/api';
import { PageHeader } from '../components/PageHeader';
import { FileText, Users, Target, ChevronRight, CheckCircle, AlertCircle, X } from 'lucide-react';

// Skill level buttons with colors
const SKILL_LEVEL_BUTTONS = [
  { key: 'B', label: 'Beginner', value: 'Beginner', color: 'bg-green-100 text-green-700 border-green-300 hover:bg-green-200', activeColor: 'bg-green-500 text-white border-green-500' },
  { key: 'D', label: 'Developing', value: 'Developing', color: 'bg-yellow-100 text-yellow-700 border-yellow-300 hover:bg-yellow-200', activeColor: 'bg-yellow-500 text-white border-yellow-500' },
  { key: 'I', label: 'Intermediate', value: 'Intermediate', color: 'bg-blue-100 text-blue-700 border-blue-300 hover:bg-blue-200', activeColor: 'bg-blue-500 text-white border-blue-500' },
  { key: 'A', label: 'Advanced', value: 'Advanced', color: 'bg-orange-100 text-orange-700 border-orange-300 hover:bg-orange-200', activeColor: 'bg-orange-500 text-white border-orange-500' },
  { key: 'E', label: 'Expert', value: 'Expert', color: 'bg-purple-100 text-purple-700 border-purple-300 hover:bg-purple-200', activeColor: 'bg-purple-500 text-white border-purple-500' },
];

export const TemplateAssessment: React.FC = () => {
  const [templates, setTemplates] = useState<TemplateListItem[]>([]);
  const [employees, setEmployees] = useState<AssessableEmployee[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateListItem | null>(null);
  const [selectedEmployee, setSelectedEmployee] = useState<AssessableEmployee | null>(null);
  const [assessmentView, setAssessmentView] = useState<TemplateAssessmentView | null>(null);
  const [assessments, setAssessments] = useState<Record<number, SkillAssessmentInput>>({});
  const [loading, setLoading] = useState(true);
  const [loadingAssessment, setLoadingAssessment] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [step, setStep] = useState<'select-template' | 'select-employee' | 'assess'>('select-template');
  
  const navigate = useNavigate();
  const user = authApi.getUser();

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [templatesRes, employeesRes] = await Promise.all([
        templateAssessmentApi.getTemplates(),
        templateAssessmentApi.getAssessableEmployees()
      ]);
      setTemplates(templatesRes);
      setEmployees(employeesRes);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTemplate = (template: TemplateListItem) => {
    setSelectedTemplate(template);
    setStep('select-employee');
    setError(null);
  };

  const handleSelectEmployee = async (employee: AssessableEmployee) => {
    if (!selectedTemplate) return;
    
    setSelectedEmployee(employee);
    setLoadingAssessment(true);
    setError(null);
    
    try {
      const view = await templateAssessmentApi.getTemplateForAssessment(
        selectedTemplate.id,
        employee.id
      );
      setAssessmentView(view);
      
      // Initialize assessments with current levels
      const initialAssessments: Record<number, SkillAssessmentInput> = {};
      view.skills.forEach(skill => {
        if (skill.skill_id > 0) {
          initialAssessments[skill.skill_id] = {
            skill_id: skill.skill_id,
            level: skill.current_level || '',
            comments: ''
          };
        }
      });
      setAssessments(initialAssessments);
      setStep('assess');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load template for assessment');
    } finally {
      setLoadingAssessment(false);
    }
  };

  const handleLevelChange = (skillId: number, level: string) => {
    setAssessments(prev => ({
      ...prev,
      [skillId]: {
        ...prev[skillId],
        skill_id: skillId,
        level: prev[skillId]?.level === level ? '' : level
      }
    }));
  };

  const handleCommentsChange = (skillId: number, comments: string) => {
    setAssessments(prev => ({
      ...prev,
      [skillId]: {
        ...prev[skillId],
        skill_id: skillId,
        comments
      }
    }));
  };

  const getAssessedCount = () => {
    return (Object.values(assessments) as SkillAssessmentInput[]).filter(a => a.level).length;
  };

  const getCompletionPercentage = () => {
    if (!assessmentView) return 0;
    const validSkills = assessmentView.skills.filter(s => s.skill_id > 0).length;
    if (validSkills === 0) return 0;
    return Math.round((getAssessedCount() / validSkills) * 100);
  };

  const handleSubmit = async () => {
    if (!selectedTemplate || !selectedEmployee || !assessmentView) return;
    
    const assessmentsToSubmit: SkillAssessmentInput[] = (Object.values(assessments) as SkillAssessmentInput[]).filter(a => a.level);
    if (assessmentsToSubmit.length === 0) {
      setError('Please assess at least one skill');
      return;
    }

    setSubmitting(true);
    setError(null);
    
    try {
      const result = await templateAssessmentApi.submitTemplateAssessment(
        selectedTemplate.id,
        selectedEmployee.id,
        assessmentsToSubmit
      );
      
      setSuccessMessage(`Successfully assessed ${result.skills_assessed} skills for ${assessmentView.employee_name}`);
      
      // Reset to template selection after success
      setTimeout(() => {
        setStep('select-template');
        setSelectedTemplate(null);
        setSelectedEmployee(null);
        setAssessmentView(null);
        setAssessments({});
        setSuccessMessage(null);
      }, 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit assessment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleBack = () => {
    if (step === 'assess') {
      setStep('select-employee');
      setAssessmentView(null);
      setAssessments({});
    } else if (step === 'select-employee') {
      setStep('select-template');
      setSelectedTemplate(null);
    }
    setError(null);
  };

  const handleLogout = () => {
    authApi.logout();
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center gap-3">
          <svg className="animate-spin h-6 w-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span className="text-gray-700">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <PageHeader
        title="Template Assessment"
        subtitle={`Assess employee skills using templates`}
        onLogout={handleLogout}
      />

      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Success Message */}
        {successMessage && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <span className="text-green-800">{successMessage}</span>
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

        {/* Progress Steps */}
        <div className="mb-6 flex items-center gap-4">
          <StepIndicator 
            number={1} 
            label="Select Template" 
            active={step === 'select-template'} 
            completed={step !== 'select-template'} 
          />
          <ChevronRight className="w-5 h-5 text-gray-400" />
          <StepIndicator 
            number={2} 
            label="Select Employee" 
            active={step === 'select-employee'} 
            completed={step === 'assess'} 
          />
          <ChevronRight className="w-5 h-5 text-gray-400" />
          <StepIndicator 
            number={3} 
            label="Assess Skills" 
            active={step === 'assess'} 
            completed={false} 
          />
        </div>

        {/* Back Button */}
        {step !== 'select-template' && (
          <button
            onClick={handleBack}
            className="mb-4 text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            ← Back
          </button>
        )}

        {/* Step 1: Select Template */}
        {step === 'select-template' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                Available Templates
              </h2>
              <p className="text-sm text-gray-600 mt-1">Select a skill template to use for assessment</p>
            </div>
            
            {templates.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No templates available. Please contact an administrator.
              </div>
            ) : (
              <div className="divide-y">
                {templates.map(template => (
                  <div
                    key={template.id}
                    onClick={() => handleSelectTemplate(template)}
                    className="p-4 hover:bg-gray-50 cursor-pointer flex items-center justify-between"
                  >
                    <div>
                      <h3 className="font-medium text-gray-900">{template.template_name}</h3>
                      <p className="text-sm text-gray-500">
                        {template.skill_count} skills • Created {new Date(template.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 2: Select Employee */}
        {step === 'select-employee' && selectedTemplate && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Users className="w-5 h-5 text-blue-600" />
                Select Employee
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Using template: <span className="font-medium">{selectedTemplate.template_name}</span>
              </p>
            </div>
            
            {employees.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No employees available for assessment. You may not have any direct reports.
              </div>
            ) : (
              <div className="divide-y">
                {employees.map(employee => (
                  <div
                    key={employee.id}
                    onClick={() => handleSelectEmployee(employee)}
                    className="p-4 hover:bg-gray-50 cursor-pointer flex items-center justify-between"
                  >
                    <div>
                      <h3 className="font-medium text-gray-900">{employee.name}</h3>
                      <p className="text-sm text-gray-500">
                        {employee.employee_id} • {employee.band || 'No band'} • {employee.department || 'No department'}
                      </p>
                    </div>
                    {loadingAssessment && selectedEmployee?.id === employee.id ? (
                      <svg className="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 3: Assess Skills */}
        {step === 'assess' && assessmentView && (
          <TemplateSkillsForm
            assessmentView={assessmentView}
            assessments={assessments}
            onLevelChange={handleLevelChange}
            onCommentsChange={handleCommentsChange}
            onSubmit={handleSubmit}
            submitting={submitting}
            completionPercentage={getCompletionPercentage()}
            assessedCount={getAssessedCount()}
          />
        )}
      </div>
    </div>
  );
};

// Step Indicator Component
const StepIndicator: React.FC<{ number: number; label: string; active: boolean; completed: boolean }> = ({
  number, label, active, completed
}) => (
  <div className={`flex items-center gap-2 ${active ? 'text-blue-600' : completed ? 'text-green-600' : 'text-gray-400'}`}>
    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
      active ? 'bg-blue-600 text-white' : completed ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-600'
    }`}>
      {completed ? <CheckCircle className="w-5 h-5" /> : number}
    </div>
    <span className="font-medium">{label}</span>
  </div>
);

// Template Skills Form Component (Task 8.2)
interface TemplateSkillsFormProps {
  assessmentView: TemplateAssessmentView;
  assessments: Record<number, SkillAssessmentInput>;
  onLevelChange: (skillId: number, level: string) => void;
  onCommentsChange: (skillId: number, comments: string) => void;
  onSubmit: () => void;
  submitting: boolean;
  completionPercentage: number;
  assessedCount: number;
}

const TemplateSkillsForm: React.FC<TemplateSkillsFormProps> = ({
  assessmentView,
  assessments,
  onLevelChange,
  onCommentsChange,
  onSubmit,
  submitting,
  completionPercentage,
  assessedCount
}) => {
  const validSkills = assessmentView.skills.filter(s => s.skill_id > 0);
  
  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header with Progress */}
      <div className="p-4 border-b bg-gradient-to-r from-blue-600 to-blue-700">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-semibold text-white">{assessmentView.template_name}</h2>
            <p className="text-blue-100 text-sm mt-1">
              Assessing: {assessmentView.employee_name}
            </p>
          </div>
          {/* Progress Indicator (Task 8.3) */}
          <div className="text-right">
            <div className="text-2xl font-bold text-white">{completionPercentage}%</div>
            <p className="text-blue-100 text-sm">
              {assessedCount} of {validSkills.length} skills
            </p>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="mt-3 h-2 bg-blue-800 rounded-full overflow-hidden">
          <div 
            className="h-full bg-green-400 transition-all duration-300"
            style={{ width: `${completionPercentage}%` }}
          />
        </div>
      </div>

      {/* Legend */}
      <div className="p-4 bg-gray-50 border-b">
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
      <div className="p-4 space-y-3 max-h-[60vh] overflow-y-auto">
        {assessmentView.skills.map((skill, index) => {
          const isValidSkill = skill.skill_id > 0;
          const currentAssessment = assessments[skill.skill_id];
          const selectedLevel = currentAssessment?.level;
          const isAssessed = !!selectedLevel;
          
          return (
            <div 
              key={skill.skill_id || `invalid-${index}`}
              className={`border rounded-lg p-4 transition-colors ${
                !isValidSkill 
                  ? 'bg-gray-50 border-gray-200' 
                  : isAssessed 
                    ? 'border-green-300 bg-green-50' 
                    : 'border-gray-200 hover:border-blue-300'
              }`}
            >
              <div className="flex flex-col md:flex-row md:items-center gap-4">
                {/* Skill Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">
                      {index + 1}. {skill.skill_name}
                    </span>
                    {isAssessed && (
                      <CheckCircle className="w-4 h-4 text-green-600" />
                    )}
                  </div>
                  {skill.skill_category && (
                    <span className="text-xs text-gray-500">({skill.skill_category})</span>
                  )}
                  {skill.required_level && (
                    <p className="text-sm text-blue-600 mt-1">
                      Required: {skill.required_level}
                    </p>
                  )}
                  {skill.current_level && (
                    <p className="text-sm text-gray-500">
                      Current: {skill.current_level}
                    </p>
                  )}
                  {!isValidSkill && (
                    <p className="text-sm text-red-500 mt-1">
                      ⚠️ Skill not found in database
                    </p>
                  )}
                </div>

                {/* Level Buttons */}
                {isValidSkill && (
                  <div className="flex items-center gap-2">
                    {SKILL_LEVEL_BUTTONS.map(btn => {
                      const isSelected = selectedLevel === btn.value;
                      return (
                        <button
                          key={btn.key}
                          onClick={() => onLevelChange(skill.skill_id, btn.value)}
                          className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm border-2 transition-all duration-200 ${
                            isSelected ? btn.activeColor : btn.color
                          }`}
                          title={btn.label}
                        >
                          {btn.key}
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* Comments */}
                {isValidSkill && (
                  <div className="md:w-48">
                    <input
                      type="text"
                      value={currentAssessment?.comments || ''}
                      onChange={(e) => onCommentsChange(skill.skill_id, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      placeholder="Comments (optional)"
                    />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="px-6 py-4 border-t bg-gray-50 flex justify-between items-center">
        <div className="text-sm text-gray-600">
          {assessedCount === 0 ? (
            <span className="text-amber-600">Please assess at least one skill</span>
          ) : (
            <span className="text-green-600">{assessedCount} skill(s) ready to submit</span>
          )}
        </div>
        <button
          onClick={onSubmit}
          disabled={assessedCount === 0 || submitting}
          className="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors flex items-center gap-2"
        >
          {submitting && (
            <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          )}
          Submit Assessment
        </button>
      </div>
    </div>
  );
};

export default TemplateAssessment;
