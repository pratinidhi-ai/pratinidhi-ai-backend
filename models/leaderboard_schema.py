from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Region:
    """User's geographic location"""
    country: str
    state: str
    city: str
    
    def to_dict(self):
        return {
            'country': self.country,
            'state': self.state,
            'city': self.city
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            country=data.get('country', ''),
            state=data.get('state', ''),
            city=data.get('city', '')
        )

@dataclass
class PerformanceMetric:
    """User's performance statistics"""
    rating: int = 0
    correct_questions: int = 0
    score: int = 0
    total_questions: int = 0
    total_quiz: int = 0
    
    def to_dict(self):
        return {
            'rating': self.rating,
            'correct_questions': self.correct_questions,
            'score': self.score,
            'total_questions': self.total_questions,
            'total_quiz': self.total_quiz
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            rating=data.get('rating', 0),
            correct_questions=data.get('correct_questions', 0),
            score=data.get('score', 0),
            total_questions=data.get('total_questions', 0),
            total_quiz=data.get('total_quiz', 0)
        )
    
    def calculate_accuracy(self) -> float:
        """Calculate accuracy percentage"""
        if self.total_questions == 0:
            return 0.0
        return (self.correct_questions / self.total_questions) * 100
    
    def update_from_quiz(self, correct: int, total: int, points: int):
        """
        Update metrics after completing a quiz
        
        Args:
            correct: Number of correct answers
            total: Total number of questions in quiz
            points: Points earned from the quiz
        """
        self.correct_questions += correct
        self.total_questions += total
        self.score += points
        self.total_quiz += 1

@dataclass
class LeaderboardEntity:
    """Leaderboard entry for a user"""
    user_id: str
    region: Region
    performance_metric: PerformanceMetric
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'region': self.region.to_dict(),
            'performance_metric': self.performance_metric.to_dict(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            user_id=data.get('user_id', ''),
            region=Region.from_dict(data.get('region', {})),
            performance_metric=PerformanceMetric.from_dict(data.get('performance_metric', {})),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )
    
    def __repr__(self):
        accuracy = self.performance_metric.calculate_accuracy()
        return (f"LeaderboardEntity(user_id='{self.user_id}', "
                f"region={self.region.city}, {self.region.state}, {self.region.country}, "
                f"rating={self.performance_metric.rating}, "
                f"score={self.performance_metric.score}, "
                f"accuracy={accuracy:.1f}%)")