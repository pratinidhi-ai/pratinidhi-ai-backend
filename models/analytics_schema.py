"""
Analytics Schema Models
Data classes for student performance analytics and tracking
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone


def _get_utc_now():
    """Get current UTC timestamp"""
    return datetime.now(timezone.utc)


@dataclass
class TagDetail:
    """Details for a specific tag's performance"""
    tag: str
    total_questions: int
    correct_answers: int
    incorrect_answers: int = 0
    score: int = 0  # Calculated based on difficulty
    total_possible_score: int = 0
    
    def __post_init__(self):
        """Calculate derived fields"""
        self.incorrect_answers = self.total_questions - self.correct_answers
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'tag': self.tag,
            'total_questions': self.total_questions,
            'correct_answers': self.correct_answers,
            'incorrect_answers': self.incorrect_answers,
            'score': self.score,
            'total_possible_score': self.total_possible_score,
            'accuracy': round((self.correct_answers / self.total_questions * 100), 2) if self.total_questions > 0 else 0
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TagDetail':
        """Create from dictionary"""
        return cls(
            tag=data['tag'],
            total_questions=data['total_questions'],
            correct_answers=data['correct_answers'],
            incorrect_answers=data.get('incorrect_answers', 0),
            score=data.get('score', 0),
            total_possible_score=data.get('total_possible_score', 0)
        )


@dataclass
class QuizSubmission:
    """
    Data submitted after a quiz/practice test is completed
    This represents a single quiz session
    """
    student_id: str
    time_spent: int  # in seconds
    number_of_questions: int
    number_of_correct_answers: int
    subject: str
    sub_category: str
    difficulty_level: int  # 1-5
    tag_wise_details: List[TagDetail]
    correct_question_ids: List[str]
    incorrect_question_ids: List[str]
    timestamp: datetime = field(default_factory=_get_utc_now)
    session_id: Optional[str] = None  # Auto-generated unique ID
    
    def __post_init__(self):
        """Validate and process submission data"""
        # Validate difficulty level
        if self.difficulty_level not in [1, 2, 3, 4, 5]:
            raise ValueError("Difficulty level must be between 1 and 5")
        
        # Validate counts
        if self.number_of_questions != len(self.correct_question_ids) + len(self.incorrect_question_ids):
            raise ValueError("Total questions must equal sum of correct and incorrect question counts")
        
        # Convert tag_wise_details to TagDetail objects if they're dicts
        if self.tag_wise_details and len(self.tag_wise_details) > 0 and isinstance(self.tag_wise_details[0], dict):
            self.tag_wise_details = [TagDetail.from_dict(tag) if isinstance(tag, dict) else tag 
                                    for tag in self.tag_wise_details]
    
    def calculate_score(self) -> int:
        """
        Calculate total score based on difficulty level
        Each question is worth points equal to its difficulty level
        """
        return self.number_of_correct_answers * self.difficulty_level
    
    def calculate_total_possible_score(self) -> int:
        """Calculate maximum possible score for this quiz"""
        return self.number_of_questions * self.difficulty_level
    
    def get_accuracy(self) -> float:
        """Calculate accuracy percentage"""
        if self.number_of_questions == 0:
            return 0.0
        return round((self.number_of_correct_answers / self.number_of_questions * 100), 2)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'student_id': self.student_id,
            'time_spent': self.time_spent,
            'number_of_questions': self.number_of_questions,
            'number_of_correct_answers': self.number_of_correct_answers,
            'subject': self.subject,
            'sub_category': self.sub_category,
            'difficulty_level': self.difficulty_level,
            'tag_wise_details': [tag.to_dict() for tag in self.tag_wise_details],
            'correct_question_ids': self.correct_question_ids,
            'incorrect_question_ids': self.incorrect_question_ids,
            'score': self.calculate_score(),
            'total_possible_score': self.calculate_total_possible_score(),
            'accuracy': self.get_accuracy(),
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'session_id': self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'QuizSubmission':
        """Create from dictionary"""
        return cls(
            student_id=data['student_id'],
            time_spent=data['time_spent'],
            number_of_questions=data['number_of_questions'],
            number_of_correct_answers=data['number_of_correct_answers'],
            subject=data['subject'],
            sub_category=data['sub_category'],
            difficulty_level=data['difficulty_level'],
            tag_wise_details=data['tag_wise_details'],  # Will be converted in __post_init__
            correct_question_ids=data['correct_question_ids'],
            incorrect_question_ids=data['incorrect_question_ids'],
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else _get_utc_now(),
            session_id=data.get('session_id')
        )


