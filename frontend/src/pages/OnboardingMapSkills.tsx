/** Onboarding page for first-time users to review and map imported skills. */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { EmployeeSkill, userSkillsApi, authApi } from '../services/api';

export const OnboardingMapSkills: React.FC = () => {
  const [skills, setSkills] = useState<EmployeeSkill[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadSkills();
  }, []);

  const loadSkills = async () => {
    try {
      setLoading(true);
      const employeeSkills = await userSkillsApi.getMySkills();
      setSkills(employeeSkills);
    } catch (error) {
      console.error('Failed to load skills:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    setSaving(true);
    try {
      // Skills are already in the database, just mark onboarding as complete
      // In a real app, you might update a user flag here
      navigate('/dashboard');
    } catch (error) {
      console.error('Failed to confirm skills:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleSkip = () => {
    navigate('/dashboard');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F6F2F4] flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-gray-600">Loading your skills...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F6F2F4] flex items-center justify-center py-12 px-4">
      <div className="max-w-4xl w-full bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Welcome to Skillboard!</h1>
        <p className="text-gray-600 mb-6">
          We've imported some skills for you. Please review and confirm them below.
        </p>

        {skills.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">No skills imported yet.</p>
            <button
              onClick={handleSkip}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Continue to Dashboard
            </button>
          </div>
        ) : (
          <>
            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-4">Your Imported Skills ({skills.length})</h2>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {skills.map((skill) => (
                  <div
                    key={skill.id}
                    className="border border-gray-200 rounded-lg p-4 flex justify-between items-center"
                  >
                    <div>
                      <h3 className="font-semibold text-gray-800">{skill.skill?.name || 'Unknown Skill'}</h3>
                      <p className="text-sm text-gray-600">
                        Rating: {skill.rating}
                        {skill.years_experience && ` • ${skill.years_experience} years experience`}
                      </p>
                      {skill.notes && (
                        <p className="text-xs text-gray-500 mt-1">{skill.notes}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        skill.is_interested 
                          ? 'bg-yellow-100 text-yellow-800' 
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {skill.is_interested ? 'Interested' : 'Existing'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-4 justify-end">
              <button
                onClick={handleSkip}
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                Skip for Now
              </button>
              <button
                onClick={handleConfirm}
                disabled={saving}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? 'Confirming...' : 'Confirm and Continue'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

