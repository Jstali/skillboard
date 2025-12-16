/**
 * Employee Skill Board Component
 * 
 * Displays an employee's skills with proficiency indicators,
 * capability alignment, and skill gaps.
 */
import React, { useEffect, useState } from 'react';
import { skillBoardApi, EmployeeSkillBoardData, SkillWithProficiency, SkillGapInfo } from '../services/api';

interface EmployeeSkillBoardProps {
  employeeId: string;
}

const ProficiencyBadge: React.FC<{ display: SkillWithProficiency['rating_display'] }> = ({ display }) => (
  <span
    className="px-2 py-1 rounded-full text-xs font-medium text-white"
    style={{ backgroundColor: display.color }}
  >
    {display.level}
  </span>
);

const AlignmentGauge: React.FC<{ score: number }> = ({ score }) => {
  const getColor = () => {
    if (score >= 80) return '#22C55E'; // Green
    if (score >= 60) return '#EAB308'; // Yellow
    if (score >= 40) return '#F97316'; // Orange
    return '#EF4444'; // Red
  };

  return (
    <div className="w-full">
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium">Alignment Score</span>
        <span className="text-sm font-bold" style={{ color: getColor() }}>{score}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className="h-3 rounded-full transition-all duration-500"
          style={{ width: `${score}%`, backgroundColor: getColor() }}
        />
      </div>
    </div>
  );
};

const SkillGapCard: React.FC<{ gap: SkillGapInfo }> = ({ gap }) => {
  const priorityColors = {
    High: 'bg-red-100 border-red-500 text-red-700',
    Medium: 'bg-yellow-100 border-yellow-500 text-yellow-700',
    Low: 'bg-blue-100 border-blue-500 text-blue-700',
  };

  return (
    <div className={`p-3 rounded-lg border-l-4 ${priorityColors[gap.priority as keyof typeof priorityColors] || priorityColors.Low}`}>
      <div className="flex justify-between items-start">
        <div>
          <h4 className="font-medium">{gap.skill_name}</h4>
          {gap.category && <p className="text-xs text-gray-500">{gap.category}</p>}
        </div>
        <span className="text-xs font-bold px-2 py-1 rounded">{gap.priority}</span>
      </div>
      <div className="mt-2 text-sm">
        <span>Current: {gap.actual_level || 'None'}</span>
        <span className="mx-2">→</span>
        <span>Required: {gap.required_level}</span>
      </div>
    </div>
  );
};

export const EmployeeSkillBoard: React.FC<EmployeeSkillBoardProps> = ({ employeeId }) => {
  const [data, setData] = useState<EmployeeSkillBoardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const skillBoard = await skillBoardApi.getEmployeeSkillBoard(employeeId);
        setData(skillBoard);
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load skill board');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [employeeId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        {error}
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-800">{data.name}</h2>
        <div className="mt-2 flex gap-4 text-sm text-gray-600">
          {data.home_capability && (
            <span className="flex items-center gap-1">
              <span className="font-medium">Capability:</span> {data.home_capability}
            </span>
          )}
          {data.team && (
            <span className="flex items-center gap-1">
              <span className="font-medium">Team:</span> {data.team}
            </span>
          )}
        </div>
      </div>

      {/* Capability Alignment */}
      {data.capability_alignment && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Capability Alignment</h3>
          <AlignmentGauge score={data.capability_alignment.alignment_score} />
          <div className="mt-4 grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-green-600">
                {data.capability_alignment.required_skills_met}
              </p>
              <p className="text-xs text-gray-500">Skills Met</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-600">
                {data.capability_alignment.required_skills_total}
              </p>
              <p className="text-xs text-gray-500">Total Required</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-600">
                {data.capability_alignment.average_proficiency.toFixed(1)}
              </p>
              <p className="text-xs text-gray-500">Avg Proficiency</p>
            </div>
          </div>
        </div>
      )}

      {/* Skills List */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Skills ({data.skills.length})</h3>
        <div className="grid gap-3">
          {data.skills.map((skill) => (
            <div
              key={skill.skill_id}
              className={`p-4 rounded-lg border ${
                skill.meets_requirement ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
              }`}
            >
              <div className="flex justify-between items-center">
                <div>
                  <h4 className="font-medium">{skill.skill_name}</h4>
                  {skill.category && (
                    <p className="text-xs text-gray-500">{skill.category}</p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {skill.is_required && (
                    <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                      Required
                    </span>
                  )}
                  <ProficiencyBadge display={skill.rating_display} />
                </div>
              </div>
              {skill.years_experience && (
                <p className="text-xs text-gray-500 mt-1">
                  {skill.years_experience} years experience
                </p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Skill Gaps */}
      {data.skill_gaps.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-red-600">
            Skill Gaps ({data.skill_gaps.length})
          </h3>
          <div className="grid gap-3">
            {data.skill_gaps.map((gap) => (
              <SkillGapCard key={gap.skill_id} gap={gap} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default EmployeeSkillBoard;
