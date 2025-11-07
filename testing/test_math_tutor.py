"""
Test script for Math Tutor API
This script tests the math tutor endpoint functionality.
"""
import requests
import json
from math_tutor.math_tutor_response import generate_math_tutor_response

# Configuration
BASE_URL = "http://localhost:8080"
MATH_TUTOR_ENDPOINT = f"{BASE_URL}/math-tutor/solve"
HEALTH_ENDPOINT = f"{BASE_URL}/math-tutor/health"

# You need to replace this with a valid Firebase token
# To get a token, run: python testing/get_firebase_token.py
TOKEN = "YOUR_FIREBASE_TOKEN_HERE"

TEST_PROBLEM = "Solve: Find if two lines are orthogonal to each other. First line: 2x + y = 3 and Second line: x - 2y = 5"


def test_generate_math_tutor_response():
    """Test the generate_math_tutor_response function directly"""
    print(f"\nTesting generate_math_tutor_response with problem: {TEST_PROBLEM}")
    try:
        solution = generate_math_tutor_response(TEST_PROBLEM)
        print(f"Generated Solution: {solution}")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_health_check():
    """Test the health check endpoint (no auth required)"""
    print("Testing health check endpoint...")
    try:
        response = requests.get(HEALTH_ENDPOINT)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def test_solve_math_problem(problem):
    """Test the solve math problem endpoint"""
    print(f"\nTesting solve endpoint with problem: {problem}")
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "problem": problem,
        "max_tokens": 4000,
        "temperature": 0.3
    }
    
    try:
        response = requests.post(MATH_TUTOR_ENDPOINT, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def test_missing_problem():
    """Test with missing problem field"""
    print("\nTesting with missing problem field...")
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(MATH_TUTOR_ENDPOINT, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 400  # Should return 400 Bad Request
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def test_unauthorized():
    """Test without authentication token"""
    print("\nTesting without authentication...")
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "problem": "Solve for x: 2x + 5 = 15"
    }
    
    try:
        response = requests.post(MATH_TUTOR_ENDPOINT, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 401  # Should return 401 Unauthorized
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def test_apis():
    # Test 1: Health check (no auth required)
    test1 = test_health_check()
    
    # Test 2: Unauthorized access
    test2 = test_unauthorized()
    
    # Check if token is set
    if TOKEN == "YOUR_FIREBASE_TOKEN_HERE":
        print("\n" + "=" * 60)
        print("WARNING: Please set a valid Firebase token in TOKEN variable")
        print("Run: python testing/get_firebase_token.py")
        print("=" * 60)
    else:
        # Test 3: Valid math problem
        test3 = test_solve_math_problem("Solve for x: 2x + 5 = 15")
        
        # Test 4: More complex problem
        test4 = test_solve_math_problem(
            "Find the derivative of f(x) = 3x^2 + 2x - 5"
        )
        
        # Test 5: Missing problem field
        test5 = test_missing_problem()
        
        # Summary
        print("\n" + "=" * 60)
        print("Test Results Summary")
        print("=" * 60)
        print(f"Health Check: {'✓ PASSED' if test1 else '✗ FAILED'}")
        print(f"Unauthorized Access: {'✓ PASSED' if test2 else '✗ FAILED'}")
        print(f"Valid Math Problem: {'✓ PASSED' if test3 else '✗ FAILED'}")
        print(f"Complex Problem: {'✓ PASSED' if test4 else '✗ FAILED'}")
        print(f"Missing Problem Field: {'✓ PASSED' if test5 else '✗ FAILED'}")

if __name__ == "__main__":
    print("=" * 60)
    print("Math Tutor API Test Suite")
    print("=" * 60)
    
    # Testing the math tutor response function directly
    test_generate_math_tutor_response()
    
    #test_apis()
