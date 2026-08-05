from datetime import datetime , timezone
from typing import List, Optional, Union
import time
from dataclasses import dataclass, field
from collections import defaultdict

from enum import Enum

def _get_utc_now():
	return datetime.now(timezone.utc)


def _parse_datetime(value: Union[str, datetime, None]) -> Optional[datetime]:
	"""Parse datetime from string or return datetime object as-is"""
	if value is None:
		return None
	if isinstance(value, datetime):
		if value.tzinfo is None:
			return value.replace(tzinfo=timezone.utc)
		return value
	if isinstance(value, str):
		try:
			return datetime.fromisoformat(value.replace('Z', '+00:00'))
		except ValueError:
			return None
	return None

class SubscriptionType(Enum):
	REGULAR = "regular"
	PRO = "pro"

class PlanType(Enum):
	NONE = "none"
	TRIAL = "trial"
	MONTHLY = "monthly"
	YEARLY = "yearly"

@dataclass
class PaymentDetail:
	order_id: str
	payment_id: str
	signature: str
	time: str

@dataclass
class SubscriptionInfo:
	type: SubscriptionType = SubscriptionType.REGULAR
	sessions_used: int = 0
	sessions_limit: int = 25  # Default limit for regular users
	session_credits: int = 0  # Credits for AI tutoring sessions
	last_reset_date: Optional[datetime] = None
	pro_expiry_date: Optional[datetime] = None
	plan_type: Optional[PlanType] = None
	payment_detail_list: List[PaymentDetail] = field(default_factory=list)
	taken_free_trial: bool = False
 
