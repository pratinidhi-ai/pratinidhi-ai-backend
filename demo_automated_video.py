"""
Demo: Automated Math Video Generation with Watermark Removal

This script provides 3 options:
1. Generate video only (no watermark removal)
2. Generate video + remove watermark with white patch (400x70)
3. Generate video + remove watermark with Educado logo (120x60)
"""

from math_tutor.math_ai_video_generator import generate_math_ai_video
from math_tutor.process_video import (
    remove_watermark_with_patch,
    remove_watermark_with_image
)
import os
import time

'''
I want to illustrate this script:
Stop losing focus during SAT practice… I’ve got the secret weapon.
Meet your brain on the SAT… it’s basically a cute, distracted squirrel.
Phone buzz? Gotta check it.
Snack nearby? Can’t resist.
That’s why you can’t get through a practice section.

Here’s the fix: the Acorn Stash Method. It’s the Pomodoro Technique, but for SAT warriors.
Step one: set a timer for 25 minutes. This is your FOCUS SPRINT.
Attack one practice section like your score depends on it. No phone, no snacks, no distractions—just you and the questions.

Step two: when the timer dings, take a guilt-free 5-minute break. Scroll, snack, stretch—you earned it.
Then repeat. You’re not studying for two hours straight… you’re doing four powerful, focused sprints.
Your brain gets rewards, and your score gets results.
'''

