/** Right area: Two columns for Existing Skills and Interested Skills. */
import React from 'react';
import {
  SortableContext,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { useDroppable } from '@dnd-kit/core';
import { SkillCard, SkillCardData } from './SkillCard';

interface ColumnsAreaProps {
  existingSkills: SkillCardData[];
  interestedSkills: SkillCardData[];
  onExistingSkillsChange: (skills: SkillCardData[]) => void;
  onInterestedSkillsChange: (skills: SkillCardData[]) => void;
  onRatingChange: (skillId: number, rating: 'Beginner' | 'Developing' | 'Intermediate' | 'Advanced' | 'Expert') => void;
  onSkillAdd: (skill: SkillCardData, column: 'existing' | 'interested') => void;
}

export const ColumnsArea: React.FC<ColumnsAreaProps> = ({
  existingSkills,
  interestedSkills,
  onExistingSkillsChange,
  onInterestedSkillsChange,
  onRatingChange,
  onSkillAdd,
}) => {
  // Drag handling is now done in App component's DndContext

  // Use DndContext from parent (App component)
  // This component now just handles the drag end logic
  return (
    <div className="grid grid-cols-2 gap-4 h-full">
      {/* Existing Skills Column */}
      <SortableColumn
        id="existing-column"
        title="Existing Skills"
        skills={existingSkills}
        onRatingChange={onRatingChange}
        columnType="existing"
      />

      {/* Interested Skills Column */}
      <SortableColumn
        id="interested-column"
        title="Interested Skills"
        skills={interestedSkills}
        onRatingChange={onRatingChange}
        columnType="interested"
      />
    </div>
  );
};

/** Sortable column component. */
const SortableColumn: React.FC<{
  id: string;
  title: string;
  skills: SkillCardData[];
  onRatingChange: (skillId: number, rating: 'Beginner' | 'Developing' | 'Intermediate' | 'Advanced' | 'Expert') => void;
  columnType: 'existing' | 'interested';
}> = ({ id, title, skills, onRatingChange, columnType }) => {
  const { setNodeRef, isOver } = useDroppable({ id });

  const skillIds = skills.map((s) => s.id);

  return (
    <div
      ref={setNodeRef}
      className={`
        bg-gray-50 rounded-lg p-4 border-2 border-dashed min-h-[400px]
        ${isOver ? 'border-blue-400 bg-blue-50' : 'border-gray-300'}
        transition-colors
      `}
    >
      <h2 className="text-lg font-semibold mb-4 text-gray-700">
        {title} ({skills.length})
      </h2>
      {/* Let the list grow naturally without an internal scrollbar */}
      <div className="min-h-[300px] space-y-2">
        <SortableContext items={skillIds} strategy={verticalListSortingStrategy}>
          {skills.length === 0 ? (
            <div className="text-center text-gray-400 py-8 min-h-[200px] flex items-center justify-center">
              <div>
                <p className="text-lg mb-2">Drop skills here</p>
                <p className="text-sm">Drag from the skill list on the left</p>
              </div>
            </div>
          ) : (
            skills.map((skill) => (
              <SkillCard
                key={skill.id}
                skill={skill}
                onRatingChange={onRatingChange}
                showRating={columnType === 'existing'}  // Only show rating for existing skills
                columnType={columnType}
              />
            ))
          )}
        </SortableContext>
      </div>
    </div>
  );
};

