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
    TagDetail,
    SATPredictorSubmission
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
            
            # 4. Update last 15 math questions if this is a math quiz
            if submission.subject.lower() == 'math':
                last_15_success = self._update_last_15_math_questions(analytics_ref, submission)
                if not last_15_success:
                    logger.warning(f"Failed to update last 15 math questions for student {student_id}")
                    # Don't fail the entire operation for this
            
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
    
    def _update_last_15_math_questions(self, analytics_ref, submission: QuizSubmission) -> bool:
        """
        Update the last 15 math questions attempted by the user
        Stores full question data including question_text and options
        
        This document stores:
        - question_id
        - question_text
        - options (A, B, C, D)
        - correct_answer
        - is_answered_correctly (boolean)
        - difficulty_level
        - tags (list of tags for this question)
        - timestamp
        - sub_category
        
        Args:
            analytics_ref: Reference to analytics subcollection
            submission: QuizSubmission object with quiz results
            
        Returns:
            bool: Success status
        """
        try:
            from database.firebase_client import get_question_db_client
            
            last_15_ref = analytics_ref.document('last_15_math_questions')
            
            # Get existing document or create new one
            last_15_doc = last_15_ref.get()
            
            if last_15_doc.exists:
                last_15_data = last_15_doc.to_dict()
                questions_list = last_15_data.get('questions', [])
            else:
                last_15_data = {
                    'student_id': submission.student_id,
                    'questions': []
                }
                questions_list = []
            
            # Create new question entries from the submission
            # Fetch full question data from question bank using collection group query
            question_db = get_question_db_client()
            new_questions = []
            
            # Build a mapping of tag to questions from tag_wise_details
            # Since we don't have individual question-tag mapping in submission,
            # we'll store all tags for this quiz with each question
            all_tags = [tag_detail.tag for tag_detail in submission.tag_wise_details]
            
            # Helper function to fetch question by document ID using the correct path
            def fetch_question_data(question_id: str) -> Optional[Dict[str, Any]]:
                """
                Fetch question data using the correct Firestore path.
                Path: /question_bank/{subject}|{sub_category}/difficulty_levels/{level}/questions/{question_id}
                """
                try:
                    # Construct the correct path using submission data
                    subject_subcategory = f"{submission.subject}|{submission.sub_category}"
                    difficulty_level = str(submission.difficulty_level)
                    
                    # Build the path to the specific question document
                    question_ref = (question_db
                                   .collection('question_bank')
                                   .document(subject_subcategory)
                                   .collection('difficulty_levels')
                                   .document(difficulty_level)
                                   .collection('questions')
                                   .document(question_id))
                    
                    # Fetch the document
                    question_doc = question_ref.get()
                    
                    if question_doc.exists:
                        data = question_doc.to_dict()
                        if data:
                            data['id'] = question_doc.id
                            logger.info(f"Found question {question_id} at path {subject_subcategory}/difficulty_levels/{difficulty_level}")
                            return data
                    
                    logger.warning(f"Question {question_id} not found at path {subject_subcategory}/difficulty_levels/{difficulty_level}")
                    return None
                except Exception as e:
                    logger.error(f"Error fetching question {question_id}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return None
            
            # Process correct questions
            for question_id in submission.correct_question_ids:
                # Fetch full question data
                question_data = fetch_question_data(question_id)
                
                if question_data:
                    # Options are stored as an array with 4 values
                    options = question_data.get('options', ['', '', '', ''])
                    
                    question_entry = {
                        'question_id': question_id,
                        'question_text': question_data.get('question_text', ''),
                        'option_a': options[0] if len(options) > 0 else '',
                        'option_b': options[1] if len(options) > 1 else '',
                        'option_c': options[2] if len(options) > 2 else '',
                        'option_d': options[3] if len(options) > 3 else '',
                        'correct_answer': question_data.get('correct_answer', ''),
                        'is_answered_correctly': True,
                        'difficulty_level': submission.difficulty_level,
                        'tags': all_tags,
                        'sub_category': submission.sub_category,
                        'timestamp': submission.timestamp.isoformat() if submission.timestamp else datetime.now(timezone.utc).isoformat()
                    }
                    new_questions.append(question_entry)
                else:
                    # If question not found, store basic info
                    logger.warning(f"Question {question_id} not found in database, storing basic info")
                    question_entry = {
                        'question_id': question_id,
                        'question_text': '',
                        'option_a': '',
                        'option_b': '',
                        'option_c': '',
                        'option_d': '',
                        'correct_answer': '',
                        'is_answered_correctly': True,
                        'difficulty_level': submission.difficulty_level,
                        'tags': all_tags,
                        'sub_category': submission.sub_category,
                        'timestamp': submission.timestamp.isoformat() if submission.timestamp else datetime.now(timezone.utc).isoformat()
                    }
                    new_questions.append(question_entry)
            
            # Process incorrect questions
            for question_id in submission.incorrect_question_ids:
                # Fetch full question data
                question_data = fetch_question_data(question_id)
                
                if question_data:
                    # Options are stored as an array with 4 values
                    options = question_data.get('options', ['', '', '', ''])
                    
                    question_entry = {
                        'question_id': question_id,
                        'question_text': question_data.get('question_text', ''),
                        'option_a': options[0] if len(options) > 0 else '',
                        'option_b': options[1] if len(options) > 1 else '',
                        'option_c': options[2] if len(options) > 2 else '',
                        'option_d': options[3] if len(options) > 3 else '',
                        'correct_answer': question_data.get('correct_answer', ''),
                        'is_answered_correctly': False,
                        'difficulty_level': submission.difficulty_level,
                        'tags': all_tags,
                        'sub_category': submission.sub_category,
                        'timestamp': submission.timestamp.isoformat() if submission.timestamp else datetime.now(timezone.utc).isoformat()
                    }
                    new_questions.append(question_entry)
                else:
                    # If question not found, store basic info
                    logger.warning(f"Question {question_id} not found in database, storing basic info")
                    question_entry = {
                        'question_id': question_id,
                        'question_text': '',
                        'option_a': '',
                        'option_b': '',
                        'option_c': '',
                        'option_d': '',
                        'correct_answer': '',
                        'is_answered_correctly': False,
                        'difficulty_level': submission.difficulty_level,
                        'tags': all_tags,
                        'sub_category': submission.sub_category,
                        'timestamp': submission.timestamp.isoformat() if submission.timestamp else datetime.now(timezone.utc).isoformat()
                    }
                    new_questions.append(question_entry)
            
            # Add new questions to the front of the list (most recent first)
            questions_list = new_questions + questions_list
            
            # Keep only the last 15 questions
            questions_list = questions_list[:15]
            
            # Update the document
            last_15_data['questions'] = questions_list
            last_15_data['last_updated'] = datetime.now(timezone.utc).isoformat()
            
            last_15_ref.set(last_15_data)
            
            logger.info(f"Updated last 15 math questions for student {submission.student_id}, now tracking {len(questions_list)} questions")
            return True
            
        except Exception as e:
            logger.error(f"Error updating last 15 math questions: {str(e)}")
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
    
    def get_last_15_math_questions(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the last 15 math questions attempted by a student
        
        Args:
            student_id: The student's user ID
            
        Returns:
            Dictionary with last 15 math questions data or None if not found
            Format:
            {
                'student_id': 'user123',
                'questions': [
                    {
                        'question_id': 'q123',
                        'is_correct': True,
                        'difficulty_level': 3,
                        'tags': ['linear-equations', 'algebra'],
                        'sub_category': 'algebra',
                        'timestamp': '2025-11-07T...'
                    },
                    ...
                ],
                'last_updated': '2025-11-07T...'
            }
        """
        try:
            if not self._check_connection():
                return None
            
            last_15_ref = (self.db.collection('users')
                          .document(student_id)
                          .collection('analytics')
                          .document('last_15_math_questions'))
            
            last_15_doc = last_15_ref.get()
            
            if last_15_doc.exists:
                return last_15_doc.to_dict()
            
            logger.info(f"No last 15 math questions found for student {student_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting last 15 math questions for {student_id}: {str(e)}")
            return False


    def submit_sat_predictor(self, submission: SATPredictorSubmission) -> tuple[bool, Optional[str]]:
        """
        Process and store SAT predictor quiz submission
        
        This function:
        1. Stores the test performance in sat_predictor_performance subcollection
        2. Updates analytics (performance_summary, activity_logs, correct/incorrect questions)
        
        Args:
            submission: SATPredictorSubmission object with test results
            
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
            
            # 1. Store SAT predictor performance
            sat_perf_success = self._store_sat_predictor_performance(student_id, submission)
            if not sat_perf_success:
                logger.error(f"Failed to store SAT predictor performance for student {student_id}")
                return False, None
            
            # 2. Update analytics (same as regular quiz submission)
            analytics_success = self._update_analytics_from_sat_predictor(student_id, submission)
            if not analytics_success:
                logger.error(f"Failed to update analytics from SAT predictor for student {student_id}")
                return False, None
            
            logger.info(f"Successfully processed SAT predictor for student {student_id}, session {submission.session_id}")
            return True, submission.session_id
            
        except Exception as e:
            logger.error(f"Error submitting SAT predictor: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, None
    
    def _store_sat_predictor_performance(self, student_id: str, submission: SATPredictorSubmission) -> bool:
        """
        Store SAT predictor test performance in sat_predictor_performance subcollection
        """
        try:
            # Reference to sat_predictor_performance subcollection
            sat_perf_ref = (self.db.collection('users')
                           .document(student_id)
                           .collection('sat_predictor_performance'))
            
            # Create document with session_id as document ID
            doc_ref = sat_perf_ref.document(submission.session_id)
            
            # Store the submission
            doc_ref.set(submission.to_dict())
            
            logger.info(f"Stored SAT predictor performance for student {student_id}, session {submission.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing SAT predictor performance: {str(e)}")
            return False
    
    def _update_analytics_from_sat_predictor(self, student_id: str, submission: SATPredictorSubmission) -> bool:
        """
        Update analytics collections from SAT predictor submission
        Similar to regular quiz submission but processes all questions
        """
        try:
            analytics_ref = self.db.collection('users').document(student_id).collection('analytics')
            
            # Get subject/subcategory stats from submission
            stats = submission.get_subject_subcategory_stats()
            
            # Process each subject's data
            for subject, subcategories in stats.items():
                for subcategory, sub_data in subcategories.items():
                    # Create a QuizSubmission-like object for each subcategory
                    # This allows reuse of existing analytics update logic
                    
                    # Collect tag details
                    tag_wise_details = []
                    for tag_name, tag_data in sub_data['tags'].items():
                        tag_detail = TagDetail(
                            tag=tag_name,
                            total_questions=tag_data['total'],
                            correct_answers=tag_data['correct'],
                            score=tag_data['correct'] * 3,  # Use difficulty 3 as average
                            total_possible_score=tag_data['total'] * 3
                        )
                        tag_wise_details.append(tag_detail)
                    
                    # Collect correct and incorrect question IDs for this subcategory
                    correct_ids = []
                    incorrect_ids = []
                    
                    # Get questions for this subject
                    questions_list = submission.math_questions if subject == 'math' else submission.rw_questions
                    for q in questions_list:
                        if q.get('sub_category') == subcategory:
                            q_id = q.get('id') or q.get('question_id', '')
                            if q.get('is_correct', False):
                                correct_ids.append(q_id)
                            else:
                                incorrect_ids.append(q_id)
                    
                    # Create QuizSubmission object for this subcategory
                    quiz_sub = QuizSubmission(
                        student_id=student_id,
                        time_spent=submission.time_spent // len(stats),  # Distribute time
                        number_of_questions=sub_data['total'],
                        number_of_correct_answers=sub_data['correct'],
                        subject=subject,
                        sub_category=subcategory,
                        difficulty_level=3,  # Use middle difficulty
                        tag_wise_details=tag_wise_details,
                        correct_question_ids=correct_ids,
                        incorrect_question_ids=incorrect_ids,
                        timestamp=submission.timestamp,
                        session_id=f"{submission.session_id}_{subject}_{subcategory}"
                    )
                    
                    # Store activity log
                    self._store_activity_log(student_id, quiz_sub)
                    
                    # Update performance summary
                    self._update_performance_summary(analytics_ref, quiz_sub)
                    
                    # Update question lists
                    self._update_question_lists(analytics_ref, quiz_sub)
                    
                    # Update last 15 math if applicable
                    if subject.lower() == 'math':
                        self._update_last_15_math_questions(analytics_ref, quiz_sub)
            
            logger.info(f"Successfully updated analytics from SAT predictor for student {student_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating analytics from SAT predictor: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


# Singleton instance
_analytics_db_instance = None


def get_analytics_db() -> AnalyticsDatabase:
    """Get singleton instance of AnalyticsDatabase"""
    global _analytics_db_instance
    if _analytics_db_instance is None:
        _analytics_db_instance = AnalyticsDatabase()
    return _analytics_db_instance
