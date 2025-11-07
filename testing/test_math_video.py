"""
Test script for Math Tutor Video Generation API
This script tests the video generation functionality.
"""
import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:8080"
SOLVE_WITH_VIDEO_ENDPOINT = f"{BASE_URL}/math-tutor/solve-with-video"

# You need to replace this with a valid Firebase token
# To get a token, run: python testing/get_firebase_token.py
TOKEN = "YOUR_FIREBASE_TOKEN_HERE"

TEST_PROBLEM = "Solve: Given coordinates of four points A(1,2), B(3,4), C(5,6), and D(7,8), determine if they form a square."

def test_math_ai_video_generation_with_watermark_removal():
    """Test the generate_math_ai_video function with watermark removal"""
    from math_tutor.math_ai_video_generator import generate_math_ai_video
    import os

    print("=" * 70)
    print("Test: Video Generation + Watermark Removal (Automated)")
    print("=" * 70)
    print(f"\nProblem: {TEST_PROBLEM}")
    
    try:
        # Generate video and automatically remove watermark
        result = generate_math_ai_video(
            math_problem=TEST_PROBLEM,
            remove_watermark=True,
            output_dir="./processed_videos"  # Save to this directory
        )
        
        print("\n" + "=" * 70)
        print("Results:")
        print("=" * 70)
        print(f"✅ Video Link (Original): {result.get('video_link')}")
        print(f"✅ VTT File: {result.get('vtt_file')}")
        print(f"✅ SRT File: {result.get('srt_file')}")
        
        if result.get('watermark_removed'):
            print(f"✅ Processed Video (No Watermark): {result.get('processed_video_path')}")
            
            # Check if file exists
            if os.path.exists(result.get('processed_video_path')):
                size_mb = os.path.getsize(result.get('processed_video_path')) / (1024 * 1024)
                print(f"📊 Processed video size: {size_mb:.2f} MB")
        else:
            print(f"❌ Watermark removal failed: {result.get('watermark_error')}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_math_ai_video_generation():
    """Test the generate_math_ai_video function directly (without watermark removal)"""
    from math_tutor.math_ai_video_generator import generate_math_ai_video

    print("=" * 70)
    print("Test: Video Generation Only (No Watermark Removal)")
    print("=" * 70)
    print(f"\nProblem: {TEST_PROBLEM}")
    
    try:
        result = generate_math_ai_video(
            math_problem=TEST_PROBLEM,
            remove_watermark=False  # Don't remove watermark
        )
        
        print("\n" + "=" * 70)
        print("Results:")
        print("=" * 70)
        print(f"✅ Generated Video Link: {result.get('video_link')}")
        print(f"✅ VTT File: {result.get('vtt_file')}")
        print(f"✅ SRT File: {result.get('srt_file')}")
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_solve_with_video(problem, generate_video=True):
    """Test the solve with video endpoint"""
    print(f"\nTesting solve-with-video endpoint")
    print(f"Problem: {problem}")
    print(f"Generate video: {generate_video}")
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "problem": problem,
        "max_tokens": 4000,
        "temperature": 0.3,
        "generate_video": generate_video
    }
    
    try:
        print("\nSending request...")
        response = requests.post(SOLVE_WITH_VIDEO_ENDPOINT, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        
        result = response.json()
        print(f"\nResponse:")
        print(json.dumps(result, indent=2))
        
        if response.status_code == 200 and result.get("success"):
            print("\n✓ Solution generated successfully")
            if "video" in result:
                if result["video"].get("status") == "completed":
                    print("✓ Video generated successfully")
                    print(f"Video Link: {result['video'].get('video_link')}")
                    print(f"VTT File: {result['video'].get('vtt_file')}")
                else:
                    print(f"✗ Video generation failed: {result['video'].get('error', 'Unknown error')}")
        else:
            print("\n✗ Request failed")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def test_without_video(problem):
    """Test solving without video generation"""
    print(f"\nTesting solve-with-video endpoint WITHOUT video generation")
    print(f"Problem: {problem}")
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "problem": problem,
        "generate_video": False
    }
    
    try:
        print("\nSending request...")
        response = requests.post(SOLVE_WITH_VIDEO_ENDPOINT, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        
        result = response.json()
        print(f"\nResponse:")
        print(json.dumps(result, indent=2))
        
        if response.status_code == 200 and "video" not in result:
            print("\n✓ Solution generated without video (as expected)")
            return True
        else:
            print("\n✗ Test failed")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def check_environment():
    """Check if KNOLIFY_API_KEY is set"""
    knolify_key = os.getenv("KNOLIFY_API_KEY")
    if knolify_key:
        print("✓ KNOLIFY_API_KEY is set in environment")
        return True
    else:
        print("✗ KNOLIFY_API_KEY is NOT set in environment")
        print("Please set it with: $env:KNOLIFY_API_KEY='your-api-key'")
        return False

def test_apis():
    # Check environment
    print("\n1. Checking Environment Variables")
    print("-" * 70)
    env_ok = check_environment()
    
    # Check if token is set
    if TOKEN == "YOUR_FIREBASE_TOKEN_HERE":
        print("\n" + "=" * 70)
        print("WARNING: Please set a valid Firebase token in TOKEN variable")
        print("Run: python testing/get_firebase_token.py")
        print("=" * 70)
    else:
        # Test 1: Solve with video generation
        print("\n2. Test: Solve with Video Generation")
        print("-" * 70)
        test1 = test_solve_with_video("Solve for x: 2x + 5 = 15", generate_video=True)
        
        # Test 2: Solve without video generation
        print("\n3. Test: Solve WITHOUT Video Generation")
        print("-" * 70)
        test2 = test_without_video("Find the derivative of f(x) = x^2 + 3x")
        
        # Summary
        print("\n" + "=" * 70)
        print("Test Results Summary")
        print("=" * 70)
        print(f"Environment Check: {'✓ PASSED' if env_ok else '✗ FAILED'}")
        print(f"Solve with Video: {'✓ PASSED' if test1 else '✗ FAILED'}")
        print(f"Solve without Video: {'✓ PASSED' if test2 else '✗ FAILED'}")
        print("\nNote: Video generation may take 20-30 seconds")

if __name__ == "__main__":
    print("=" * 70)
    print("Math Tutor Video Generation Test Suite")
    print("=" * 70)
    
    print("\n🎯 Choose a test to run:")
    print("1. Generate video + Remove watermark (AUTOMATED)")
    print("2. Generate video only (no watermark removal)")
    print("3. Test API endpoints (requires Firebase token)")
    
    choice = input("\nEnter choice (1/2/3) or press Enter for option 1: ").strip()
    
    if choice == "2":
        # Test video generation without watermark removal
        test_math_ai_video_generation()
    elif choice == "3":
        # Test API endpoints
        test_apis()
    else:
        # Default: Test video generation with watermark removal
        test_math_ai_video_generation_with_watermark_removal()
    
