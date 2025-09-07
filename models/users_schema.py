from datetime import datetime , timezone
from typing import List, Optional
import time
from dataclasses import dataclass, field

from enum import Enum

class Grade(Enum):
    GRADE_6 = "6"
    GRADE_7 = "7"
    GRADE_8 = "8"
    GRADE_9 = "9"
    GRADE_10 = "10"
    GRADE_11 = "11"
    GRADE_12 = "12"

class Board(Enum):
    CBSE = "CBSE"
    ICSE = "ICSE"
    IB = "IB"
    OTHER = "Other"

class Language(Enum):
    ENGLISH = "English"
    HINGLISH = "Hinglish"
    TAMIL = "Tamil"
    KANNADA = "Kannada"

class FontSize(Enum):
    NORMAL = "Normal"
    LARGE = "Large"

@dataclass
class AccessibilitySettings:
    font_size: FontSize = FontSize.NORMAL
    read_aloud: bool = False

@dataclass
class UserPreferences:
    language: Language = Language.ENGLISH
    accessibility: AccessibilitySettings = field(default_factory=AccessibilitySettings)
    notif_opt_in: bool = False
    quiet_hours_start: Optional[str] = None  # "22:00"
    quiet_hours_end: Optional[str] = None    # "08:00"

@dataclass
class User:
    # Required fields
    id: str
    email: str
    name: str
    
	#additionals
    grade: Optional[Grade] = None
    board: Optional[Board] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    school: Optional[str] = None
    
    # Preferences
    preferences: UserPreferences = field(default_factory=UserPreferences)
    
    # Interests
    interests: List[str] = field(default_factory=list)
    custom_interests: List[str] = field(default_factory=list)
    
    # Consent and tracking
    terms_and_conditions: bool = False
    personalized_content: bool = True
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=datetime.now(timezone.utc))
    onboarding_completed: bool = False
    last_login: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert User object to dictionary for JSON """
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'grade': self.grade.value if self.grade else None,
            'board': self.board.value if self.board else None,
            'city': self.city,
            'timezone': self.timezone,
            'school': self.school,
            'preferences': {
                'language': self.preferences.language.value,
                'accessibility': {
                    'font_size': self.preferences.accessibility.font_size.value,
                    'read_aloud': self.preferences.accessibility.read_aloud
                },
                'notif_opt_in': self.preferences.notif_opt_in,
                'quiet_hours_start': self.preferences.quiet_hours_start,
                'quiet_hours_end': self.preferences.quiet_hours_end
            },
            'interests': self.interests,
            'custom_interests': self.custom_interests,
            'terms_and_conditions': self.terms_and_conditions,
            'personalized_content': self.personalized_content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'onboarding_completed': self.onboarding_completed,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create User object from dictionary"""
        # Handle preferences
        prefs_data = data.get('preferences', {})
        accessibility_data = prefs_data.get('accessibility', {})
        
        preferences = UserPreferences(
            language=Language(prefs_data.get('language', 'English')),
            accessibility=AccessibilitySettings(
                font_size=FontSize(accessibility_data.get('font_size', 'Normal')),
                read_aloud=accessibility_data.get('read_aloud', False)
            ),
            notif_opt_in=prefs_data.get('notif_opt_in', False),
            quiet_hours_start=prefs_data.get('quiet_hours_start'),
            quiet_hours_end=prefs_data.get('quiet_hours_end')
        )
        
        return cls(
            id=data['id'],
            email=data['email'],
            name=data['name'],
            grade=Grade(data['grade']) if data.get('grade') else None,
            board=Board(data['board']) if data.get('board') else None,
            city=data.get('city'),
            timezone=data.get('timezone'),
            school=data.get('school'),
            preferences=preferences,
            interests=data.get('interests', []),
            custom_interests=data.get('custom_interests', []),
            terms_and_conditions=data.get('terms_and_conditions', False),
            personalized_content=data.get('personalized_content', True),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(timezone.utc),
            onboarding_completed=data.get('onboarding_completed', False),
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None
        )
    
    def complete_onboarding(self):
        """Mark onboarding as completed"""
        self.onboarding_completed = True
        self.updated_at = datetime.now(timezone.utc)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)