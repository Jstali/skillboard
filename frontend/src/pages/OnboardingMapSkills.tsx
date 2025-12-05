import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DndContext, DragEndEvent, DragStartEvent, DragOverlay, PointerSensor, useSensor, useSensors, useDroppable } from '@dnd-kit/core';
import { userSkillsApi, authApi, skillsApi, Skill } from '../services/api';
import { SkillBrowser } from '../components/SkillBrowser';
import { SkillCardData } from '../components/SkillCard';

export const OnboardingMapSkills: React.FC = () => {
  const [mySkills, setMySkills] = useState<SkillCardData[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [customSkillName, setCustomSkillName] = useState('');
  const [showCustomSkillInput, setShowCustomSkillInput] = useState(false);
  const navigate = useNavigate();
  const user = authApi.getUser();

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }));

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    loadSkills();
    loadAllSkills();
  }, []);

  const loadSkills = async () => {
    try {
      setLoading(true);
      const employeeSkills = await userSkillsApi.getMySkills();
      
      const skills: SkillCardData[] = [];
      
      employeeSkills.forEach((empSkill) => {
        const skillData: SkillCardData = {
          id: empSkill.skill_id,
          name: empSkill.skill?.name || 'Unknown',
          description: empSkill.skill?.description,
          rating: empSkill.rating || undefined,
          years_experience: empSkill.years_experience || undefined,
          employee_skill_id: empSkill.id,
          is_custom: empSkill.is_custom || false,
        };
        
        // Only include non-interested skills
        if (!empSkill.is_interested) {
          skills.push(skillData);
        }
      });
      
      setMySkills(skills);
    } catch (error) {
      console.error('Failed to load skills:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAllSkills = async () => {
    try {
      const data = await skillsApi.getAll();
      setSkills(data);
    } catch (error) {
      console.error('Failed to load all skills:', error);
    }
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over) return;

    const activeData = active.data.current;
    const overId = over.id as string;

    // Handle dropping from master list
    if (activeData?.type === 'skill') {
      const skill: Skill = activeData.skill;
      const newSkillData: SkillCardData = {
        id: skill.id,
        name: skill.name,
        description: skill.description,
        is_custom: false,
      };

      if (overId === 'skills-column' || overId.startsWith('skills-')) {
        // Add to my skills
        if (!mySkills.find(s => s.id === skill.id)) {
          try {
            const created = await userSkillsApi.createMySkill({
              skill_name: skill.name,
              rating: 'Beginner',
              is_interested: false,
              is_custom: false,
            });
            newSkillData.employee_skill_id = created.id;
            newSkillData.rating = 'Beginner';
            setMySkills([...mySkills, newSkillData]);
          } catch (error) {
            console.error('Failed to add skill:', error);
          }
        }
      }
    }
  };

  const handleAddCustomSkill = async () => {
    if (!customSkillName.trim()) return;

    try {
      const created = await userSkillsApi.createMySkill({
        skill_name: customSkillName.trim(),
        rating: 'Beginner',
        is_interested: false,
        is_custom: true,
      });

      const newSkillData: SkillCardData = {
        id: created.skill_id,
        name: customSkillName.trim(),
        rating: 'Beginner',
        employee_skill_id: created.id,
        is_custom: true,
      };

      setMySkills([...mySkills, newSkillData]);
      setCustomSkillName('');
      setShowCustomSkillInput(false);
      
      // Reload all skills to include the new custom skill
      await loadAllSkills();
    } catch (error) {
      console.error('Failed to add custom skill:', error);
      alert('Failed to add custom skill. Please try again.');
    }
  };

  const handleRatingChange = async (skillId: number, rating: 'Beginner' | 'Developing' | 'Intermediate' | 'Advanced' | 'Expert') => {
    const skill = mySkills.find(s => s.id === skillId);
    if (!skill || !skill.employee_skill_id) return;

    try {
      await userSkillsApi.updateMySkill(skill.employee_skill_id, { rating });
      setMySkills(mySkills.map(s =>
        s.id === skillId ? { ...s, rating } : s
      ));
    } catch (error) {
      console.error('Failed to update rating:', error);
    }
  };

  const handleSkillRemove = async (skillId: number) => {
    const skill = mySkills.find(s => s.id === skillId);
    
    if (!skill || !skill.employee_skill_id) return;

    try {
      await userSkillsApi.deleteMySkill(skill.employee_skill_id);
      setMySkills(mySkills.filter(s => s.id !== skillId));
    } catch (error) {
      console.error('Failed to remove skill:', error);
    }
  };

  const excludeSkillIds = mySkills.map((s: SkillCardData) => s.id);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F6F2F4] flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-gray-600">Loading skills...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F7F7F9]">
      {/* Slim Professional Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-2.5 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-1 hover:bg-gray-100 rounded transition-colors"
              title="Back to Profile"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4 text-gray-600">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
            </button>
            <h1 className="text-sm font-semibold text-gray-800">Edit Skills</h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500">{user?.email}</span>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700 font-medium transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-3">
        {/* Instructions Banner */}
        <div className="mb-3 bg-blue-50 border border-blue-200 rounded-md px-3 py-2 flex items-start gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
          </svg>
          <p className="text-xs text-blue-800">
            <strong>Drag skills</strong> from the Master Skills list to add them to your profile. Click rating buttons to set your proficiency level. You can also add custom skills not in the template.
          </p>
        </div>

        <DndContext
          sensors={sensors}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <div className="grid grid-cols-12 gap-3">
            {/* Left Panel - Master Skills Browser */}
            <div className="col-span-4">
              <div className="bg-white rounded-md shadow-sm border border-gray-200 p-3 sticky top-16">
                <div className="flex items-center justify-between mb-2">
                  <h2 className="text-sm font-semibold text-gray-800">Master Skills</h2>
                  <span className="text-xs text-gray-500">{skills.filter(s => !excludeSkillIds.includes(s.id)).length} available</span>
                </div>
                <div className="mb-2">
                  <div className="relative">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3.5 h-3.5 absolute left-2 top-1.5 text-gray-400">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                    </svg>
                    <input
                      type="text"
                      placeholder="Search skills..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-7 pr-2 py-1.5 text-xs border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
                
                <SkillBrowser
                  searchQuery={searchQuery}
                  excludeSkillIds={excludeSkillIds}
                />
              </div>
            </div>

            {/* Right Panel - My Skills */}
            <div className="col-span-8">
              <MySkillsDropZone
                mySkills={mySkills}
                onRatingChange={handleRatingChange}
                onSkillRemove={handleSkillRemove}
              />
            </div>
          </div>

          <DragOverlay>
            {activeId ? (
              <div className="bg-white rounded-md shadow-xl p-2 border-2 border-blue-500 ring-2 ring-blue-200">
                <div className="flex items-center gap-1.5">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3 h-3 text-blue-600">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                  </svg>
                  <span className="font-medium text-gray-800 text-xs">Moving skill...</span>
                </div>
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </div>
    </div>
  );
};

