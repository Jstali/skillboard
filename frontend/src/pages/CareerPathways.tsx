/** Career Pathways Management - Configure skill requirements per band dynamically. */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, roleRequirementsApi, userSkillsApi, skillsApi, categoriesApi, RoleRequirement, PathwaySkill, Skill } from '../services/api';
import { Button } from '../components/Button';
import { PageHeader } from '../components/PageHeader';
import { SearchableSelect } from '../components/SearchableSelect';
import { Plus, Trash2, Edit2, Play, Users, Search, Save, X } from 'lucide-react';
import NxzenLogo from '../images/Nxzen.jpg';

const BANDS = ['A', 'B', 'C', 'L1', 'L2', 'L3', 'U'];
const RATINGS = ['Beginner', 'Developing', 'Intermediate', 'Advanced', 'Expert'];

const RATING_COLORS: Record<string, string> = {
  Beginner: 'bg-green-100 text-green-800',
  Developing: 'bg-blue-100 text-blue-800',
  Intermediate: 'bg-yellow-100 text-yellow-800',
  Advanced: 'bg-blue-200 text-blue-900',
  Expert: 'bg-red-100 text-red-800',
};

interface PathwayInfo {
  pathway: string;
  total_skills: number;
  skills_in_requirements: number;
  skills_remaining: number;
  skill_categories: string[];
}

interface CareerPathwaysProps {
  isEmbedded?: boolean;
}

