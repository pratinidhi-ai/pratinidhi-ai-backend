"""
Simple Task Testing Runner
Easy script to test task creation locally
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Setup test environment
import testing.test_config

# Setup mock database
from testing.mock_database import setup_mock_database, load_test_data
print("🔧 Setting up mock database for testing...")
mock_client = setup_mock_database()
load_test_data(mock_client)
print("✅ Mock database ready!\n")

def run_basic_test():
    """Run a basic test with one user"""
    print("🚀 Running Basic Task Test")
    print("=" * 30)
    
    try:
        from testing.task_testing import TaskTester
        
        tester = TaskTester()
        
        # Create a new user
        print("1️⃣ Creating test user...")
        user = tester.create_test_user("test_user_basic", [])
        
        # Test task assignment
        print("2️⃣ Testing task assignment...")
        tasks = tester.test_task_assignment_logic(user)
        
        if tasks:
            # Test task details
            print("3️⃣ Task Details:")
            for i, task in enumerate(tasks, 1):
                print(f"   Task {i}: {task.title}")
                print(f"   - Type: {task.type_of_task.value}")
                print(f"   - Due: {task.due_date.strftime('%Y-%m-%d %H:%M')}")
                
                if hasattr(task, 'quiz_related_attributes') and task.quiz_related_attributes:
                    print(f"   - Quiz Tags: {len(task.quiz_related_attributes.get('tags', []))}")
                elif hasattr(task, 'ai_tutorial_related_attributes') and task.ai_tutorial_related_attributes:
                    print(f"   - Chapter: {task.ai_tutorial_related_attributes.get('chapter_id', 'N/A')}")
                print()
            
            # Test task completion
            print("4️⃣ Testing task completion...")
            if tasks:
                first_task = tasks[0]
                if first_task.type_of_task.value == "quiz":
                    tester.simulate_task_completion(user, first_task, 88.0)
                else:
                    tester.simulate_task_completion(user, first_task)
        
        print("✅ Basic test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

def run_full_test():
    """Run the comprehensive test suite"""
    try:
        from testing.task_testing import main
        main()
    except Exception as e:
        print(f"❌ Full test failed: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main menu for testing"""
    print("🔧 Task System Testing Menu")
    print("=" * 30)
    print("1. Basic Test (Quick)")
    print("2. Full Test Suite (Comprehensive)")
    print("3. Exit")
    print()
    
    while True:
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == "1":
            print()
            run_basic_test()
            break
        elif choice == "2":
            print()
            run_full_test()
            break
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()