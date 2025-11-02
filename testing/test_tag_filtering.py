"""
Quick test script for tag filtering functionality
Run this after creating the Firebase indexes
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"  # Change if needed
TOKEN = "YOUR_BEARER_TOKEN_HERE"  # Replace with actual token

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}

def test_single_tag():
    """Test filtering with a single tag"""
    print("\n=== Test 1: Single Tag Filter ===")
    payload = {
        "subject_name": "math",
        "sub_category": "algebra",
        "selected_difficulty_level": 3,
        "number_of_questions": 5,
        "tag": "linear_equations"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/questions/fetch-quiz",
        headers=headers,
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response

def test_multiple_tags():
    """Test filtering with multiple tags (array-contains-any)"""
    print("\n=== Test 2: Multiple Tags Filter ===")
    payload = {
        "subject_name": "math",
        "sub_category": "algebra",
        "selected_difficulty_level": 3,
        "number_of_questions": 5,
        "tags": ["linear_equations", "quadratic_equations", "word_problems"]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/questions/fetch-quiz",
        headers=headers,
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response

def test_theme_and_tags():
    """Test combining theme and tag filters"""
    print("\n=== Test 3: Theme + Tags Filter ===")
    payload = {
        "subject_name": "math",
        "sub_category": "algebra",
        "selected_difficulty_level": 3,
        "number_of_questions": 5,
        "theme": "Harry Potter",
        "tags": ["linear_equations", "word_problems"]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/questions/fetch-quiz",
        headers=headers,
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response

def test_invalid_tags():
    """Test validation - tags must be array"""
    print("\n=== Test 4: Invalid Tags (not an array) ===")
    payload = {
        "subject_name": "math",
        "sub_category": "algebra",
        "selected_difficulty_level": 3,
        "number_of_questions": 5,
        "tags": "single_string"  # Should be array
    }
    
    response = requests.post(
        f"{BASE_URL}/api/questions/fetch-quiz",
        headers=headers,
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response

def test_too_many_tags():
    """Test validation - max 10 tags"""
    print("\n=== Test 5: Too Many Tags (>10) ===")
    payload = {
        "subject_name": "math",
        "sub_category": "algebra",
        "selected_difficulty_level": 3,
        "number_of_questions": 5,
        "tags": [f"tag{i}" for i in range(11)]  # 11 tags (exceeds limit)
    }
    
    response = requests.post(
        f"{BASE_URL}/api/questions/fetch-quiz",
        headers=headers,
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response

def test_no_filters():
    """Test without any filters (baseline)"""
    print("\n=== Test 6: No Filters (Baseline) ===")
    payload = {
        "subject_name": "math",
        "sub_category": "algebra",
        "selected_difficulty_level": 3,
        "number_of_questions": 5
    }
    
    response = requests.post(
        f"{BASE_URL}/api/questions/fetch-quiz",
        headers=headers,
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response

def main():
    """Run all tests"""
    print("=" * 60)
    print("Tag Filtering Test Suite")
    print("=" * 60)
    
    if TOKEN == "YOUR_BEARER_TOKEN_HERE":
        print("\n⚠️  WARNING: Please set your Bearer token in the TOKEN variable!")
        print("You can get a token from testing/test_token.txt or run testing/get_firebase_token.py\n")
        return
    
    tests = [
        ("Baseline (No Filters)", test_no_filters),
        ("Single Tag", test_single_tag),
        ("Multiple Tags", test_multiple_tags),
        ("Theme + Tags", test_theme_and_tags),
        ("Invalid Tags Validation", test_invalid_tags),
        ("Too Many Tags Validation", test_too_many_tags),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            response = test_func()
            results[test_name] = {
                "status": response.status_code,
                "success": response.status_code == 200 or response.status_code == 400  # 400 is expected for validation tests
            }
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results[test_name] = {
                "status": "ERROR",
                "success": False,
                "error": str(e)
            }
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        status_icon = "✅" if result["success"] else "❌"
        print(f"{status_icon} {test_name}: {result['status']}")
    
    print("\n" + "=" * 60)
    
    # Check for missing index error
    print("\n📝 Note: If you see 'Missing Index' errors, follow these steps:")
    print("1. Copy the URL from the error message")
    print("2. Open it in your browser")
    print("3. Click 'Create Index' in Firebase Console")
    print("4. Wait 5-15 minutes for the index to build")
    print("5. Run this test script again")
    print("\nSee FIREBASE_TAG_INDEX_SETUP.md for detailed instructions.")

if __name__ == "__main__":
    main()
