/**
 * Metrics Dashboard Component
 * 
 * Displays high-level skill counts, distribution visualizations,
 * and trend charts without personal data.
 */
import React, { useEffect, useState } from 'react';
import { metricsApi } from '../services/api';

interface MetricsDashboardProps {
  capability?: string;
  team?: string;
}

const CountCard: React.FC<{ label: string; count: number; color: string }> = ({ label, count, color }) => (
  <div className="bg-white rounded-lg shadow p-4">
    <p className="text-sm text-gray-500">{label}</p>
    <p className="text-3xl font-bold" style={{ color }}>{count}</p>
  </div>
);

export const MetricsDashboard: React.FC<MetricsDashboardProps> = ({ capability, team }) => {
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await metricsApi.getSkillCountsByProficiency(capability, team);
        setCounts(data);
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load metrics');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [capability, team]);

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

  const proficiencyColors = {
    Beginner: '#EF4444',
    Developing: '#F97316',
    Intermediate: '#EAB308',
    Advanced: '#22C55E',
    Expert: '#3B82F6',
  };

  const total = Object.values(counts).reduce((sum, c) => sum + c, 0);

  return (
    <div className="space-y-6">
      {/* Total Count */}
      <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg shadow p-6 text-white">
        <p className="text-lg opacity-90">Total Skills Recorded</p>
        <p className="text-5xl font-bold">{total}</p>
      </div>

      {/* Proficiency Counts */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {Object.entries(proficiencyColors).map(([level, color]) => (
          <CountCard
            key={level}
            label={level}
            count={counts[level] || 0}
            color={color}
          />
        ))}
      </div>

      {/* Distribution Bar */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Proficiency Distribution</h3>
        <div className="flex h-8 rounded-lg overflow-hidden">
          {Object.entries(proficiencyColors).map(([level, color]) => {
            const percentage = total > 0 ? ((counts[level] || 0) / total) * 100 : 0;
            return percentage > 0 ? (
              <div
                key={level}
                style={{ width: `${percentage}%`, backgroundColor: color }}
                className="flex items-center justify-center"
                title={`${level}: ${counts[level] || 0} (${percentage.toFixed(1)}%)`}
              >
                {percentage > 10 && (
                  <span className="text-xs text-white font-medium">
                    {percentage.toFixed(0)}%
                  </span>
                )}
              </div>
            ) : null;
          })}
        </div>
        <div className="flex flex-wrap gap-4 mt-4">
          {Object.entries(proficiencyColors).map(([level, color]) => (
            <div key={level} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: color }} />
              <span className="text-sm text-gray-600">{level}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MetricsDashboard;
