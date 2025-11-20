// @ts-nocheck
/** Employee Dashboard - Main page for employees to manage their skills. */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DndContext, DragOverlay, useSensor, useSensors, PointerSensor, KeyboardSensor, pointerWithin, DragEndEvent, DragStartEvent } from '@dnd-kit/core';
import { arrayMove } from '@dnd-kit/sortable';
import { SkillBrowser } from '../components/SkillBrowser';
import { ColumnsArea } from '../components/ColumnsArea';
import { SkillCardData } from '../components/SkillCard';
import { authApi, userSkillsApi, skillsApi, Skill, EmployeeSkill } from '../services/api';

const DndContextWrapper: React.FC<{ 
  children: React.ReactNode;
  onDragStart?: (event: DragStartEvent) => void;
  onDragEnd: (event: DragEndEvent) => void;
  overlay?: React.ReactNode;
}> = ({ children, onDragStart, onDragEnd, overlay }) => {
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        delay: 150,
        tolerance: 5,
      },
    }),
    useSensor(KeyboardSensor)
  );

  return (
    <DndContext 
      sensors={sensors} 
      collisionDetection={pointerWithin} 
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
    >
      {children}
      {/* Overlay preserves pickup offset; no snap-to-center modifier applied */}
      <DragOverlay>
        {overlay || null}
      </DragOverlay>
    </DndContext>
  );
};