TEST_PROBLEM = "3D Visualization of parabola, cuboid, and plane transformations"
def demo_video_only():
    """
    Option 1: Generate video only (no watermark removal)
    """
    print("=" * 80)
    print("OPTION 1: Video Generation Only")
    print("=" * 80)
    
    problem = TEST_PROBLEM
    
    print(f"\n📝 Math Problem: {problem}")
    print("\n🚀 Generating video...\n")
    
    try:
        start_time = time.time()
        
        result = generate_math_ai_video(
            math_problem=problem,
            remove_watermark=False  # No watermark removal
        )
        
        print("\n" + "=" * 80)
        print("✅ VIDEO GENERATED!")
        print("=" * 80)
        print(f"\n� Video URL:     {result.get('video_link')}")
        print(f"📄 VTT File:      {result.get('vtt_file')}")
        print(f"📄 SRT File:      {result.get('srt_file')}")
        
        end_time = time.time()
        print(f"\n⏱️  Total Time: {end_time - start_time:.2f} seconds")
        print("\n💡 The video link can be opened in browser to view/download")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def demo_video_with_white_patch():
    """
    Option 2: Generate video + remove watermark with white patch (400x70)
    """
    print("=" * 80)
    print("OPTION 2: Video Generation + White Patch Removal")
    print("=" * 80)
    
    problem = TEST_PROBLEM  
    
    print(f"\n📝 Math Problem: {problem}")
    print("\n🚀 Generating video and removing watermark with white patch...\n")

    try:
        start_time = time.time()
        
        # Step 1: Generate video
        print("📹 Step 1/2: Generating AI video...")
        result = generate_math_ai_video(
            math_problem=problem,
            remove_watermark=False  # We'll process it manually with correct dimensions
        )
        
        video_url = result.get('video_link')
        print(f"✅ Video generated: {video_url}")
        
        # Step 2: Remove watermark with white patch
        print("\n🎨 Step 2/2: Removing watermark with white patch (400x70)...")
        
        # Create output directory if it doesn't exist
        os.makedirs("./demo_output", exist_ok=True)
        output_path = "./demo_output/video_white_patch.mp4"
        
        processed_video = remove_watermark_with_patch(
            video_input=video_url,
            output_path=output_path,
            patch_width=400,              # Tested dimensions
            patch_height=70,              # Tested dimensions
            patch_color=(255, 255, 255),  # White
            position="bottom-right",
            margin_x=0,
            margin_y=0
        )
        
        print("\n" + "=" * 80)
        print("✅ VIDEO GENERATED & WATERMARK REMOVED!")
        print("=" * 80)
        
        print(f"\n📹 Original Video URL: {video_url}")
        print(f"📄 VTT Subtitles:      {result.get('vtt_file')}")
        print(f"📄 SRT Subtitles:      {result.get('srt_file')}")
        print(f"\n🎬 Processed Video:    {processed_video}")
        
        if os.path.exists(processed_video):
            size_mb = os.path.getsize(processed_video) / (1024 * 1024)
            print(f"📊 File Size:          {size_mb:.2f} MB")
        
        end_time = time.time()
        print(f"\n⏱️  Total Time: {end_time - start_time:.2f} seconds")
        print("\n🎉 Video ready with watermark covered by white patch (400x70)!")
        
        return {
            'original_url': video_url,
            'processed_video': processed_video,
            'vtt_file': result.get('vtt_file'),
            'srt_file': result.get('srt_file')
        }
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def demo_video_with_logo():
    """
    Option 3: Generate video + remove watermark with Educado logo (120x60)
    """
    print("=" * 80)
    print("OPTION 3: Video Generation + Educado Logo Overlay")
    print("=" * 80)
    
    problem = TEST_PROBLEM
    
    print(f"\n📝 Math Problem: {problem}")
    print("\n🚀 Generating video and adding Educado logo overlay...\n")
    
    # Check if logo exists
    logo_path = "resources/Educado.jpg"
    if not os.path.exists(logo_path):
        print(f"❌ Error: Logo file not found at {logo_path}")
        print("   Please ensure the file exists before running this option.")
        return None
    
    try:
        start_time = time.time()
        
        # Step 1: Generate video
        print("📹 Step 1/2: Generating AI video...")
        result = generate_math_ai_video(
            math_problem=problem,
            remove_watermark=False  # We'll process it manually with correct dimensions
        )
        
        video_url = result.get('video_link')
        print(f"✅ Video generated: {video_url}")
        
        # Step 2: Remove watermark with Educado logo
        print("\n🖼️  Step 2/2: Adding Educado logo overlay (120x60)...")
        
        # Create output directory if it doesn't exist
        os.makedirs("./demo_output", exist_ok=True)
        output_path = "./demo_output/video_with_educado_logo.mp4"
        
        processed_video = remove_watermark_with_image(
            video_input=video_url,
            overlay_image=logo_path,  # Educado.jpg from resources
            output_path=output_path,
            patch_width=120,          # Tested dimensions
            patch_height=60,          # Tested dimensions
            position="bottom-right",
            margin_x=0,
            margin_y=0
        )
        
        print("\n" + "=" * 80)
        print("✅ VIDEO GENERATED & EDUCADO LOGO ADDED!")
        print("=" * 80)
        
        print(f"\n📹 Original Video URL: {video_url}")
        print(f"📄 VTT Subtitles:      {result.get('vtt_file')}")
        print(f"📄 SRT Subtitles:      {result.get('srt_file')}")
        print(f"\n🎬 Processed Video:    {processed_video}")
        print(f"🖼️  Logo Used:          {logo_path}")
        
        if os.path.exists(processed_video):
            size_mb = os.path.getsize(processed_video) / (1024 * 1024)
            print(f"📊 File Size:          {size_mb:.2f} MB")
        
        end_time = time.time()
        print(f"\n⏱️  Total Time: {end_time - start_time:.2f} seconds")
        print("\n🎉 Video ready with Educado branding (120x60)!")
        
        return {
            'original_url': video_url,
            'processed_video': processed_video,
            'vtt_file': result.get('vtt_file'),
            'srt_file': result.get('srt_file')
        }
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🎓 Math AI Video Generator - Educado")
    print("=" * 80)
    
    print("\nChoose an option:")
    print("1. Video only (no watermark removal)")
    print("2. Video + remove watermark with white patch (400x70)")
    print("3. Video + remove watermark with Educado logo (120x60)")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    if choice == "1":
        demo_video_only()
    elif choice == "2":
        demo_video_with_white_patch()
    elif choice == "3":
        demo_video_with_logo()
    else:
        print("\n❌ Invalid choice. Please run the script again and choose 1, 2, or 3.")