@dataclass
class SubCategoryPerformance:
    """Performance metrics at sub_category level"""
    sub_category: str
    total_questions_attempted: int = 0
    total_correct_answers: int = 0
    total_score: int = 0
    total_possible_score: int = 0
    total_time_spent: int = 0  # in seconds
    quiz_count: int = 0
    tags: Dict[str, 'TagPerformance'] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=_get_utc_now)
    
    def get_accuracy(self) -> float:
        """Calculate accuracy percentage"""
        if self.total_questions_attempted == 0:
            return 0.0
        return round((self.total_correct_answers / self.total_questions_attempted * 100), 2)
    
    def get_score_percentage(self) -> float:
        """Calculate score as percentage of possible score"""
        if self.total_possible_score == 0:
            return 0.0
        return round((self.total_score / self.total_possible_score * 100), 2)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'sub_category': self.sub_category,
            'total_questions_attempted': self.total_questions_attempted,
            'total_correct_answers': self.total_correct_answers,
            'total_score': self.total_score,
            'total_possible_score': self.total_possible_score,
            'total_time_spent': self.total_time_spent,
            'quiz_count': self.quiz_count,
            'accuracy': self.get_accuracy(),
            'score_percentage': self.get_score_percentage(),
            'tags': {tag_name: tag_perf.to_dict() for tag_name, tag_perf in self.tags.items()},
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SubCategoryPerformance':
        """Create from dictionary"""
        tags_data = data.get('tags', {})
        tags = {tag_name: TagPerformance.from_dict(tag_data) 
                for tag_name, tag_data in tags_data.items()}
        
        return cls(
            sub_category=data['sub_category'],
            total_questions_attempted=data.get('total_questions_attempted', 0),
            total_correct_answers=data.get('total_correct_answers', 0),
            total_score=data.get('total_score', 0),
            total_possible_score=data.get('total_possible_score', 0),
            total_time_spent=data.get('total_time_spent', 0),
            quiz_count=data.get('quiz_count', 0),
            tags=tags,
            last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else _get_utc_now()
        )


@dataclass
class TagPerformance:
    """Performance metrics at tag level"""
    tag: str
    total_questions_attempted: int = 0
    total_correct_answers: int = 0
    total_score: int = 0
    total_possible_score: int = 0
    
    def get_accuracy(self) -> float:
        """Calculate accuracy percentage"""
        if self.total_questions_attempted == 0:
            return 0.0
        return round((self.total_correct_answers / self.total_questions_attempted * 100), 2)
    
    def get_score_percentage(self) -> float:
        """Calculate score as percentage"""
        if self.total_possible_score == 0:
            return 0.0
        return round((self.total_score / self.total_possible_score * 100), 2)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'tag': self.tag,
            'total_questions_attempted': self.total_questions_attempted,
            'total_correct_answers': self.total_correct_answers,
            'total_score': self.total_score,
            'total_possible_score': self.total_possible_score,
            'accuracy': self.get_accuracy(),
            'score_percentage': self.get_score_percentage()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TagPerformance':
        """Create from dictionary"""
        return cls(
            tag=data['tag'],
            total_questions_attempted=data.get('total_questions_attempted', 0),
            total_correct_answers=data.get('total_correct_answers', 0),
            total_score=data.get('total_score', 0),
            total_possible_score=data.get('total_possible_score', 0)
        )


@dataclass
class SubjectPerformance:
    """Performance metrics at subject level"""
    subject: str
    total_questions_attempted: int = 0
    total_correct_answers: int = 0
    total_score: int = 0
    total_possible_score: int = 0
    total_time_spent: int = 0  # in seconds
    quiz_count: int = 0
    sub_categories: Dict[str, SubCategoryPerformance] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=_get_utc_now)
    
    def get_accuracy(self) -> float:
        """Calculate accuracy percentage"""
        if self.total_questions_attempted == 0:
            return 0.0
        return round((self.total_correct_answers / self.total_questions_attempted * 100), 2)
    
    def get_score_percentage(self) -> float:
        """Calculate score as percentage"""
        if self.total_possible_score == 0:
            return 0.0
        return round((self.total_score / self.total_possible_score * 100), 2)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'subject': self.subject,
            'total_questions_attempted': self.total_questions_attempted,
            'total_correct_answers': self.total_correct_answers,
            'total_score': self.total_score,
            'total_possible_score': self.total_possible_score,
            'total_time_spent': self.total_time_spent,
            'quiz_count': self.quiz_count,
            'accuracy': self.get_accuracy(),
            'score_percentage': self.get_score_percentage(),
            'sub_categories': {sub_cat: sub_perf.to_dict() 
                              for sub_cat, sub_perf in self.sub_categories.items()},
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SubjectPerformance':
        """Create from dictionary"""
        sub_cats_data = data.get('sub_categories', {})
        sub_categories = {sub_cat: SubCategoryPerformance.from_dict(sub_data) 
                         for sub_cat, sub_data in sub_cats_data.items()}
        
        return cls(
            subject=data['subject'],
            total_questions_attempted=data.get('total_questions_attempted', 0),
            total_correct_answers=data.get('total_correct_answers', 0),
            total_score=data.get('total_score', 0),
            total_possible_score=data.get('total_possible_score', 0),
            total_time_spent=data.get('total_time_spent', 0),
            quiz_count=data.get('quiz_count', 0),
            sub_categories=sub_categories,
            last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else _get_utc_now()
        )


