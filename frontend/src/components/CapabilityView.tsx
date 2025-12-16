/**
 * Capability View Component
 * 
 * Displays aggregate skill distributions, coverage metrics,
 * and training needs for CPs and HR users.
 */
import React, { useEffect, useState } from 'react';
import { metricsApi, SkillDistribution, CoverageMetrics, TrainingNeedInfo } from '../services/api';

interface CapabilityViewProps {
  capability?: string;
}

const CoverageCard: React.FC<{ coverage: CoverageMetrics }> = ({ coverage }) => {
  const getColor = () => {
    if (coverage.coverage_percentage >= 80) return '#22C55E';
    if (coverage.coverage_percentage >= 60) return '#EAB308';
    if (coverage.coverage_percentage >= 40) return '#F97316';
    return '#EF4444';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Coverage: {coverage.capability}</h3>
      <div className="flex items-center gap-4">
        <div className="relative w-24 h-24">
          <svg className="w-24 h-24 transform -rotate-90">
            <circle
              cx="48" cy="48" r="40"
              stroke="#E5E7EB" strokeWidth="8" fill="none"
            />
            <circle
              cx="48" cy="48" r="40"
              stroke={getColor()} strokeWidth="8" fill="none"
              strokeDasharray={`${coverage.coverage_percentage * 2.51} 251`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xl font-bold">{coverage.coverage_percentage}%</span>
          </div>
        </div>
        <div className="flex-1">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-green-600 font-bold">{coverage.skills_with_coverage}</span>
              <span className="text-gray-500 ml-1">covered</span>
            </div>
            <div>
              <span className="text-red-600 font-bold">{coverage.skills_without_coverage}</span>
              <span className="text-gray-500 ml-1">gaps</span>
            </div>
          </div>
          {coverage.critical_gaps.length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-red-600 font-medium">Critical Gaps:</p>
              <p className="text-xs text-gray-600">{coverage.critical_gaps.slice(0, 3).join(', ')}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const TrainingNeedsTable: React.FC<{ needs: TrainingNeedInfo[] }> = ({ needs }) => {
  const priorityColors = {
    High: 'bg-red-100 text-red-700',
    Medium: 'bg-yellow-100 text-yellow-700',
    Low: 'bg-blue-100 text-blue-700',
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="p-4 border-b">
        <h3 className="text-lg font-semibold">Training Needs</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Skill</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Current</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Required</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Gap</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {needs.map((need, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium">{need.skill_name}</td>
                <td className="px-4 py-3 text-sm">{need.current_coverage.toFixed(1)}%</td>
                <td className="px-4 py-3 text-sm">{need.required_coverage}%</td>
                <td className="px-4 py-3 text-sm text-red-600">{need.gap_percentage.toFixed(1)}%</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${priorityColors[need.priority as keyof typeof priorityColors]}`}>
                    {need.priority}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const DistributionChart: React.FC<{ distribution: SkillDistribution }> = ({ distribution }) => {
  const proficiencyLevels = ['Beginner', 'Developing', 'Intermediate', 'Advanced', 'Expert'];
  const colors = ['#EF4444', '#F97316', '#EAB308', '#22C55E', '#3B82F6'];

  // Calculate totals by proficiency
  const totals = proficiencyLevels.map((level) => {
    let count = 0;
    Object.values(distribution.proficiency_distribution).forEach((skillDist) => {
      count += skillDist[level] || 0;
    });
    return count;
  });

  const maxCount = Math.max(...totals, 1);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Proficiency Distribution</h3>
      <div className="space-y-3">
        {proficiencyLevels.map((level, idx) => (
          <div key={level} className="flex items-center gap-3">
            <span className="w-24 text-sm text-gray-600">{level}</span>
            <div className="flex-1 bg-gray-200 rounded-full h-6">
              <div
                className="h-6 rounded-full flex items-center justify-end pr-2"
                style={{
                  width: `${(totals[idx] / maxCount) * 100}%`,
                  backgroundColor: colors[idx],
                  minWidth: totals[idx] > 0 ? '30px' : '0'
                }}
              >
                <span className="text-xs text-white font-medium">{totals[idx]}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 text-sm text-gray-500">
        Total Employees: {distribution.total_employees}
      </div>
    </div>
  );
};

export const CapabilityView: React.FC<CapabilityViewProps> = ({ capability }) => {
  const [distribution, setDistribution] = useState<SkillDistribution | null>(null);
  const [coverage, setCoverage] = useState<CoverageMetrics | null>(null);
  const [trainingNeeds, setTrainingNeeds] = useState<TrainingNeedInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCapability, setSelectedCapability] = useState(capability || '');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const dist = await metricsApi.getCapabilityDistribution(selectedCapability || undefined);
        setDistribution(dist);

        if (selectedCapability) {
          const cov = await metricsApi.getCapabilityCoverage(selectedCapability);
          setCoverage(cov);
          const needs = await metricsApi.getTrainingNeeds(selectedCapability);
          setTrainingNeeds(needs);
        }
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load metrics');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedCapability]);

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

  return (
    <div className="space-y-6">
      {/* Filter */}
      <div className="bg-white rounded-lg shadow p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Filter by Capability
        </label>
        <input
          type="text"
          value={selectedCapability}
          onChange={(e) => setSelectedCapability(e.target.value)}
          placeholder="Enter capability name..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Distribution */}
      {distribution && <DistributionChart distribution={distribution} />}

      {/* Coverage */}
      {coverage && <CoverageCard coverage={coverage} />}

      {/* Training Needs */}
      {trainingNeeds.length > 0 && <TrainingNeedsTable needs={trainingNeeds} />}
    </div>
  );
};

export default CapabilityView;