export const EmployeeDashboard: React.FC = () => {
  const [existingSkills, setExistingSkills] = useState<SkillCardData[]>([]);
  const [interestedSkills, setInterestedSkills] = useState<SkillCardData[]>([]);
  const [activeOverlay, setActiveOverlay] = useState<React.ReactNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [user, setUser] = useState(authApi.getUser());
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user is logged in
    if (!user) {
      navigate('/login');
      return;
    }

    loadSkills();
  }, []);

  const loadSkills = async () => {
    try {
      setLoading(true);
      const employeeSkills = await userSkillsApi.getMySkills();
      
      // Separate existing and interested skills
      const existing: SkillCardData[] = [];
      const interested: SkillCardData[] = [];
      
      employeeSkills.forEach((es: EmployeeSkill) => {
        const skillData: SkillCardData = {
          id: es.skill_id,
          employee_skill_id: es.id,  // Store employee_skill.id for updates
          name: es.skill?.name || 'Unknown',
          description: es.skill?.description,
          rating: es.rating || undefined,  // Rating may be null for interested skills
          years_experience: es.years_experience,
        };
        
        if (es.is_interested) {
          interested.push(skillData);
        } else {
          existing.push(skillData);
        }
      });
      
      setExistingSkills(existing);
      setInterestedSkills(interested);
    } catch (error) {
      console.error('Failed to load skills:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveSkills = async () => {
    setSaving(true);
    setSaveMessage('');
    
    try {
      // Save all existing skills
      for (const skill of existingSkills) {
        await userSkillsApi.createMySkill({
          skill_name: skill.name,
          rating: skill.rating || 'Beginner',  // Required for existing skills
          years_experience: skill.years_experience,
          is_interested: false,
        });
      }
      
      // Save all interested skills (no rating needed)
      for (const skill of interestedSkills) {
        await userSkillsApi.createMySkill({
          skill_name: skill.name,
          rating: undefined,  // No rating for interested skills
          years_experience: skill.years_experience,
          is_interested: true,
        });
      }
      
      setSaveMessage('Skills saved successfully!');
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (error) {
      console.error('Failed to save skills:', error);
      setSaveMessage('Failed to save skills. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleSkillAdd = (
    skill: SkillCardData,
    column: 'existing' | 'interested'
  ) => {
    // Check if skill already exists
    const existsInExisting = existingSkills.some((s) => s.id === skill.id);
    const existsInInterested = interestedSkills.some((s) => s.id === skill.id);

    if (existsInExisting || existsInInterested) {
      return;
    }

    if (column === 'existing') {
      setExistingSkills([...existingSkills, skill]);
    } else {
      setInterestedSkills([...interestedSkills, skill]);
    }
  };

  const handleRatingChange = (
    skillId: number,
    rating: 'Beginner' | 'Developing' | 'Intermediate' | 'Advanced' | 'Expert'
  ) => {
    setExistingSkills(
      existingSkills.map((s) => (s.id === skillId ? { ...s, rating } : s))
    );
    setInterestedSkills(
      interestedSkills.map((s) => (s.id === skillId ? { ...s, rating } : s))
    );
  };

  const handleSkillMove = async (
    skillId: number,
    fromColumn: 'existing' | 'interested',
    toColumn: 'existing' | 'interested'
  ) => {
    // Find the skill in the source column
    const sourceSkills = fromColumn === 'existing' ? existingSkills : interestedSkills;
    const skillToMove = sourceSkills.find((s) => s.id === skillId);
    
    if (!skillToMove || !skillToMove.employee_skill_id) {
      // If no employee_skill_id, it's a new skill - use createMySkill instead
      return;
    }

    try {
      // Update the skill's is_interested flag
      await userSkillsApi.updateMySkill(skillToMove.employee_skill_id, {
        is_interested: toColumn === 'interested',
        rating: toColumn === 'existing' ? (skillToMove.rating || 'Beginner') : undefined,
      });
    } catch (error) {
      console.error('Failed to update skill:', error);
      // Reload skills on error to sync state
      loadSkills();
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    // Helper to parse a droppable card id like "existing-123" or "interested-456"
    const parseTargetId = (idStr: string, prefix: 'existing' | 'interested') => {
      if (!idStr) return null;
      if (idStr.startsWith(`${prefix}-`)) {
        const num = parseInt(idStr.slice(prefix.length + 1), 10);
        return isNaN(num) ? null : num;
      }
      return null;
    };

    // Check if dragging from master list
    if (activeId.toString().startsWith('skill-')) {
      const skillId = parseInt(activeId.toString().replace('skill-', ''));
      const skillData = active.data.current?.skill as Skill;
      
      if (skillData) {
        // Check if dropped on existing column (including cards)
        if (overId === 'existing-column' || 
            overId.toString().startsWith('existing-')) {
          const newSkill: SkillCardData = {
            id: skillData.id,
            name: skillData.name,
            description: skillData.description,
            rating: 'Beginner',
          };
          // If dropped over a specific card, insert before that card
          const targetId = parseTargetId(overId.toString(), 'existing');
          if (targetId !== null) {
            const alreadyExists = existingSkills.some((s) => s.id === newSkill.id);
            if (!alreadyExists) {
              const targetIndex = existingSkills.findIndex((s) => s.id === targetId);
              const arr = [...existingSkills];
              arr.splice(targetIndex >= 0 ? targetIndex : arr.length, 0, newSkill);
              setExistingSkills(arr);
            }
          } else {
            // Dropped on column background, append to end
            handleSkillAdd(newSkill, 'existing');
          }
        } 
        // Check if dropped on interested column (including cards)
        else if (overId === 'interested-column' || 
                 overId.toString().startsWith('interested-')) {
          const newSkill: SkillCardData = {
            id: skillData.id,
            name: skillData.name,
            description: skillData.description,
            rating: undefined,  // No rating for interested skills
          };
          const targetId = parseTargetId(overId.toString(), 'interested');
          if (targetId !== null) {
            const alreadyExists = interestedSkills.some((s) => s.id === newSkill.id);
            if (!alreadyExists) {
              const targetIndex = interestedSkills.findIndex((s) => s.id === targetId);
              const arr = [...interestedSkills];
              arr.splice(targetIndex >= 0 ? targetIndex : arr.length, 0, newSkill);
              setInterestedSkills(arr);
            }
          } else {
            handleSkillAdd(newSkill, 'interested');
          }
        }
      }
      return;
    }

    // Handle moving between columns
    const activeSkillId = parseInt(activeId.toString());
    const activeInExisting = existingSkills.find((s) => s.id === activeSkillId);
    const activeInInterested = interestedSkills.find((s) => s.id === activeSkillId);

    if (activeInExisting) {
      if (overId === 'interested-column' || 
          overId.toString().startsWith('interested-')) {
        // Move from existing to interested - remove rating
        setExistingSkills(existingSkills.filter((s) => s.id !== activeSkillId));
        const targetId = parseTargetId(overId.toString(), 'interested');
        const movedItem: SkillCardData = { ...activeInExisting, rating: undefined };
        if (targetId !== null) {
          const targetIndex = interestedSkills.findIndex((s) => s.id === targetId);
          const arr = [...interestedSkills];
          arr.splice(targetIndex >= 0 ? targetIndex : arr.length, 0, movedItem);
          setInterestedSkills(arr);
        } else {
          setInterestedSkills([...interestedSkills, movedItem]);
        }
        // Save to backend
        handleSkillMove(activeSkillId, 'existing', 'interested');
      } else {
        // Reorder within existing
        const overSkillId = parseInt(overId.toString());
        const overInExisting = existingSkills.find((s) => s.id === overSkillId);
        if (overInExisting) {
          const oldIndex = existingSkills.findIndex((s) => s.id === activeSkillId);
          const newIndex = existingSkills.findIndex((s) => s.id === overSkillId);
          setExistingSkills(arrayMove(existingSkills, oldIndex, newIndex));
        }
      }
    } else if (activeInInterested) {
      if (overId === 'existing-column' || 
          overId.toString().startsWith('existing-')) {
        // Move from interested to existing - add default rating
        setInterestedSkills(interestedSkills.filter((s) => s.id !== activeSkillId));
        const targetId = parseTargetId(overId.toString(), 'existing');
        const movedItem: SkillCardData = { ...activeInInterested, rating: 'Beginner' };
        if (targetId !== null) {
          const targetIndex = existingSkills.findIndex((s) => s.id === targetId);
          const arr = [...existingSkills];
          arr.splice(targetIndex >= 0 ? targetIndex : arr.length, 0, movedItem);
          setExistingSkills(arr);
        } else {
          setExistingSkills([...existingSkills, movedItem]);
        }
        // Save to backend
        handleSkillMove(activeSkillId, 'interested', 'existing');
      } else {
        // Reorder within interested
        const overSkillId = parseInt(overId.toString());
        const overInInterested = interestedSkills.find((s) => s.id === overSkillId);
        if (overInInterested) {
          const oldIndex = interestedSkills.findIndex((s) => s.id === activeSkillId);
          const newIndex = interestedSkills.findIndex((s) => s.id === overSkillId);
          setInterestedSkills(arrayMove(interestedSkills, oldIndex, newIndex));
        }
      }
    }
  };

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    const activeId = String(active.id);
    // Master list drag
    if (activeId.startsWith('skill-')) {
      const skillData = active.data.current?.skill as Skill | undefined;
      if (skillData) {
        setActiveOverlay(
          <div className="bg-white rounded-lg shadow-lg p-4 border-2 border-blue-400 w-[320px]">
            <h3 className="font-semibold text-gray-800">{skillData.name}</h3>
            {skillData.description && (
              <p className="text-sm text-gray-600 mt-1">{skillData.description}</p>
            )}
          </div>
        );
      }
      return;
    }
    // Existing/interested card drag
    const numericId = parseInt(activeId, 10);
    if (!isNaN(numericId)) {
      const found = existingSkills.find(s => s.id === numericId) || interestedSkills.find(s => s.id === numericId);
      if (found) {
        setActiveOverlay(
          <div className="bg-white rounded-lg shadow-lg p-4 border-2 border-blue-400 w-[320px]">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="font-semibold text-gray-800">{found.name}</h3>
                {found.description && (
                  <p className="text-sm text-gray-600 mt-1">{found.description}</p>
                )}
              </div>
              {found.rating && (
                <span className="ml-4 inline-block text-xs px-2 py-1 rounded bg-blue-100 text-blue-700">{found.rating}</span>
              )}
            </div>
          </div>
        );
      }
    }
  };

  const handleLogout = () => {
    authApi.logout();
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-gray-600">Loading your skills...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">Skillboard - My Skills</h1>
          <div className="flex gap-2 items-center">
            <span className="text-sm text-gray-600">{user?.email}</span>
            <button
              onClick={() => navigate('/skill-gap')}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Skill Gap Analysis
            </button>
            {user?.is_admin && (
              <button
                onClick={() => navigate('/admin/dashboard')}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Admin Dashboard
              </button>
            )}
            <button
              onClick={saveSkills}
              disabled={saving}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
            {saveMessage && (
              <span className={`text-sm ${saveMessage.includes('Failed') ? 'text-red-600' : 'text-green-600'}`}>
                {saveMessage}
              </span>
            )}
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <DndContextWrapper onDragStart={handleDragStart} onDragEnd={handleDragEnd} overlay={activeOverlay}>
        <div className="max-w-7xl mx-auto px-4 py-6">
          {/* Allow natural page scrolling by removing fixed viewport height */}
          <div className="grid grid-cols-4 gap-4">
            {/* Left Panel: Master Skills */}
            <div className="col-span-1 bg-white rounded-lg shadow-md border border-gray-200">
              <div className="p-4 border-b border-gray-200">
                <input
                  type="text"
                  placeholder="Search skills..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <SkillBrowser 
                searchQuery={searchQuery} 
                excludeSkillIds={[
                  ...existingSkills.map(s => s.id),
                  ...interestedSkills.map(s => s.id)
                ]}
              />
            </div>

            {/* Right Area: Two Columns */}
            <div className="col-span-3">
              <ColumnsArea
                existingSkills={existingSkills}
                interestedSkills={interestedSkills}
                onExistingSkillsChange={setExistingSkills}
                onInterestedSkillsChange={setInterestedSkills}
                onRatingChange={handleRatingChange}
                onSkillAdd={handleSkillAdd}
              />
            </div>
          </div>
        </div>
      </DndContextWrapper>
    </div>
  );
};