@dataclass
class PerformanceSummary:
    """
    Overall performance summary for a student
    Stores aggregated data at subject, sub_category, and tag levels
    """
    student_id: str
    total_time_spent: int = 0  # Total time in seconds
    total_quizzes: int = 0
    subjects: Dict[str, SubjectPerformance] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=_get_utc_now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'student_id': self.student_id,
            'total_time_spent': self.total_time_spent,
            'total_quizzes': self.total_quizzes,
            'subjects': {subject: perf.to_dict() for subject, perf in self.subjects.items()},
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PerformanceSummary':
        """Create from dictionary"""
        subjects_data = data.get('subjects', {})
        subjects = {subject: SubjectPerformance.from_dict(perf_data) 
                   for subject, perf_data in subjects_data.items()}
        
        return cls(
            student_id=data['student_id'],
            total_time_spent=data.get('total_time_spent', 0),
            total_quizzes=data.get('total_quizzes', 0),
            subjects=subjects,
            last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else _get_utc_now()
        )


@dataclass
class SATPredictorSubmission:
    """
    Data submitted after SAT Predictor quiz is completed
    This represents a full 24-question SAT predictor test
    """
    student_id: str
    time_spent: int  # in seconds
    
    # Math section (12 questions)
    math_correct: int
    math_total: int  # Should always be 12
    math_questions: List[Dict[str, Any]]  # List of question details with tags, correctness
    
    # Reading & Writing section (12 questions)  
    rw_correct: int
    rw_total: int  # Should always be 12
    rw_questions: List[Dict[str, Any]]  # List of question details with tags, correctness
    
    timestamp: datetime = field(default_factory=_get_utc_now)
    session_id: Optional[str] = None  # Auto-generated unique ID
    
    def __post_init__(self):
        """Validate submission data"""
        # Validate question counts
        if self.math_total != 12:
            raise ValueError("Math section must have exactly 12 questions")
        if self.rw_total != 12:
            raise ValueError("Reading & Writing section must have exactly 12 questions")
        
        if self.math_correct > self.math_total:
            raise ValueError("Math correct answers cannot exceed total questions")
        if self.rw_correct > self.rw_total:
            raise ValueError("R&W correct answers cannot exceed total questions")
    
    def calculate_math_score(self) -> int:
        """
        Calculate SAT Math score (200-800) based on correct answers and difficulty
        
        Scoring system:
        - Difficulty 5: 65 points per correct answer
        - Difficulty 1: 15 points per correct answer
        - Linear interpolation for difficulties 2-4
        - Time bonus: Up to 40 points for completing under 15 minutes
        
        Formula: Base score from questions + time bonus, scaled to 200-800
        """
        base_score = 0
        
        # Calculate points from correct answers based on difficulty
        for q in self.math_questions:
            if q.get('is_correct', False):
                difficulty = q.get('difficulty_level', 3)
                # Linear interpolation: 15 points (diff 1) to 65 points (diff 5)
                points = 15 + ((difficulty - 1) / 4) * 50
                base_score += points
        
        total_score = 200 + base_score
        return min(800, total_score)
    
    def calculate_rw_score(self) -> int:
        """
        Calculate SAT Reading & Writing score (200-800) based on correct answers and difficulty
        
        Scoring system:
        - Difficulty 5: 65 points per correct answer
        - Difficulty 1: 15 points per correct answer
        - Linear interpolation for difficulties 2-4
        - Time bonus: Up to 40 points for completing under 15 minutes
        
        Formula: Base score from questions + time bonus, scaled to 200-800
        """
        base_score = 0
        
        # Calculate points from correct answers based on difficulty
        for q in self.rw_questions:
            if q.get('is_correct', False):
                difficulty = q.get('difficulty_level', 3)
                # Linear interpolation: 15 points (diff 1) to 65 points (diff 5)
                points = 15 + ((difficulty - 1) / 4) * 50
                base_score += points
        
        total_score = 200 + base_score
        return min(800, total_score)
    
    def _calculate_time_bonus(self) -> int:
        """
        Calculate time bonus based on how quickly the test was completed
        
        Rules:
        - Target time: 900 seconds (15 minutes)
        - For every 3 seconds saved: +1 point
        - Maximum bonus: 40 points
        
        Returns:
            Time bonus points (0-40)
        """
        target_time = 900  # 15 minutes
        max_bonus = 40
        
        if self.time_spent >= target_time:
            return 0
        
        time_saved = target_time - self.time_spent
        bonus = time_saved // 3  # Integer division: 1 point per 3 seconds
        
        return min(bonus, max_bonus)
    
    def calculate_total_sat_score(self) -> int:
        """Calculate total SAT score (400-1600)"""
        return self.calculate_math_score() + self.calculate_rw_score() + self._calculate_time_bonus()
    
    def get_math_accuracy(self) -> float:
        """Calculate math section accuracy percentage"""
        if self.math_total == 0:
            return 0.0
        return round((self.math_correct / self.math_total * 100), 2)
    
    def get_rw_accuracy(self) -> float:
        """Calculate R&W section accuracy percentage"""
        if self.rw_total == 0:
            return 0.0
        return round((self.rw_correct / self.rw_total * 100), 2)
    
    def get_subject_subcategory_stats(self) -> Dict[str, Dict[str, Dict[str, int]]]:
        """
        Calculate performance statistics by subject, subcategory, and tags
        Returns nested dict: {subject: {subcategory: {tag: {correct, total}}}}
        """
        stats = {}
        
        # Process math questions
        for q in self.math_questions:
            subject = q.get('subject', 'math')
            subcategory = q.get('sub_category', 'unknown')
            tags = q.get('tags', [])
            is_correct = q.get('is_correct', False)
            
            if subject not in stats:
                stats[subject] = {}
            if subcategory not in stats[subject]:
                stats[subject][subcategory] = {'total': 0, 'correct': 0, 'tags': {}}
            
            stats[subject][subcategory]['total'] += 1
            if is_correct:
                stats[subject][subcategory]['correct'] += 1
            
            # Track tag-level stats
            for tag in tags:
                if tag not in stats[subject][subcategory]['tags']:
                    stats[subject][subcategory]['tags'][tag] = {'total': 0, 'correct': 0}
                stats[subject][subcategory]['tags'][tag]['total'] += 1
                if is_correct:
                    stats[subject][subcategory]['tags'][tag]['correct'] += 1
        
        # Process R&W questions
        for q in self.rw_questions:
            subject = q.get('subject', 'reading-and-writing')
            subcategory = q.get('sub_category', 'unknown')
            tags = q.get('tags', [])
            is_correct = q.get('is_correct', False)
            
            if subject not in stats:
                stats[subject] = {}
            if subcategory not in stats[subject]:
                stats[subject][subcategory] = {'total': 0, 'correct': 0, 'tags': {}}
            
            stats[subject][subcategory]['total'] += 1
            if is_correct:
                stats[subject][subcategory]['correct'] += 1
            
            # Track tag-level stats
            for tag in tags:
                if tag not in stats[subject][subcategory]['tags']:
                    stats[subject][subcategory]['tags'][tag] = {'total': 0, 'correct': 0}
                stats[subject][subcategory]['tags'][tag]['total'] += 1
                if is_correct:
                    stats[subject][subcategory]['tags'][tag]['correct'] += 1
        
        return stats
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        time_bonus = self._calculate_time_bonus()
        
        return {
            'student_id': self.student_id,
            'time_spent': self.time_spent,
            'time_bonus_points': time_bonus,
            'math_correct': self.math_correct,
            'math_total': self.math_total,
            'math_score': self.calculate_math_score(),
            'math_accuracy': self.get_math_accuracy(),
            'rw_correct': self.rw_correct,
            'rw_total': self.rw_total,
            'rw_score': self.calculate_rw_score(),
            'rw_accuracy': self.get_rw_accuracy(),
            'total_sat_score': self.calculate_total_sat_score(),
            'math_questions': self.math_questions,
            'rw_questions': self.rw_questions,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'session_id': self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SATPredictorSubmission':
        """Create from dictionary"""
        return cls(
            student_id=data['student_id'],
            time_spent=data['time_spent'],
            math_correct=data['math_correct'],
            math_total=data['math_total'],
            math_questions=data['math_questions'],
            rw_correct=data['rw_correct'],
            rw_total=data['rw_total'],
            rw_questions=data['rw_questions'],
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else _get_utc_now(),
            session_id=data.get('session_id')
        )