export const CareerPathways: React.FC<CareerPathwaysProps> = ({ isEmbedded = false }) => {
  const [pathways, setPathways] = useState<Record<string, PathwaySkill[]>>({});
  const [pathwaysList, setPathwaysList] = useState<PathwayInfo[]>([]);
  const [allSkills, setAllSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedPathway, setSelectedPathway] = useState<string>('');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [editingSkill, setEditingSkill] = useState<number | null>(null);
  const [editedRequirements, setEditedRequirements] = useState<Record<string, string>>({});
  const [showAddSkill, setShowAddSkill] = useState(false);
  const [showCreatePathway, setShowCreatePathway] = useState(false);
  const [newPathwayName, setNewPathwayName] = useState('');
  const [selectedSkillToAdd, setSelectedSkillToAdd] = useState<number | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [addingAllSkills, setAddingAllSkills] = useState(false);
  const navigate = useNavigate();
  const user = authApi.getUser();

  useEffect(() => {
    if (!user?.is_admin) {
      navigate('/login');
      return;
    }
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [skillsData, pathwaysListData] = await Promise.all([
        skillsApi.getAllSimple(1000),
        roleRequirementsApi.getPathwaysList(),
      ]);
      setAllSkills(skillsData);
      setPathwaysList(pathwaysListData);

      // Set first pathway as selected if none selected
      if (pathwaysListData.length > 0 && !selectedPathway) {
        setSelectedPathway(pathwaysListData[0].pathway);
      }
    } catch (error) {
      console.error('Failed to load pathways:', error);
      setMessage({ type: 'error', text: 'Failed to load career pathways' });
    } finally {
      setLoading(false);
    }
  };

  // Load skills for selected pathway
  const loadPathwaySkills = async (pathway: string) => {
    if (!pathway) {
      setPathways({});
      return;
    }
    try {
      const pathwaySkills = await roleRequirementsApi.getPathwaySkills(pathway);
      setPathways(pathwaySkills);
    } catch (error) {
      console.error('Failed to load pathway skills:', error);
      setPathways({});
    }
  };

  // Load pathway skills when selected pathway changes
  useEffect(() => {
    if (selectedPathway) {
      loadPathwaySkills(selectedPathway);
    }
  }, [selectedPathway]);


  // Get skills for the selected pathway - now directly from pathways state
  const getSkillsForPathway = () => {
    return pathways;
  };

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(category)) {
        newSet.delete(category);
      } else {
        newSet.add(category);
      }
      return newSet;
    });
  };

  const handleEditSkill = (skill: PathwaySkill) => {
    setEditingSkill(skill.skill_id);
    setEditedRequirements({ ...skill.band_requirements });
  };

  const handleCancelEdit = () => {
    setEditingSkill(null);
    setEditedRequirements({});
  };

  const handleUpdateSkill = async (skillId: number) => { // Renamed from handleSaveSkill
    setSaving(true);
    try {
      await roleRequirementsApi.bulkUpdateSkill(skillId, editedRequirements);
      setMessage({ type: 'success', text: 'Skill requirements updated successfully' });
      setEditingSkill(null);
      setEditedRequirements({});
      await loadData();
      if (selectedPathway) {
        await loadPathwaySkills(selectedPathway);
      }
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to update requirements' });
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteSkill = async (skillId: number, skillName: string) => {
    if (!confirm(`Remove "${skillName}" from career pathways ? This will delete all band requirements for this skill.`)) {
      return;
    }

    setSaving(true);
    try {
      await roleRequirementsApi.removeSkillFromPathway(skillId);
      setMessage({ type: 'success', text: `Removed ${skillName} from pathways` });
      await loadData();
      if (selectedPathway) {
        await loadPathwaySkills(selectedPathway);
      }
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to remove skill' });
    } finally {
      setSaving(false);
    }
  };

  const handleAddSkill = async () => {
    if (!selectedSkillToAdd) return;

    setSaving(true);
    try {
      // Pass the selectedPathway as the category to force update if needed
      await roleRequirementsApi.addSkillToPathway(selectedSkillToAdd, selectedPathway);
      setMessage({ type: 'success', text: 'Skill added to pathway' });
      setShowAddSkill(false);
      setSelectedSkillToAdd(null);
      await loadData();
      if (selectedPathway) {
        await loadPathwaySkills(selectedPathway);
      }
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to add skill' });
    } finally {
      setSaving(false);
    }
  };

  const handleRatingChange = (band: string, rating: string) => {
    setEditedRequirements(prev => ({
      ...prev,
      [band]: rating,
    }));
  };

  const handleAddAllSkills = async () => { // Renamed from handleAddAllSkillsForPathway
    if (!selectedPathway) return;

    const pathwayInfo = pathwaysList.find(p => p.pathway === selectedPathway);
    if (!pathwayInfo || pathwayInfo.skills_remaining === 0) {
      setMessage({ type: 'error', text: 'No skills remaining to add for this pathway' });
      return;
    }

    if (!confirm(`This will add ${pathwayInfo.skills_remaining} skills from "${selectedPathway}" pathway with default requirements(A = Beginner → L2 += Expert).Continue ? `)) {
      return;
    }

    setAddingAllSkills(true);
    try {
      const result = await roleRequirementsApi.addAllSkillsToPathways(selectedPathway);
      setMessage({
        type: 'success',
        text: `${result.message} (Added: ${result.added}, Skipped: ${result.skipped} already in pathways)`
      });
      // Reload both the pathways list and the current pathway skills
      await loadData();
      await loadPathwaySkills(selectedPathway);
      // Expand all categories to show the new skills
      const pathwaySkills = await roleRequirementsApi.getPathwaySkills(selectedPathway);
      setExpandedCategories(new Set(Object.keys(pathwaySkills)));
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to add skills' });
    } finally {
      setAddingAllSkills(false);
    }
  };

  // Get skills that are not yet in pathways
  const availableSkills = allSkills.filter(skill => {
    const allPathwaySkillIds = Object.values(pathways).flat().map((p: PathwaySkill) => p.skill_id);
    return !allPathwaySkillIds.includes(skill.id);
  });

  const skillsForPathway = getSkillsForPathway();
  const skillCategories = Object.keys(skillsForPathway).sort();
  const currentPathwayInfo = pathwaysList.find(p => p.pathway === selectedPathway);
  const totalSkillsInPathway = Object.values(skillsForPathway).flat().length;

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F6F2F4] flex items-center justify-center">
        <div className="text-xl text-gray-600">Loading career pathways...</div>
      </div>
    );
  }


  return (
    <div className="min-h-screen bg-[#F6F2F4]">
      {/* Header */}
      {!isEmbedded && (
        <PageHeader
          title="Career Pathways"
          rightAction={
            <Button
              variant="success"
              size="sm"
              icon={<Plus className="w-4 h-4" />}
              onClick={() => setShowCreatePathway(true)}
            >
              New Pathway
            </Button>
          }
        />
      )}

      {/* Quick Actions */}
      {!isEmbedded && (
        <div className="max-w-7xl mx-auto px-6 mt-4">
          <h2 className="text-center text-lg font-semibold text-gray-800 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-4">
            <button
              onClick={() => navigate('/admin/dashboard?tab=overview')}
              className="flex items-center gap-3 rounded-2xl shadow-xl hover:shadow-2xl p-4 transition bg-white"
            >
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-blue-600">
                  <rect x="4" y="4" width="6" height="6" rx="1"></rect>
                  <rect x="14" y="4" width="6" height="6" rx="1"></rect>
                  <rect x="4" y="14" width="6" height="6" rx="1"></rect>
                  <rect x="14" y="14" width="6" height="6" rx="1"></rect>
                </svg>
              </span>
              <div>
                <div className="text-sm font-semibold text-gray-900">Overview</div>
                <div className="text-xs text-gray-500">Summary metrics</div>
              </div>
            </button>
            <button
              onClick={() => navigate('/admin/dashboard?tab=skill-gap')}
              className="flex items-center gap-3 rounded-2xl shadow-xl hover:shadow-2xl p-4 transition bg-white"
            >
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-rose-50">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-rose-600">
                  <path d="M3 12c3-5 6-7 9-7s6 2 9 7"></path>
                  <circle cx="12" cy="12" r="3"></circle>
                  <path d="M15 15l4 4"></path>
                </svg>
              </span>
              <div>
                <div className="text-sm font-semibold text-gray-900">Skill Gap Analysis</div>
                <div className="text-xs text-gray-500">Analyze gaps</div>
              </div>
            </button>
            <button
              onClick={() => navigate('/admin/dashboard?tab=employees')}
              className="flex items-center gap-3 rounded-2xl shadow-xl hover:shadow-2xl p-4 transition bg-white"
            >
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-green-50">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-green-600">
                  <circle cx="8" cy="9" r="3"></circle>
                  <circle cx="16" cy="9" r="3"></circle>
                  <path d="M2 20c0-3.5 3.5-6 8-6s8 2.5 8 6"></path>
                </svg>
              </span>
              <div>
                <div className="text-sm font-semibold text-gray-900">Employees</div>
                <div className="text-xs text-gray-500">Manage employees</div>
              </div>
            </button>
            <button
              onClick={() => navigate('/admin/dashboard?tab=skills')}
              className="flex items-center gap-3 rounded-2xl shadow-xl hover:shadow-2xl p-4 transition bg-white"
            >
              <span className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-purple-100">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className="w-8 h-8 text-purple-700">
                  <path fill="currentColor" d="M12 2c4.97 0 9 3.58 9 8.3 0 3.73-2.65 6.93-6.25 7.67V21H9.5v-2.06C6.07 18.4 3 15.15 3 10.96 3 5.66 7.03 2 12 2z" />
                  <g fill="#ffffff">
                    <circle cx="12" cy="11" r="2" />
                    <rect x="11.3" y="6.5" width="1.4" height="2.2" rx="0.3" />
                    <rect x="15.8" y="10.3" width="2.2" height="1.4" rx="0.3" />
                    <rect x="11.3" y="13.3" width="1.4" height="2.2" rx="0.3" />
                    <rect x="6" y="10.3" width="2.2" height="1.4" rx="0.3" />
                    <rect x="14.7" y="8" width="1.6" height="1.6" rx="0.3" />
                    <rect x="8.7" y="8" width="1.6" height="1.6" rx="0.3" />
                    <rect x="14.7" y="12.9" width="1.6" height="1.6" rx="0.3" />
                    <rect x="8.7" y="12.9" width="1.6" height="1.6" rx="0.3" />
                  </g>
                </svg>
              </span>
              <div>
                <div className="text-sm font-semibold text-gray-900">Skills</div>
                <div className="text-xs text-gray-500">Browse skills</div>
              </div>
            </button>
            <button
              onClick={() => navigate('/admin/dashboard?tab=improvements')}
              className="flex items-center gap-3 rounded-2xl shadow-xl hover:shadow-2xl p-4 transition bg-white"
            >
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-indigo-600">
                  <path d="M6 18v-4"></path>
                  <path d="M12 18v-7"></path>
                  <path d="M18 18v-10"></path>
                  <path d="M5 6l5 5 4-3 5 5"></path>
                </svg>
              </span>
              <div>
                <div className="text-sm font-semibold text-gray-900">Improvements</div>
                <div className="text-xs text-gray-500">Track improvements</div>
              </div>
            </button>
            <button
              onClick={() => navigate('/admin/learning')}
              className="flex items-center gap-3 rounded-2xl shadow-xl hover:shadow-2xl p-4 transition bg-white"
            >
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-purple-50">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-purple-600">
                  <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
                  <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
                </svg>
              </span>
              <div>
                <div className="text-sm font-semibold text-gray-900">Learning</div>
                <div className="text-xs text-gray-500">Manage courses</div>
              </div>
            </button>
            <button
              className="flex items-center gap-3 rounded-2xl shadow-xl hover:shadow-2xl p-4 transition bg-white ring-2 ring-teal-500"
            >
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-teal-50">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-teal-600">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                  <path d="M2 17l10 5 10-5"></path>
                  <path d="M2 12l10 5 10-5"></path>
                </svg>
              </span>
              <div>
                <div className="text-sm font-semibold text-gray-900">Career Pathways</div>
                <div className="text-xs text-gray-500">Skill requirements</div>
              </div>
            </button>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Description */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-2">Career Pathways & Skill Requirements</h2>
          <p className="text-gray-600">
            Define career pathways and the skills required at each career level (A, B, C, L1, L2, L3, U).
            These requirements are used for skill gap analysis and learning recommendations.
          </p>
        </div>

        {/* Messages */}
        {message && (
          <div className={`mb-4 p-4 rounded-lg ${message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
            {message.text}
            <button onClick={() => setMessage(null)} className="ml-4 text-sm underline">Dismiss</button>
          </div>
        )}

        {/* Pathway Selector */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <label className="font-medium text-gray-700">Select Pathway:</label>
              <div className="min-w-[250px] w-72">
                <SearchableSelect
                  options={[
                    { value: "", label: "Select a pathway..." },
                    ...pathwaysList.map(p => ({ value: p.pathway, label: `${p.pathway} (${p.total_skills} skills)` }))
                  ]}
                  value={selectedPathway}
                  onChange={(v) => {
                    setSelectedPathway(v as string);
                    setExpandedCategories(new Set());
                  }}
                  placeholder="Select a pathway..."
                />
              </div>
              {currentPathwayInfo && (
                <span className="text-sm text-gray-500">
                  {currentPathwayInfo.skills_in_requirements} of {currentPathwayInfo.total_skills} skills configured
                </span>
              )}
            </div>

          </div>

          <div className="flex items-center gap-2 mt-4">
            <button
              onClick={() => setShowCreatePathway(true)}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 font-medium"
            >
              + Create New Pathway
            </button>

            {selectedPathway && currentPathwayInfo && currentPathwayInfo.skills_remaining > 0 && (
              <div className="flex-shrink-0">
                <Button
                  variant={addingAllSkills ? "secondary" : "primary"}
                  onClick={handleAddAllSkills}
                  disabled={addingAllSkills || !selectedPathway}
                  loading={addingAllSkills}
                  icon={<Plus className="w-4 h-4" />}
                >
                  Populate from Skills
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Pathway Content */}
      {selectedPathway && (
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          {/* Pathway Header */}
          <div className="p-4 border-b bg-gray-50 flex justify-between items-center">
            <div>
              <h3 className="text-xl font-bold text-gray-800">{selectedPathway}</h3>
              <p className="text-sm text-gray-500">{totalSkillsInPathway} skills configured</p>
            </div>
            <button
              onClick={() => setShowAddSkill(true)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
            >
              <span>+</span> Add Skill
            </button>
          </div>

          {/* Create Pathway Button - if no pathway selected or to add new */}
          {/* Actually, the 'Content' only shows if selectedPathway is set. */
            /* We need 'Create Pathway' OUTSIDE or in the header. */
            /* Let's move this logic to the main update block where we inject the button. */
          }

          {/* Skill Categories */}
          {skillCategories.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {skillCategories.map(category => (
                <div key={category}>
                  {/* Category Header */}
                  <button
                    onClick={() => toggleCategory(category)}
                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition"
                  >
                    <span className="font-medium text-gray-800">{category}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-gray-500">
                        {skillsForPathway[category]?.length || 0} skills
                      </span>
                      <svg
                        className={`w-5 h-5 text-gray-400 transition-transform ${expandedCategories.has(category) ? 'rotate-180' : ''}`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </button>

                  {/* Skills Table */}
                  {expandedCategories.has(category) && skillsForPathway[category] && (
                    <div className="overflow-x-auto bg-gray-50">
                      <table className="w-full">
                        <thead className="bg-gray-100">
                          <tr>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700 w-64">Skill</th>
                            {BANDS.map(band => (
                              <th key={band} className="px-3 py-2 text-center text-sm font-medium text-gray-700 w-24">
                                {band}
                              </th>
                            ))}
                            <th className="px-4 py-2 text-center text-sm font-medium text-gray-700 w-24">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 bg-white">
                          {skillsForPathway[category].map(skill => (
                            <tr key={skill.skill_id} className="hover:bg-gray-50">
                              <td className="px-4 py-2 font-medium text-gray-900">{skill.skill_name}</td>
                              {BANDS.map(band => (
                                <td key={band} className="px-3 py-2 text-center">
                                  {editingSkill === skill.skill_id ? (
                                    <select
                                      value={editedRequirements[band] || ''}
                                      onChange={(e) => handleRatingChange(band, e.target.value)}
                                      className="w-full p-1 text-xs border rounded"
                                    >
                                      <option value="">-</option>
                                      {RATINGS.map(r => (
                                        <option key={r} value={r}>{r}</option>
                                      ))}
                                    </select>
                                  ) : (
                                    <span className={`inline-block px-2 py-1 text-xs rounded-full ${skill.band_requirements[band]
                                      ? RATING_COLORS[skill.band_requirements[band]]
                                      : 'bg-gray-100 text-gray-400'
                                      } `}>
                                      {skill.band_requirements[band] || '-'}
                                    </span>
                                  )}
                                </td>
                              ))}
                              <td className="px-4 py-2 text-center">
                                {editingSkill === skill.skill_id ? (
                                  <div className="flex items-center gap-2">
                                    <Button
                                      size="sm"
                                      variant="secondary"
                                      icon={<Save className="w-4 h-4" />}
                                      onClick={() => handleUpdateSkill(skill.skill_id!)}
                                    >
                                      Save
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      icon={<X className="w-4 h-4" />}
                                      onClick={() => {
                                        setEditingSkill(null);
                                        setEditedRequirements({});
                                      }}
                                    >
                                      Cancel
                                    </Button>
                                  </div>
                                ) : (
                                  <div className="flex justify-center gap-1">
                                    <button
                                      onClick={() => handleEditSkill(skill)}
                                      className="p-1 text-blue-600 hover:text-blue-800"
                                      title="Edit"
                                    >
                                      ✎
                                    </button>
                                    <button
                                      onClick={() => handleDeleteSkill(skill.skill_id, skill.skill_name)}
                                      className="p-1 text-red-600 hover:text-red-800"
                                      title="Delete"
                                    >
                                      🗑
                                    </button>
                                  </div>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-gray-500">
              No skills configured for this pathway yet. Click "Populate from Skills" to add all skills from this pathway, or "Add Skill Requirement" to add individual skills.
            </div>
          )}
        </div>
      )}

      {!selectedPathway && pathwaysList.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-8 text-center text-gray-500">
          Select a pathway above to view and manage skill requirements.
        </div>
      )}

      {pathwaysList.length === 0 && (
        <div className="bg-white rounded-lg shadow-sm p-8 text-center text-gray-500">
          No pathways found. Please configure category templates first.
        </div>
      )}

      {/* Add Skill Modal is handled below */}

      {/* Create Pathway Modal */}
      {showCreatePathway && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Create New Pathway</h3>
            <p className="text-sm text-gray-600 mb-4">
              Enter a name for the new career pathway. You can then add skills to it.
            </p>
            <input
              type="text"
              value={newPathwayName}
              onChange={(e) => setNewPathwayName(e.target.value)}
              placeholder="e.g., Cloud Engineering"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4 focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => { setShowCreatePathway(false); setNewPathwayName(''); }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (newPathwayName.trim()) {
                    setSelectedPathway(newPathwayName.trim());
                    setPathwaysList(prev => [...prev, {
                      pathway: newPathwayName.trim(),
                      total_skills: 0,
                      skills_in_requirements: 0,
                      skills_remaining: 0,
                      skill_categories: []
                    }]);
                    setShowCreatePathway(false);
                    setNewPathwayName('');
                  }
                }}
                disabled={!newPathwayName.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Create Pathway
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Skill Modal matching original code but outside verify block */}
      {showAddSkill && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Add Skill to Career Pathways</h3>
            <p className="text-sm text-gray-600 mb-4">
              Select a skill to add. Default requirements will be created (A=Beginner → L2+=Expert).
            </p>
            <div className="mb-4">
              <SearchableSelect
                options={availableSkills.map(skill => ({
                  value: skill.id,
                  label: `${skill.name} ${skill.category ? `(${skill.category})` : ''}`
                }))}
                value={selectedSkillToAdd}
                onChange={(v) => setSelectedSkillToAdd(v as number)}
                placeholder="Select a skill..."
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => { setShowAddSkill(false); setSelectedSkillToAdd(null); }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={handleAddSkill}
                disabled={!selectedSkillToAdd || saving}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {saving ? 'Adding...' : 'Add Skill'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CareerPathways;
