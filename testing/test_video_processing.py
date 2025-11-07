"""
Test script for video watermark removal
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from math_tutor.process_video import remove_watermark_from_video, process_knolify_video


def test_with_local_file():
    """Test with a local video file"""
    print("=" * 70)
    print("Test 1: Local Video File")
    print("=" * 70)
    
    input_video = input("Enter path to local video file (or press Enter to skip): ").strip()
    
    if not input_video:
        print("⏭️  Skipped local file test")
        return False
    
    if not os.path.exists(input_video):
        print(f"❌ File not found: {input_video}")
        return False
    
    try:
        output_video = "output_no_watermark.mp4"
        
        result = remove_watermark_from_video(
            video_input=input_video,
            output_path=output_video,
            patch_width=100,
            patch_height=50,
            patch_color=(255, 255, 255),
            position="bottom-right"
        )
        
        print(f"\n✅ Test passed!")
        print(f"📁 Output file: {result}")
        
        if os.path.exists(result):
            size_mb = os.path.getsize(result) / (1024 * 1024)
            print(f"📊 File size: {size_mb:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False


def test_with_url():
    """Test with a video URL"""
    print("\n" + "=" * 70)
    print("Test 2: Video URL")
    print("=" * 70)
    
    video_url = input("Enter video URL (or press Enter to skip): ").strip()
    
    if not video_url:
        print("⏭️  Skipped URL test")
        return False
    
    try:
        output_video = "output_from_url.mp4"
        
        result = remove_watermark_from_video(
            video_input=video_url,
            output_path=output_video,
            patch_width=100,
            patch_height=50
        )
        
        print(f"\n✅ Test passed!")
        print(f"📁 Output file: {result}")
        
        if os.path.exists(result):
            size_mb = os.path.getsize(result) / (1024 * 1024)
            print(f"📊 File size: {size_mb:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False


def test_knolify_convenience_function():
    """Test the Knolify-specific convenience function"""
    print("\n" + "=" * 70)
    print("Test 3: Knolify Video Processing")
    print("=" * 70)
    
    video_url = input("Enter Knolify video URL (or press Enter to skip): ").strip()
    
    if not video_url:
        print("⏭️  Skipped Knolify test")
        return False
    
    try:
        output_video = "knolify_processed.mp4"
        
        result = process_knolify_video(video_url, output_video)
        
        print(f"\n✅ Test passed!")
        print(f"📁 Output file: {result}")
        
        if os.path.exists(result):
            size_mb = os.path.getsize(result) / (1024 * 1024)
            print(f"📊 File size: {size_mb:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False


def test_custom_patch():
    """Test with custom patch settings"""
    print("\n" + "=" * 70)
    print("Test 4: Custom Patch Settings")
    print("=" * 70)
    
    input_video = input("Enter video path/URL (or press Enter to skip): ").strip()
    
    if not input_video:
        print("⏭️  Skipped custom patch test")
        return False
    
    try:
        output_video = "output_custom_patch.mp4"
        
        # Black patch, larger size, top-right corner
        result = remove_watermark_from_video(
            video_input=input_video,
            output_path=output_video,
            patch_width=150,
            patch_height=75,
            patch_color=(0, 0, 0),  # Black
            position="top-right",
            margin_x=10,
            margin_y=10
        )
        
        print(f"\n✅ Test passed!")
        print(f"📁 Output file: {result}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False


def quick_test():
    """Quick automated test with a sample URL"""
    print("\n" + "=" * 70)
    print("Quick Test: Sample Video")
    print("=" * 70)
    
    # Using a sample video URL (you can replace with actual test URL)
    print("ℹ️  This requires a valid video URL to test")
    print("ℹ️  If you have a Knolify video link, use Test 3 instead")
    
    return False


if __name__ == "__main__":
    print("=" * 70)
    print("Video Watermark Removal Test Suite")
    print("=" * 70)
    print("\n📋 Available Tests:")
    print("1. Local video file")
    print("2. Video from URL")
    print("3. Knolify video (convenience function)")
    print("4. Custom patch settings")
    print("\n" + "=" * 70)
    
    results = []
    
    # Check if moviepy is installed
    try:
        from moviepy.editor import VideoFileClip
        print("✅ moviepy is installed")
    except ImportError:
        print("❌ moviepy is NOT installed")
        print("\nPlease install it with:")
        print("  pip install moviepy")
        print("\nNote: moviepy also requires ffmpeg to be installed on your system")
        sys.exit(1)
    
    print("\n")
    
    # Run tests
    test1 = test_with_local_file()
    results.append(("Local File", test1))
    
    test2 = test_with_url()
    results.append(("URL", test2))
    
    test3 = test_knolify_convenience_function()
    results.append(("Knolify", test3))
    
    test4 = test_custom_patch()
    results.append(("Custom Patch", test4))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Results Summary")
    print("=" * 70)
    for name, result in results:
        if result is None or result is False:
            status = "⏭️  SKIPPED"
        else:
            status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")
    
    print("\n" + "=" * 70)
    print("Usage Tips:")
    print("=" * 70)
    print("• The function works with both local files and URLs")
    print("• Default patch: 100x50 white pixels at bottom-right")
    print("• Customize: patch size, color, position, and margins")
    print("• Processing time depends on video length and resolution")
    print("\nNote: Ensure ffmpeg is installed on your system for moviepy to work")