@dataclass
class PredictedScore:
	math_score: int = 0
	rw_score: int = 0
	is_synced: bool = False
	total_score: int = 0

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
	phone: Optional[str] = None
	country: Optional[str] = None
	state: Optional[str] = None
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
	
	# Subscription Info
	subscription: SubscriptionInfo = field(default_factory=SubscriptionInfo)
 
	# SAT predicted score
	predicted_score:  PredictedScore = field(default_factory=PredictedScore)

	
	# SAT Preparation Tracking
	completed_chapters: List[str] = field(default_factory=list)  # Track completed chapter IDs
	current_week_start: Optional[datetime] = None  # Track current week for task assignment
	completed_quiz_tags: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))
	completed_tutorial_tags: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))
	num_tasks : Optional[int] = 16
	predicted_score: Optional[int] = None  # Predicted SAT score from assessments

	# Task onboarding flags
	sat_score_test_given: bool = False

	# Task set rotation tracking
	math_subcategory_index: int = 0        # 0=Algebra, 1=Advanced Math, 2=Problem Solving, 3=Geometry
	english_subcategory_index: int = 0     # 0=Craft&Structure, 1=Expression, 2=Info&Ideas, 3=StdEnglish
	completed_task_sets: int = 0           # How many full task sets the user has finished

	# Free trial usage caps (one-time for the whole trial; SAT predictor uses sat_score_test_given)
	trial_quizzes_completed: int = 0
	trial_ai_tutorials_completed: int = 0
	trial_mock_completed: int = 0

	# Metadata
	created_at: datetime = field(default_factory=_get_utc_now)
	updated_at: datetime = field(default_factory=_get_utc_now)
	onboarding_completed: bool = False
	last_login: Optional[datetime] = None
	
	
	def to_dict(self) -> dict:
		"""Convert User object to dictionary for JSON """
		return {
			'id': self.id,
			'email': self.email,
			'name': self.name,
			'phone': self.phone,
			'country': self.country,
			'state': self.state,
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
			'subscription': {
				'type': self.subscription.type.value,
				'sessions_used': self.subscription.sessions_used,
				'sessions_limit': self.subscription.sessions_limit,
				'session_credits': self.subscription.session_credits if hasattr(self.subscription, 'session_credits') else 0,
				'last_reset_date': self.subscription.last_reset_date.isoformat() if self.subscription.last_reset_date else None,
				'pro_expiry_date': self.subscription.pro_expiry_date.isoformat() if self.subscription.pro_expiry_date else None,
				'plan_type': self.subscription.plan_type.value if self.subscription.plan_type else None,
				'taken_free_trial': self.subscription.taken_free_trial,
				'payment_detail_list': [
					{
						'order_id': pd.order_id,
						'payment_id': pd.payment_id,
						'signature': pd.signature,
						'time': pd.time
					} for pd in self.subscription.payment_detail_list
				]
			},
			'predicted_score': {
				'math_score': self.predicted_score.math_score,
				'rw_score': self.predicted_score.rw_score,
				'is_synced': self.predicted_score.is_synced,
				'total_score': self.predicted_score.total_score
			},
			'completed_chapters': self.completed_chapters,
			'completed_quiz_tags':dict(self.completed_quiz_tags),
			'completed_tutorial_tags': dict(self.completed_tutorial_tags),
			'num_tasks': self.num_tasks,
			'current_week_start': self.current_week_start.isoformat() if self.current_week_start else None,
			'sat_score_test_given': self.sat_score_test_given,
			'math_subcategory_index': self.math_subcategory_index,
			'english_subcategory_index': self.english_subcategory_index,
			'completed_task_sets': self.completed_task_sets,
			'trial_quizzes_completed': self.trial_quizzes_completed,
			'trial_ai_tutorials_completed': self.trial_ai_tutorials_completed,
			'trial_mock_completed': self.trial_mock_completed,
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
		
		# Handle missing or empty subscription data with defaults
		sub_data = data.get('subscription', {})
		if not sub_data:  # If subscription field doesn't exist or is empty
			subscription = SubscriptionInfo()  # Will use default values
		else:
			payment_details = [
				PaymentDetail(
					order_id=pd.get('order_id', ''),
					payment_id=pd.get('payment_id', ''),
					signature=pd.get('signature', ''),
					time=pd.get('time', '')
				) for pd in sub_data.get('payment_detail_list', [])
			]
			
			subscription = SubscriptionInfo(
				type=SubscriptionType(sub_data.get('type', 'regular')),
				sessions_used=sub_data.get('sessions_used', 0),
				sessions_limit=sub_data.get('sessions_limit', 25),
				session_credits=sub_data.get('session_credits', 0),
				last_reset_date=_parse_datetime(sub_data.get('last_reset_date')),
				pro_expiry_date=_parse_datetime(sub_data.get('pro_expiry_date')),
				plan_type=PlanType(sub_data['plan_type']) if sub_data.get('plan_type') else None,
				taken_free_trial=sub_data.get('taken_free_trial', False),
				payment_detail_list=payment_details
			)

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
		
		# Handle predicted score
		predicted_score_data = data.get('predicted_score', {})
		predicted_score = PredictedScore(
			math_score=predicted_score_data.get('math_score', 0),
			rw_score=predicted_score_data.get('rw_score', 0),
			is_synced=predicted_score_data.get('is_synced', False),
			total_score=predicted_score_data.get('total_score', 0)
		)
		
		return cls(
			id=data['id'],
			email=data['email'],
			name=data['name'],
			phone=data.get('phone'),
			country=data.get('country'),
			state=data.get('state'),
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
			subscription = subscription,
			predicted_score=predicted_score,
			completed_chapters=data.get('completed_chapters', []),
			current_week_start=_parse_datetime(data.get('current_week_start')),
			sat_score_test_given=data.get('sat_score_test_given', False),
			math_subcategory_index=data.get('math_subcategory_index', 0),
			english_subcategory_index=data.get('english_subcategory_index', 0),
			completed_task_sets=data.get('completed_task_sets', 0),
			trial_quizzes_completed=data.get('trial_quizzes_completed', 0),
			trial_ai_tutorials_completed=data.get('trial_ai_tutorials_completed', 0),
			trial_mock_completed=data.get('trial_mock_completed', 0),
			completed_quiz_tags=defaultdict(int, data.get('completed_quiz_tags', {})),
			completed_tutorial_tags=defaultdict(int, data.get('completed_tutorial_tags', {})),
			num_tasks=data.get('num_tasks', 16),
			created_at=_parse_datetime(data.get('created_at')) or datetime.now(timezone.utc),
			updated_at=_parse_datetime(data.get('updated_at')) or datetime.now(timezone.utc),
			onboarding_completed=data.get('onboarding_completed', False),
			last_login=_parse_datetime(data.get('last_login'))
		)
	
	def complete_onboarding(self):
		"""Mark onboarding as completed"""
		self.onboarding_completed = True
		self.updated_at = datetime.now(timezone.utc)
	
	def update_last_login(self):
		"""Update last login timestamp"""
		self.last_login = datetime.now(timezone.utc)
		self.updated_at = datetime.now(timezone.utc)
	def can_start_session(self) -> bool:
		"""Check if user can start a new tutoring session based on session credits"""
		return self.subscription.session_credits > 0

	def decrement_session_credits(self):
		"""Decrement session credits by 1 when starting a new session"""
		if self.subscription.session_credits > 0:
			self.subscription.session_credits -= 1
			self.updated_at = datetime.now(timezone.utc)

	def add_session_credits(self, credits: int):
		"""Add session credits to the user's account"""
		self.subscription.session_credits += credits
		self.updated_at = datetime.now(timezone.utc)

	def increment_session_count(self):
		"""Increment the sessions used count (legacy method for tracking)"""
		if self.subscription.type == SubscriptionType.REGULAR:
			self.subscription.sessions_used += 1
			self.updated_at = datetime.now(timezone.utc)
	
	def mark_chapter_completed(self, chapter_id: str):
		"""Mark a chapter as completed"""
		if chapter_id not in self.completed_chapters:
			self.completed_chapters.append(chapter_id)
			self.updated_at = datetime.now(timezone.utc)
	
	def get_next_chapter(self, already_selected_chapters=None) -> Optional[str]:
		"""Get the next chapter ID that hasn't been completed"""
		# This will be used to assign the next AI tutorial task
		all_chapters = ["Chapter 1", "Chapter 2", "Chapter 3", "Chapter 4", "Chapter 5", "Chapter 6", "Chapter 7"]
		for chapter_id in all_chapters:
			if chapter_id not in self.completed_chapters and (already_selected_chapters is None or chapter_id not in already_selected_chapters):
				return chapter_id
		return None  # All chapters completed
	def mark_quiz_tag(self, tag: str):
		"""Mark a tag as completed"""
		self.completed_quiz_tags[tag] += 1
		self.updated_at = datetime.now(timezone.utc)

	def mark_tutorial_tag(self, tag: str):
		"""Mark a tag as completed"""
		self.completed_tutorial_tags[tag] +=1
		self.updated_at = datetime.now(timezone.utc)

	def mark_quiz_from_set(self, tags: set):
		"""Mark a set of tags as completed"""
		for tag in tags:
			self.mark_quiz_tag(tag)
