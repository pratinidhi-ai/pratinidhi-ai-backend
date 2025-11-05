"""
Analytics Database Operations
Handles all analytics-related database interactions including:
- Storing quiz submissions
- Aggregating performance data
- Managing analytics subcollections
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
import uuid
import pytz

from database.firebase_client import get_firestore_client
from models.analytics_schema import (
    QuizSubmission, 
    PerformanceSummary,
    SubjectPerformance,
    SubCategoryPerformance,
    TagPerformance,
    TagDetail
)

logger = logging.getLogger(__name__)

# Indian Standard Time timezone
IST = pytz.timezone('Asia/Kolkata')


class AnalyticsDatabase:
    """Database operations for analytics management"""
    
    def __init__(self):
        self.db = get_firestore_client()
    
    def _check_connection(self) -> bool:
        """Check if database connection is available"""
        if self.db is None:
            logger.error("Firestore client is not initialized")
            return False
        return True
    
    def submit_quiz_analytics(self, submission: QuizSubmission) -> tuple[bool, Optional[str]]:
        """
        Process and store quiz submission analytics
        
        This function:
        1. Stores the raw quiz submission in activity_logs
        2. Updates performance_summary with aggregated data
        3. Updates correct_questions and incorrect_questions documents
        
        Args:
            submission: QuizSubmission object with quiz results
            
        Returns:
            tuple: (success: bool, session_id: str or None)
        """
        try:
            if not self._check_connection():
                return False, None
            
            # Generate unique session ID if not provided
            if not submission.session_id:
                submission.session_id = str(uuid.uuid4())
            
            student_id = submission.student_id
            
            # Reference to user's analytics subcollection
            analytics_ref = self.db.collection('users').document(student_id).collection('analytics')
            
            # 1. Store activity log
            activity_log_success = self._store_activity_log(student_id, submission)
            if not activity_log_success:
                logger.error(f"Failed to store activity log for student {student_id}")
                return False, None
            
            # 2. Update performance summary
            summary_success = self._update_performance_summary(analytics_ref, submission)
            if not summary_success:
                logger.error(f"Failed to update performance summary for student {student_id}")
                return False, None
            
            # 3. Update correct and incorrect questions
            questions_success = self._update_question_lists(analytics_ref, submission)
            if not questions_success:
                logger.error(f"Failed to update question lists for student {student_id}")
                return False, None
            
            logger.info(f"Successfully processed quiz analytics for student {student_id}, session {submission.session_id}")
            return True, submission.session_id
            
        except Exception as e:
            logger.error(f"Error submitting quiz analytics: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, None
    
    def _store_activity_log(self, student_id: str, submission: QuizSubmission) -> bool:
        """
        Store the quiz submission in activity_logs subcollection
        Each submission is stored as a document with timestamp-based ID
        """
        try:
            # Reference to activity_logs subcollection
            activity_logs_ref = (self.db.collection('users')
                                .document(student_id)
                                .collection('activity_logs'))
            
            # Create document with session_id as document ID
            doc_ref = activity_logs_ref.document(submission.session_id)
            
            # Store the submission
            doc_ref.set(submission.to_dict())
            
            logger.info(f"Stored activity log for student {student_id}, session {submission.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing activity log: {str(e)}")
            return False
    
    def _update_performance_summary(self, analytics_ref, submission: QuizSubmission) -> bool:
        """
        Update the performance_summary document with aggregated data
        This maintains hierarchical stats: Subject -> SubCategory -> Tag
        """
        try:
            summary_ref = analytics_ref.document('performance_summary')
            
            # Get existing summary or create new one
            summary_doc = summary_ref.get()
            
            if summary_doc.exists:
                summary_data = summary_doc.to_dict()
                summary = PerformanceSummary.from_dict(summary_data)
            else:
                summary = PerformanceSummary(student_id=submission.student_id)
            
            # Update overall stats
            summary.total_time_spent += submission.time_spent
            summary.total_quizzes += 1
            summary.last_updated = datetime.now(timezone.utc)
            
            # Get or create subject performance
            subject = submission.subject
            if subject not in summary.subjects:
                summary.subjects[subject] = SubjectPerformance(subject=subject)
            
            subject_perf = summary.subjects[subject]
            
            # Update subject-level stats
            subject_perf.total_questions_attempted += submission.number_of_questions
            subject_perf.total_correct_answers += submission.number_of_correct_answers
            subject_perf.total_score += submission.calculate_score()
            subject_perf.total_possible_score += submission.calculate_total_possible_score()
            subject_perf.total_time_spent += submission.time_spent
            subject_perf.quiz_count += 1
            subject_perf.last_updated = datetime.now(timezone.utc)
            
            # Get or create sub_category performance
            sub_category = submission.sub_category
            if sub_category not in subject_perf.sub_categories:
                subject_perf.sub_categories[sub_category] = SubCategoryPerformance(sub_category=sub_category)
            
            sub_cat_perf = subject_perf.sub_categories[sub_category]
            
            # Update sub_category-level stats
            sub_cat_perf.total_questions_attempted += submission.number_of_questions
            sub_cat_perf.total_correct_answers += submission.number_of_correct_answers
            sub_cat_perf.total_score += submission.calculate_score()
            sub_cat_perf.total_possible_score += submission.calculate_total_possible_score()
            sub_cat_perf.total_time_spent += submission.time_spent
            sub_cat_perf.quiz_count += 1
            sub_cat_perf.last_updated = datetime.now(timezone.utc)
            
            # Update tag-level stats
            for tag_detail in submission.tag_wise_details:
                tag_name = tag_detail.tag
                
                if tag_name not in sub_cat_perf.tags:
                    sub_cat_perf.tags[tag_name] = TagPerformance(tag=tag_name)
                
                tag_perf = sub_cat_perf.tags[tag_name]
                tag_perf.total_questions_attempted += tag_detail.total_questions
                tag_perf.total_correct_answers += tag_detail.correct_answers
                tag_perf.total_score += tag_detail.score
                tag_perf.total_possible_score += tag_detail.total_possible_score
            
            # Save updated summary
            summary_ref.set(summary.to_dict())
            
            logger.info(f"Updated performance summary for student {submission.student_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating performance summary: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _update_question_lists(self, analytics_ref, submission: QuizSubmission) -> bool:
        """
        Update correct_questions and incorrect_questions documents
        Store question IDs organized by subject|sub_category
        """
        try:
            # Create document key for this subject|sub_category combination
            doc_key = f"{submission.subject}|{submission.sub_category}"
            
            # Update correct_questions
            if submission.correct_question_ids:
                correct_ref = analytics_ref.document('correct_questions')
                correct_doc = correct_ref.get()
                
                if correct_doc.exists:
                    correct_data = correct_doc.to_dict()
                else:
                    correct_data = {'student_id': submission.student_id}
                
                # Get existing list or create new one
                if doc_key not in correct_data:
                    correct_data[doc_key] = []
                
                # Add new correct question IDs (avoiding duplicates)
                existing_ids = set(correct_data[doc_key])
                new_ids = set(submission.correct_question_ids)
                correct_data[doc_key] = list(existing_ids.union(new_ids))
                
                # Update last_updated
                correct_data['last_updated'] = datetime.now(timezone.utc).isoformat()
                
                correct_ref.set(correct_data)
            
            # Update incorrect_questions
            if submission.incorrect_question_ids:
                incorrect_ref = analytics_ref.document('incorrect_questions')
                incorrect_doc = incorrect_ref.get()
                
                if incorrect_doc.exists:
                    incorrect_data = incorrect_doc.to_dict()
                else:
                    incorrect_data = {'student_id': submission.student_id}
                
                # Get existing list or create new one
                if doc_key not in incorrect_data:
                    incorrect_data[doc_key] = []
                
                # Add new incorrect question IDs (avoiding duplicates)
                existing_ids = set(incorrect_data[doc_key])
                new_ids = set(submission.incorrect_question_ids)
                incorrect_data[doc_key] = list(existing_ids.union(new_ids))
                
                # Update last_updated
                incorrect_data['last_updated'] = datetime.now(timezone.utc).isoformat()
                
                incorrect_ref.set(incorrect_data)
            
            logger.info(f"Updated question lists for student {submission.student_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating question lists: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_performance_summary(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the performance summary for a student
        
        Args:
            student_id: The student's user ID
            
        Returns:
            Dictionary with performance data or None if not found
        """
        try:
            if not self._check_connection():
                return None
            
            summary_ref = (self.db.collection('users')
                          .document(student_id)
                          .collection('analytics')
                          .document('performance_summary'))
            
            summary_doc = summary_ref.get()
            
            if summary_doc.exists:
                return summary_doc.to_dict()
            
            logger.info(f"No performance summary found for student {student_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting performance summary for {student_id}: {str(e)}")
            return None
    
    def get_activity_logs(self, student_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get activity logs for a student
        
        Args:
            student_id: The student's user ID
            limit: Maximum number of logs to return (default 50)
            
        Returns:
            List of activity log dictionaries, sorted by timestamp (newest first)
        """
        try:
            if not self._check_connection():
                return []
            
            logs_ref = (self.db.collection('users')
                       .document(student_id)
                       .collection('activity_logs')
                       .order_by('timestamp', direction='DESCENDING')
                       .limit(limit))
            
            docs = logs_ref.stream()
            
            logs = []
            for doc in docs:
                log_data = doc.to_dict()
                log_data['id'] = doc.id
                logs.append(log_data)
            
            logger.info(f"Retrieved {len(logs)} activity logs for student {student_id}")
            return logs
            
        except Exception as e:
            logger.error(f"Error getting activity logs for {student_id}: {str(e)}")
            return []
    
    def get_correct_questions(self, student_id: str, subject: Optional[str] = None, 
                            sub_category: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get correct question IDs for a student
        
        Args:
            student_id: The student's user ID
            subject: Optional filter by subject
            sub_category: Optional filter by sub_category (requires subject)
            
        Returns:
            Dictionary mapping subject|sub_category to list of question IDs
        """
        try:
            if not self._check_connection():
                return {}
            
            correct_ref = (self.db.collection('users')
                          .document(student_id)
                          .collection('analytics')
                          .document('correct_questions'))
            
            correct_doc = correct_ref.get()
            
            if not correct_doc.exists:
                return {}
            
            correct_data = correct_doc.to_dict()
            
            # Remove metadata fields
            correct_data.pop('student_id', None)
            correct_data.pop('last_updated', None)
            
            # Filter if requested
            if subject and sub_category:
                key = f"{subject}|{sub_category}"
                return {key: correct_data.get(key, [])}
            elif subject:
                return {k: v for k, v in correct_data.items() if k.startswith(f"{subject}|")}
            
            return correct_data
            
        except Exception as e:
            logger.error(f"Error getting correct questions for {student_id}: {str(e)}")
            return {}
    
    def get_incorrect_questions(self, student_id: str, subject: Optional[str] = None,
                               sub_category: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get incorrect question IDs for a student
        
        Args:
            student_id: The student's user ID
            subject: Optional filter by subject
            sub_category: Optional filter by sub_category (requires subject)
            
        Returns:
            Dictionary mapping subject|sub_category to list of question IDs
        """
        try:
            if not self._check_connection():
                return {}
            
            incorrect_ref = (self.db.collection('users')
                            .document(student_id)
                            .collection('analytics')
                            .document('incorrect_questions'))
            
            incorrect_doc = incorrect_ref.get()
            
            if not incorrect_doc.exists:
                return {}
            
            incorrect_data = incorrect_doc.to_dict()
            
            # Remove metadata fields
            incorrect_data.pop('student_id', None)
            incorrect_data.pop('last_updated', None)
            
            # Filter if requested
            if subject and sub_category:
                key = f"{subject}|{sub_category}"
                return {key: incorrect_data.get(key, [])}
            elif subject:
                return {k: v for k, v in incorrect_data.items() if k.startswith(f"{subject}|")}
            
            return incorrect_data
            
        except Exception as e:
            logger.error(f"Error getting incorrect questions for {student_id}: {str(e)}")
            return {}
    
    def update_daily_progress(self, student_id: str, submission: QuizSubmission) -> bool:
        """
        Update daily progress statistics for a student
        Tracks today's and yesterday's stats with IST timezone
        
        Daily Progress includes:
        1. Quizzing Time Today
        2. Number of Quizzes Taken Today
        3. Accuracy Today
        4. Hot Topic Today (most attempted tag)
        5. Streak (consecutive days of activity)
        
        Args:
            student_id: The student's user ID
            submission: QuizSubmission object with quiz results
            
        Returns:
            bool: Success status
        """
        try:
            if not self._check_connection():
                return False
            
            # Get current IST date
            now_ist = datetime.now(IST)
            today_date = now_ist.date().isoformat()  # YYYY-MM-DD format
            
            # Reference to daily_progress document
            daily_progress_ref = (self.db.collection('users')
                                 .document(student_id)
                                 .collection('analytics')
                                 .document('daily_progress'))
            
            # Get existing daily progress or create new one
            progress_doc = daily_progress_ref.get()
            
            if progress_doc.exists:
                progress_data = progress_doc.to_dict()
            else:
                progress_data = {
                    'student_id': student_id,
                    'today': {},
                    'yesterday': {},
                    'streak': 0,
                    'last_activity_date': None
                }
            
            # Check if we need to roll over to a new day
            last_activity_date = progress_data.get('last_activity_date')
            
            if last_activity_date and last_activity_date != today_date:
                # Check if it's a new day
                yesterday_ist = (now_ist - timedelta(days=1)).date().isoformat()
                
                if last_activity_date == yesterday_ist:
                    # Consecutive day - increment streak
                    progress_data['streak'] = progress_data.get('streak', 0) + 1
                    # Move today's data to yesterday
                    progress_data['yesterday'] = progress_data.get('today', {})
                else:
                    # Gap in activity - reset streak to 1
                    progress_data['streak'] = 1
                    # Clear yesterday's data
                    progress_data['yesterday'] = {}
                
                # Reset today's data for new day
                progress_data['today'] = {}
            elif not last_activity_date:
                # First time activity
                progress_data['streak'] = 1
            
            # Initialize today's data if empty
            if not progress_data.get('today'):
                progress_data['today'] = {
                    'date': today_date,
                    'total_time_spent': 0,
                    'total_quizzes': 0,
                    'total_questions': 0,
                    'total_correct': 0,
                    'tags': {}  # tag -> count mapping
                }
            
            # Update today's stats
            today_stats = progress_data['today']
            today_stats['total_time_spent'] += submission.time_spent
            today_stats['total_quizzes'] += 1
            today_stats['total_questions'] += submission.number_of_questions
            today_stats['total_correct'] += submission.number_of_correct_answers
            
            # Update tag counts to determine hot topic
            for tag_detail in submission.tag_wise_details:
                tag_name = tag_detail.tag
                if tag_name not in today_stats['tags']:
                    today_stats['tags'][tag_name] = 0
                today_stats['tags'][tag_name] += tag_detail.total_questions
            
            # Calculate accuracy
            if today_stats['total_questions'] > 0:
                today_stats['accuracy'] = round(
                    (today_stats['total_correct'] / today_stats['total_questions']) * 100, 2
                )
            else:
                today_stats['accuracy'] = 0
            
            # Determine hot topic (most attempted tag)
            if today_stats['tags']:
                hot_topic = max(today_stats['tags'].items(), key=lambda x: x[1])
                today_stats['hot_topic'] = hot_topic[0]
                today_stats['hot_topic_count'] = hot_topic[1]
            else:
                today_stats['hot_topic'] = None
                today_stats['hot_topic_count'] = 0
            
            # Update last activity date
            progress_data['last_activity_date'] = today_date
            progress_data['last_updated'] = datetime.now(timezone.utc).isoformat()
            
            # Save updated daily progress
            daily_progress_ref.set(progress_data)
            
            logger.info(f"Updated daily progress for student {student_id} on {today_date}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating daily progress for {student_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_daily_progress(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Get daily progress statistics for a student
        
        Args:
            student_id: The student's user ID
            
        Returns:
            Dictionary with daily progress data or None if not found
        """
        try:
            if not self._check_connection():
                return None
            
            daily_progress_ref = (self.db.collection('users')
                                 .document(student_id)
                                 .collection('analytics')
                                 .document('daily_progress'))
            
            progress_doc = daily_progress_ref.get()
            
            if progress_doc.exists:
                progress_data = progress_doc.to_dict()
                
                # Ensure today's date is current (IST)
                now_ist = datetime.now(IST)
                today_date = now_ist.date().isoformat()
                
                last_activity_date = progress_data.get('last_activity_date')
                
                # If last activity was not today, return empty today stats
                if last_activity_date != today_date:
                    progress_data['today'] = {
                        'date': today_date,
                        'total_time_spent': 0,
                        'total_quizzes': 0,
                        'total_questions': 0,
                        'total_correct': 0,
                        'accuracy': 0,
                        'hot_topic': None,
                        'hot_topic_count': 0,
                        'tags': {}
                    }
                    
                    # Check if streak should be reset
                    yesterday_ist = (now_ist - timedelta(days=1)).date().isoformat()
                    if last_activity_date != yesterday_ist:
                        progress_data['streak'] = 0
                
                return progress_data
            
            logger.info(f"No daily progress found for student {student_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting daily progress for {student_id}: {str(e)}")
            return None


# Singleton instance
_analytics_db_instance = None


def get_analytics_db() -> AnalyticsDatabase:
    """Get singleton instance of AnalyticsDatabase"""
    global _analytics_db_instance
    if _analytics_db_instance is None:
        _analytics_db_instance = AnalyticsDatabase()
    return _analytics_db_instance
