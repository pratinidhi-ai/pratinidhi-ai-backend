"""
Task System Testing Script
Tests task creation, assignment, and management locally
"""

import sys
import os

# Setup mock database before importing other modules
from testing.mock_database import setup_mock_database, load_test_data
mock_client = setup_mock_database()
load_test_data(mock_client)
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.users_schema import User, Grade, Board, Language
from models.task_schema import Task, TaskType, Subject
from helper.task_assignment import (
    assign_weekly_tasks,
    should_assign_new_tasks,
    get_week_start,
    get_days_left_in_week,
    calculate_task_priority
)
from helper.task_service import (
    TaskService,
    initialize_user_tasks,
    fetch_current_task_for_user,
    get_user_dashboard_data
)

class TaskTester:
    """Test harness for task system"""
    
    def __init__(self):
        self.test_users = []
        self.created_tasks = []
        self.firestore_client = None  # For local testing without Firebase
        
    def create_test_user(self, user_id: str = "test_user_001", 
                        completed_chapters: Optional[List[str]] = None) -> User:
        """Create a test user for task assignment testing"""
        
        if completed_chapters is None:
            completed_chapters = []
            
        user = User(
            id=user_id,
            email=f"{user_id}@test.com",
            name=f"Test User {user_id[-3:]}",
            grade=Grade.GRADE_11,
            board=Board.CBSE,
            city="Test City",
            timezone="UTC",
            school="Test School",
            completed_chapters=completed_chapters,
            onboarding_completed=True
        )
        
        self.test_users.append(user)
        print(f"✅ Created test user: {user.name} (ID: {user.id})")
        print(f"   - Email: {user.email}")
        print(f"   - Completed chapters: {len(user.completed_chapters)}")
        print(f"   - Current week start: {user.current_week_start}")
        print()
        
        return user
    
    def test_task_assignment_logic(self, user: User) -> List[Task]:
        """Test the core task assignment logic"""
        
        print(f"🔄 Testing task assignment for user: {user.name}")
        print(f"   - Current date: {datetime.now(timezone.utc).strftime('%A, %Y-%m-%d %H:%M UTC')}")
        print(f"   - Week start: {get_week_start().strftime('%A, %Y-%m-%d')}")
        print(f"   - Days left in week: {get_days_left_in_week()}")
        print(f"   - Completed chapters: {user.completed_chapters}")
        print()
        
        # Check if new tasks should be assigned
        should_assign = should_assign_new_tasks(user)
        print(f"   - Should assign new tasks: {should_assign}")
        
        if should_assign:
            # Assign new tasks
            tasks = assign_weekly_tasks(user)
            self.created_tasks.extend(tasks)
            
            print(f"✅ Assigned {len(tasks)} tasks:")
            
            for i, task in enumerate(tasks, 1):
                print(f"   {i}. {task.title}")
                print(f"      - Type: {task.type_of_task.value}")
                print(f"      - Subject: {task.subject.value}")
                print(f"      - Due: {task.due_date.strftime('%A, %Y-%m-%d %H:%M')}")
                print(f"      - Task Number: {task.task_number}")
                print(f"      - Priority Score: {calculate_task_priority(task)}")
                
                if task.type_of_task == TaskType.QUIZ:
                    attrs = task.quiz_related_attributes
                    print(f"      - Facet: {attrs.get('facet', 'N/A')}")
                    print(f"      - Tags: {len(attrs.get('tags', []))} tags")
                    print(f"      - Questions: {attrs.get('num_questions', 'N/A')}")
                    print(f"      - Duration: {attrs.get('duration_minutes', 'N/A')} min")
                    print(f"      - Passing Score: {attrs.get('passing_score', 'N/A')}%")
                    
                elif task.type_of_task == TaskType.AI_TUTORIAL:
                    attrs = task.ai_tutorial_related_attributes
                    print(f"      - Chapter: {attrs.get('chapter_id', 'N/A')}")
                    print(f"      - Title: {attrs.get('chapter_title', 'N/A')}")
                    print(f"      - Duration: {attrs.get('estimated_duration_minutes', 'N/A')} min")
                
                print()
            
            return tasks
        else:
            print("   ℹ️ No new tasks assigned (existing tasks for current week)")
            return []
    
    def test_task_priority_sorting(self, tasks: List[Task]):
        """Test task priority and sorting"""
        
        if not tasks:
            print("⚠️ No tasks to test priority sorting")
            return
            
        print("🔄 Testing task priority sorting...")
        
        # Sort tasks by priority
        sorted_tasks = sorted(tasks, key=lambda t: calculate_task_priority(t))
        
        print("   Task priority order (lower score = higher priority):")
        for i, task in enumerate(sorted_tasks, 1):
            priority = calculate_task_priority(task)
            days_until_due = task.get_days_until_due()
            is_overdue = task.is_overdue()
            
            status = "⚠️ OVERDUE" if is_overdue else f"📅 Due in {days_until_due} days"
            
            print(f"   {i}. {task.title}")
            print(f"      - Priority Score: {priority}")
            print(f"      - Status: {status}")
            print(f"      - Due Date: {task.due_date.strftime('%A, %Y-%m-%d %H:%M')}")
            print()
    
    def simulate_task_completion(self, user: User, task: Task, score: Optional[float] = None):
        """Simulate completing a task"""
        
        print(f"🔄 Simulating task completion...")
        print(f"   - Task: {task.title}")
        print(f"   - Type: {task.type_of_task.value}")
        
        # Mark task as completed
        task.mark_completed()
        
        # Add attempt info if it's a quiz
        if task.type_of_task == TaskType.QUIZ and score is not None:
            task.add_attempt(
                score=score,
                time_taken_minutes=8,
                correct_answers=int(score / 10) if score <= 100 else 10,
                total_questions=10,
                completed_at=datetime.now(timezone.utc).isoformat()
            )
            print(f"   - Score: {score}%")
        
        # Mark chapter as completed if it's an AI tutorial
        if task.type_of_task == TaskType.AI_TUTORIAL:
            chapter_id = task.ai_tutorial_related_attributes.get('chapter_id')
            if chapter_id:
                user.mark_chapter_completed(chapter_id)
                print(f"   - Marked chapter '{chapter_id}' as completed")
        
        print(f"✅ Task completed successfully!")
        print(f"   - Completion time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"   - Attempts: {task.attempts_info.get('attempts', 0)}")
        
        if task.type_of_task == TaskType.QUIZ:
            best_score = task.attempts_info.get('best_score')
            print(f"   - Best Score: {best_score}%" if best_score else "   - No score recorded")
        
        print()
    
    def test_user_progress_analytics(self, user: User, tasks: List[Task]):
        """Test user progress and analytics"""
        
        print("🔄 Testing user progress analytics...")
        
        # Calculate basic stats
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.completed])
        pending_tasks = total_tasks - completed_tasks
        overdue_tasks = len([t for t in tasks if t.is_overdue()])
        quiz_tasks = len([t for t in tasks if t.type_of_task == TaskType.QUIZ])
        tutorial_tasks = len([t for t in tasks if t.type_of_task == TaskType.AI_TUTORIAL])
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        print(f"   📊 Task Statistics:")
        print(f"   - Total Tasks: {total_tasks}")
        print(f"   - Completed: {completed_tasks}")
        print(f"   - Pending: {pending_tasks}")
        print(f"   - Overdue: {overdue_tasks}")
        print(f"   - Completion Rate: {completion_rate:.1f}%")
        print(f"   - Quiz Tasks: {quiz_tasks}")
        print(f"   - Tutorial Tasks: {tutorial_tasks}")
        print()
        
        print(f"   📈 Chapter Progress:")
        print(f"   - Completed Chapters: {len(user.completed_chapters)}")
        print(f"   - Next Chapter: {user.get_next_chapter() or 'All completed!'}")
        print(f"   - Chapters: {user.completed_chapters if user.completed_chapters else 'None'}")
        print()
    
    def simulate_different_day_scenarios(self):
        """Test task assignment on different days of the week"""
        
        print("🔄 Testing task assignment for different days of the week...")
        print()
        
        # Test scenarios for different days
        test_days = [
            ("Monday", 0),      # Start of week
            ("Wednesday", 2),   # Mid-week  
            ("Thursday", 3),    # Late mid-week
            ("Saturday", 5),    # Weekend
            ("Sunday", 6)       # End of week
        ]
        
        for day_name, weekday in test_days:
            print(f"📅 Scenario: Starting on {day_name}")
            
            # Create a mock date for this weekday
            today = datetime.now(timezone.utc)
            days_to_target = weekday - today.weekday()
            target_date = today + timedelta(days=days_to_target)
            
            # Create user with no current week set
            user = self.create_test_user(f"user_{day_name.lower()}", [])
            user.current_week_start = None  # Force new assignment
            
            # Mock the current date for testing
            import helper.task_assignment
            original_get_days_left = helper.task_assignment.get_days_left_in_week
            
            def mock_get_days_left(date=None):
                return 6 - weekday + 1  # Days left including today
            
            helper.task_assignment.get_days_left_in_week = mock_get_days_left
            
            try:
                tasks = assign_weekly_tasks(user, target_date)
                
                print(f"   - Days left in week: {6 - weekday + 1}")
                print(f"   - Tasks assigned: {len(tasks)}")
                
                task_breakdown = {}
                for task in tasks:
                    task_type = task.type_of_task.value
                    task_breakdown[task_type] = task_breakdown.get(task_type, 0) + 1
                
                for task_type, count in task_breakdown.items():
                    print(f"   - {task_type}: {count}")
                
                print()
                
            finally:
                # Restore original function
                helper.task_assignment.get_days_left_in_week = original_get_days_left
    
    def export_test_results(self, filename: str = "task_test_results.json"):
        """Export test results to a JSON file"""
        
        results = {
            "test_timestamp": datetime.now(timezone.utc).isoformat(),
            "users_tested": len(self.test_users),
            "tasks_created": len(self.created_tasks),
            "users": [],
            "tasks": []
        }
        
        # Export user data
        for user in self.test_users:
            results["users"].append({
                "id": user.id,
                "name": user.name,
                "completed_chapters": user.completed_chapters,
                "chapter_progress": f"{len(user.completed_chapters)}/7"
            })
        
        # Export task data
        for task in self.created_tasks:
            task_data = {
                "id": task.id,
                "title": task.title,
                "type": task.type_of_task.value,
                "subject": task.subject.value,
                "due_date": task.due_date.isoformat(),
                "completed": task.completed,
                "task_number": task.task_number,
                "priority_score": calculate_task_priority(task),
                "user_id": task.user_id
            }
            
            if task.type_of_task == TaskType.QUIZ:
                task_data["quiz_info"] = task.quiz_related_attributes
            else:
                task_data["tutorial_info"] = task.ai_tutorial_related_attributes
                
            results["tasks"].append(task_data)
        
        # Write to file
        filepath = os.path.join("testing", filename)
        os.makedirs("testing", exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"📁 Test results exported to: {filepath}")
        print()
    
    def run_comprehensive_test(self):
        """Run a comprehensive test of the task system"""
        
        print("🚀 Starting Comprehensive Task System Test")
        print("=" * 50)
        print()
        
        # Test 1: Create users with different chapter progress
        print("📝 TEST 1: Creating Test Users")
        print("-" * 30)
        
        user1 = self.create_test_user("new_user_001", [])
        user2 = self.create_test_user("progress_user_002", ["Chapter 1", "Chapter 2"])
        user3 = self.create_test_user("advanced_user_003", ["Chapter 1", "Chapter 2", "Chapter 3", "Chapter 4"])
        
        # Test 2: Task assignment for each user
        print("📝 TEST 2: Task Assignment")
        print("-" * 30)
        
        all_tasks = []
        for user in [user1, user2, user3]:
            tasks = self.test_task_assignment_logic(user)
            all_tasks.extend(tasks)
        
        # Test 3: Task priority sorting
        print("📝 TEST 3: Task Priority Sorting")
        print("-" * 30)
        
        if all_tasks:
            self.test_task_priority_sorting(all_tasks[:6])  # Test first 6 tasks
        
        # Test 4: Simulate task completions
        print("📝 TEST 4: Task Completion Simulation")
        print("-" * 30)
        
        if all_tasks:
            # Complete a quiz task
            quiz_tasks = [t for t in all_tasks if t.type_of_task == TaskType.QUIZ]
            if quiz_tasks:
                self.simulate_task_completion(user1, quiz_tasks[0], 85.0)
            
            # Complete a tutorial task
            tutorial_tasks = [t for t in all_tasks if t.type_of_task == TaskType.AI_TUTORIAL]
            if tutorial_tasks:
                self.simulate_task_completion(user1, tutorial_tasks[0])
        
        # Test 5: Progress analytics
        print("📝 TEST 5: Progress Analytics")
        print("-" * 30)
        
        user1_tasks = [t for t in all_tasks if t.user_id == user1.id]
        self.test_user_progress_analytics(user1, user1_tasks)
        
        # Test 6: Different day scenarios
        print("📝 TEST 6: Different Day Scenarios")
        print("-" * 30)
        
        self.simulate_different_day_scenarios()
        
        # Export results
        print("📝 TEST 7: Export Results")
        print("-" * 30)
        
        self.export_test_results()
        
        print("🎉 All Tests Completed Successfully!")
        print("=" * 50)

def main():
    """Main test runner"""
    
    print("🔧 Task System Local Testing")
    print("=" * 40)
    print()
    
    # Initialize tester
    tester = TaskTester()
    
    # Run tests
    try:
        tester.run_comprehensive_test()
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    print("🔍 Test Summary:")
    print(f"   - Users created: {len(tester.test_users)}")
    print(f"   - Tasks created: {len(tester.created_tasks)}")
    
    if tester.created_tasks:
        completed_tasks = len([t for t in tester.created_tasks if t.completed])
        print(f"   - Tasks completed: {completed_tasks}")
        print(f"   - Success rate: {(completed_tasks / len(tester.created_tasks) * 100):.1f}%")

if __name__ == "__main__":
    main()