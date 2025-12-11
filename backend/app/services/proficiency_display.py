"""Proficiency Display Service for consistent visual indicators.

This service provides consistent mapping of proficiency levels to visual
indicators including colors, icons, and numeric values.
"""
from typing import Dict, Optional
from pydantic import BaseModel
from enum import Enum


class ProficiencyLevel(str, Enum):
    """Proficiency level enumeration."""
    BEGINNER = "Beginner"
    DEVELOPING = "Developing"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"


class ProficiencyDisplay(BaseModel):
    """Visual display information for a proficiency level."""
    level: str
    color: str
    icon: str
    numeric_value: int  # 1-5 for calculations
    description: str
    css_class: str


class ProficiencyDisplayService:
    """
    Service for mapping proficiency levels to visual indicators.
    
    Provides consistent visual representation across the application.
    """
    
    # Proficiency display configurations
    PROFICIENCY_CONFIG: Dict[str, ProficiencyDisplay] = {
        "Beginner": ProficiencyDisplay(
            level="Beginner",
            color="#EF4444",  # Red
            icon="circle-1",
            numeric_value=1,
            description="Basic understanding, requires guidance",
            css_class="proficiency-beginner"
        ),
        "Developing": ProficiencyDisplay(
            level="Developing",
            color="#F97316",  # Orange
            icon="circle-2",
            numeric_value=2,
            description="Growing skills, some supervision needed",
            css_class="proficiency-developing"
        ),
        "Intermediate": ProficiencyDisplay(
            level="Intermediate",
            color="#EAB308",  # Yellow
            icon="circle-3",
            numeric_value=3,
            description="Competent, works independently",
            css_class="proficiency-intermediate"
        ),
        "Advanced": ProficiencyDisplay(
            level="Advanced",
            color="#22C55E",  # Green
            icon="circle-4",
            numeric_value=4,
            description="Highly skilled, can mentor others",
            css_class="proficiency-advanced"
        ),
        "Expert": ProficiencyDisplay(
            level="Expert",
            color="#3B82F6",  # Blue
            icon="circle-5",
            numeric_value=5,
            description="Industry expert, thought leader",
            css_class="proficiency-expert"
        )
    }
    
    # Aliases for common variations
    LEVEL_ALIASES: Dict[str, str] = {
        "beginner": "Beginner",
        "developing": "Developing",
        "intermediate": "Intermediate",
        "advanced": "Advanced",
        "expert": "Expert",
        "1": "Beginner",
        "2": "Developing",
        "3": "Intermediate",
        "4": "Advanced",
        "5": "Expert",
        "basic": "Beginner",
        "novice": "Beginner",
        "junior": "Developing",
        "mid": "Intermediate",
        "senior": "Advanced",
        "lead": "Expert",
        "master": "Expert"
    }
    
    def get_proficiency_display(self, rating: str) -> ProficiencyDisplay:
        """
        Get the display configuration for a proficiency rating.
        
        Args:
            rating: The proficiency rating (e.g., "Beginner", "Expert")
            
        Returns:
            ProficiencyDisplay with visual indicator information
        """
        # Normalize the rating
        normalized = self._normalize_rating(rating)
        
        # Return the display config or default to Beginner
        return self.PROFICIENCY_CONFIG.get(normalized, self.PROFICIENCY_CONFIG["Beginner"])
    
    def _normalize_rating(self, rating: str) -> str:
        """Normalize a rating string to standard format."""
        if not rating:
            return "Beginner"
        
        # Check direct match first
        if rating in self.PROFICIENCY_CONFIG:
            return rating
        
        # Check aliases
        lower_rating = rating.lower().strip()
        if lower_rating in self.LEVEL_ALIASES:
            return self.LEVEL_ALIASES[lower_rating]
        
        # Default to Beginner
        return "Beginner"
    
    def get_numeric_value(self, rating: str) -> int:
        """Get the numeric value (1-5) for a proficiency rating."""
        display = self.get_proficiency_display(rating)
        return display.numeric_value
    
    def get_color(self, rating: str) -> str:
        """Get the color for a proficiency rating."""
        display = self.get_proficiency_display(rating)
        return display.color
    
    def get_all_levels(self) -> list:
        """Get all proficiency levels in order."""
        return list(self.PROFICIENCY_CONFIG.keys())
    
    def compare_proficiency(self, rating1: str, rating2: str) -> int:
        """
        Compare two proficiency ratings.
        
        Returns:
            -1 if rating1 < rating2
            0 if rating1 == rating2
            1 if rating1 > rating2
        """
        val1 = self.get_numeric_value(rating1)
        val2 = self.get_numeric_value(rating2)
        
        if val1 < val2:
            return -1
        elif val1 > val2:
            return 1
        return 0
    
    def meets_requirement(self, actual: str, required: str) -> bool:
        """Check if actual proficiency meets or exceeds required level."""
        return self.compare_proficiency(actual, required) >= 0
    
    def calculate_gap(self, actual: str, required: str) -> int:
        """
        Calculate the gap between actual and required proficiency.
        
        Returns:
            Positive number if below requirement (gap exists)
            Zero if meets requirement
            Negative number if exceeds requirement
        """
        actual_val = self.get_numeric_value(actual)
        required_val = self.get_numeric_value(required)
        return required_val - actual_val


# Singleton instance
proficiency_service = ProficiencyDisplayService()