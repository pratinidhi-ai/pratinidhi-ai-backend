"""
Test script for video watermark removal with two separate functions:
1. remove_watermark_with_patch() - for solid color patches
2. remove_watermark_with_image() - for custom image overlays
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from math_tutor.process_video import (
    remove_watermark_with_patch,
    remove_watermark_with_image,
    remove_watermark_from_video  # Backward compatible wrapper
)


def test_color_patch():
    """
    Test solid color patch watermark removal.
    """
    print("\n" + "="*60)
    print("TEST 1: Solid Color Patch")
    print("="*60)
    
    video_path = "path/to/your/test/video.mp4"
    output_path = "output_with_color_patch.mp4"
    
    try:
        result = remove_watermark_with_patch(
            video_input=video_path,
            output_path=output_path,
            patch_width=400,
            patch_height=100,
            patch_color=(255, 255, 255),  # White
            position="bottom-right"
        )
        
        print(f"\n✅ SUCCESS: Video processed with white patch")
        print(f"📁 Output: {result}")
        
    except FileNotFoundError:
        print("⚠️  Test skipped: Please provide valid video path")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")


def test_image_overlay_local_file():
    """
    Test image overlay with a local image file.
    """
    print("\n" + "="*60)
    print("TEST 2: Image Overlay with Local File")
    print("="*60)
    
    video_path = "path/to/your/test/video.mp4"
    image_path = "path/to/your/overlay/image.png"
    output_path = "output_with_local_image_overlay.mp4"
    
    try:
        result = remove_watermark_with_image(
            video_input=video_path,
            overlay_image=image_path,
            output_path=output_path,
            patch_width=400,
            patch_height=100,
            position="bottom-right"
        )
        
        print(f"\n✅ SUCCESS: Video processed with local image overlay")
        print(f"📁 Output: {result}")
        
    except FileNotFoundError:
        print("⚠️  Test skipped: Please provide valid video and image paths")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")


def test_image_overlay_url():
    """
    Test image overlay with a URL image.
    """
    print("\n" + "="*60)
    print("TEST 3: Image Overlay with URL")
    print("="*60)
    
    video_url = "https://knowlify-videos1.s3.us-west-2.amazonaws.com/example.mp4"
    image_url = "https://example.com/logo.png"
    output_path = "output_with_url_image_overlay.mp4"
    
    try:
        result = remove_watermark_with_image(
            video_input=video_url,
            overlay_image=image_url,
            output_path=output_path,
            patch_width=400,
            patch_height=100,
            position="bottom-right"
        )
        
        print(f"\n✅ SUCCESS: Video processed with URL image overlay")
        print(f"📁 Output: {result}")
        
    except Exception as e:
        print(f"⚠️  Test skipped or failed: {str(e)}")
        print("    (This is expected if you're using placeholder URLs)")


def test_backward_compatibility():
    """
    Test the wrapper function for backward compatibility.
    """
    print("\n" + "="*60)
    print("TEST 4: Backward Compatible Wrapper")
    print("="*60)
    
    video_path = "path/to/your/test/video.mp4"
    
    try:
        # Test 4a: With patch (no overlay_image)
        print("\n4a. Testing with color patch...")
        result1 = remove_watermark_from_video(
            video_input=video_path,
            output_path="output_wrapper_patch.mp4",
            patch_color=(255, 255, 255)
        )
        print(f"✅ Wrapper with patch: {result1}")
        
        # Test 4b: With image overlay
        print("\n4b. Testing with image overlay...")
        result2 = remove_watermark_from_video(
            video_input=video_path,
            output_path="output_wrapper_image.mp4",
            overlay_image="path/to/logo.png"
        )
        print(f"✅ Wrapper with image: {result2}")
        
    except FileNotFoundError:
        print("⚠️  Test skipped: Please provide valid paths")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")


def show_usage_examples():
    """Display usage examples for both functions."""
    print("\n" + "="*60)
    print("USAGE EXAMPLES - TWO SEPARATE FUNCTIONS")
    print("="*60)
    
    examples = """
# ============================================================
# FUNCTION 1: remove_watermark_with_patch()
# Use this for solid color patches (white, black, etc.)
# ============================================================

from math_tutor.process_video import remove_watermark_with_patch

# Example 1a: White patch (default)
result = remove_watermark_with_patch(
    video_input="input_video.mp4",
    output_path="output_with_white_patch.mp4",
    patch_width=400,
    patch_height=100,
    patch_color=(255, 255, 255),  # White
    position="bottom-right"
)

# Example 1b: Black patch
result = remove_watermark_with_patch(
    video_input="input_video.mp4",
    output_path="output_with_black_patch.mp4",
    patch_width=400,
    patch_height=100,
    patch_color=(0, 0, 0),  # Black
    position="bottom-left",
    margin_x=10,
    margin_y=10
)

# Example 1c: Custom color (green)
result = remove_watermark_with_patch(
    video_input="input_video.mp4",
    output_path="output_with_green_patch.mp4",
    patch_color=(0, 255, 0)  # Green
)


# ============================================================
# FUNCTION 2: remove_watermark_with_image()
# Use this for custom image overlays (logos, branding, etc.)
# ============================================================

from math_tutor.process_video import remove_watermark_with_image

# Example 2a: Local image file
result = remove_watermark_with_image(
    video_input="input_video.mp4",
    overlay_image="my_logo.png",  # REQUIRED parameter
    output_path="output_with_logo.mp4",
    patch_width=400,
    patch_height=100,
    position="bottom-right"
)

# Example 2b: Image from URL
result = remove_watermark_with_image(
    video_input="https://example.com/video.mp4",
    overlay_image="https://example.com/watermark.png",
    output_path="branded_video.mp4",
    patch_width=300,
    patch_height=80,
    position="bottom-left",
    margin_x=10,
    margin_y=10
)


# ============================================================
# WRAPPER FUNCTION: remove_watermark_from_video()
# Backward compatible - automatically chooses patch or image
# ============================================================

from math_tutor.process_video import remove_watermark_from_video

# Example 3a: Without overlay_image = uses patch
result = remove_watermark_from_video(
    video_input="input.mp4",
    output_path="output.mp4",
    patch_color=(255, 255, 255)  # White patch
)

# Example 3b: With overlay_image = uses image overlay
result = remove_watermark_from_video(
    video_input="input.mp4",
    output_path="output.mp4",
    overlay_image="logo.png"  # Image overlay
)


# ============================================================
# SUPPORTED IMAGE FORMATS
# ============================================================
# - PNG (with transparency support)
# - JPG/JPEG
# - GIF
# - WEBP
# - Any format supported by MoviePy/PIL
"""
    
    print(examples)


if __name__ == "__main__":
    print("\n🎬 VIDEO WATERMARK REMOVAL TEST SUITE")
    print("="*60)
    
    # Show usage examples first
    show_usage_examples()
    
    # Run tests
    print("\n\n🧪 RUNNING TESTS...")
    print("="*60)
    print("\nNOTE: To run these tests, you need to:")
    print("1. Update video_path and image_path with actual file paths")
    print("2. Have MoviePy installed: pip install moviepy")
    print("3. Have a test video file available")
    print("4. Have a test image file (PNG/JPG) for image overlay tests")
    
    # Uncomment these when you have actual files to test with
    # test_color_patch()
    # test_image_overlay_local_file()
    # test_image_overlay_url()
    # test_backward_compatibility()
    
    print("\n" + "="*60)
    print("✅ Test script ready! Update paths and uncomment tests to run.")
    print("="*60)