/** Droppable zone for My Skills */
const MySkillsDropZone: React.FC<{
  mySkills: SkillCardData[];
  onRatingChange: (skillId: number, rating: 'Beginner' | 'Developing' | 'Intermediate' | 'Advanced' | 'Expert') => void;
  onSkillRemove: (skillId: number) => void;
}> = ({ mySkills, onRatingChange, onSkillRemove }) => {
  const { setNodeRef, isOver } = useDroppable({
    id: 'skills-column',
  });

  // Separate template and custom skills
  const templateSkills = mySkills.filter(s => !s.is_custom);
  const customSkills = mySkills.filter(s => s.is_custom);

  return (
    <div
      ref={setNodeRef}
      className={`bg-white rounded-md shadow-sm border border-gray-200 p-3 min-h-[500px] transition-all ${
        isOver ? 'ring-2 ring-blue-400 border-blue-400' : ''
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-gray-800">My Skills ({mySkills.length})</h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Proficiency:</span>
          <div className="flex gap-1">
            <span className="px-1.5 py-0.5 rounded-full bg-green-100 text-green-700 font-semibold text-xs">B</span>
            <span className="px-1.5 py-0.5 rounded-full bg-blue-100 text-blue-700 font-semibold text-xs">D</span>
            <span className="px-1.5 py-0.5 rounded-full bg-yellow-100 text-yellow-700 font-semibold text-xs">I</span>
            <span className="px-1.5 py-0.5 rounded-full bg-orange-100 text-orange-700 font-semibold text-xs">A</span>
            <span className="px-1.5 py-0.5 rounded-full bg-purple-100 text-purple-700 font-semibold text-xs">E</span>
          </div>
        </div>
      </div>
      
      <div className="space-y-3 max-h-[calc(100vh-200px)] overflow-y-auto pr-1">
        {mySkills.length === 0 ? (
          <div className={`text-center py-12 rounded-md border-2 border-dashed transition-all ${
            isOver ? 'border-blue-400 bg-blue-50' : 'border-gray-300 bg-gray-50'
          }`}>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-10 h-10 mx-auto mb-2 text-gray-400">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            <p className="text-gray-700 font-medium text-sm">Drop skills here</p>
            <p className="text-gray-500 text-xs mt-1">Drag from Master Skills list or add custom skills</p>
          </div>
        ) : (
          <>
            {/* Template Skills */}
            {templateSkills.length > 0 && (
              <div className="space-y-1.5">
                {templateSkills.map((skill) => (
                  <SkillRow
                    key={skill.id}
                    skill={skill}
                    onRatingChange={onRatingChange}
                    onSkillRemove={onSkillRemove}
                  />
                ))}
              </div>
            )}

            {/* Custom Skills Section */}
            {customSkills.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h3 className="text-xs font-semibold text-gray-600 uppercase mb-2 flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-3.5 h-3.5 text-green-600">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 6h.008v.008H6V6z" />
                  </svg>
                  Custom Skills ({customSkills.length})
                </h3>
                <div className="space-y-1.5">
                  {customSkills.map((skill) => (
                    <SkillRow
                      key={skill.id}
                      skill={skill}
                      onRatingChange={onRatingChange}
                      onSkillRemove={onSkillRemove}
                      isCustom
                    />
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

/** Individual skill row component */
const SkillRow: React.FC<{
  skill: SkillCardData;
  onRatingChange: (skillId: number, rating: 'Beginner' | 'Developing' | 'Intermediate' | 'Advanced' | 'Expert') => void;
  onSkillRemove: (skillId: number) => void;
  isCustom?: boolean;
}> = ({ skill, onRatingChange, onSkillRemove, isCustom }) => {
  return (
    <div className={`bg-white rounded-md p-2 border hover:border-blue-300 hover:shadow-sm transition-all group ${
      isCustom ? 'border-green-200 bg-green-50/30' : 'border-gray-200'
    }`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-gray-900 text-xs truncate">{skill.name}</h3>
            {isCustom && (
              <span className="px-1.5 py-0.5 bg-green-100 text-green-700 text-xs font-semibold rounded">Custom</span>
            )}
          </div>
          {skill.description && (
            <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{skill.description}</p>
          )}
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <div className="flex gap-0.5">
            {(['Beginner', 'Developing', 'Intermediate', 'Advanced', 'Expert'] as const).map((rating) => (
              <button
                key={rating}
                onClick={() => onRatingChange(skill.id, rating)}
                className={`w-6 h-6 rounded-full font-semibold text-xs transition-all ${
                  skill.rating === rating
                    ? rating === 'Beginner' ? 'bg-green-500 text-white shadow-sm'
                    : rating === 'Developing' ? 'bg-blue-500 text-white shadow-sm'
                    : rating === 'Intermediate' ? 'bg-yellow-500 text-white shadow-sm'
                    : rating === 'Advanced' ? 'bg-orange-500 text-white shadow-sm'
                    : 'bg-purple-500 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                }`}
                title={rating}
              >
                {rating.charAt(0)}
              </button>
            ))}
          </div>
          <button
            onClick={() => onSkillRemove(skill.id)}
            className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors opacity-0 group-hover:opacity-100"
            title="Remove skill"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-3.5 h-3.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};
