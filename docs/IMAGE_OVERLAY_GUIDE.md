# Image Overlay Guide - Custom Watermark Replacement

## Overview

The video watermark removal feature now supports **custom image overlays** in addition to solid color patches. This allows you to place your own logo, branding, or custom graphics over watermarked areas in videos.

## Features

✅ **Flexible Input**: Works with both local image files and image URLs  
✅ **Multiple Formats**: Supports PNG, JPG, GIF, WEBP  
✅ **Automatic Resizing**: Images are automatically resized to match specified dimensions  
✅ **Transparency Support**: PNG images with transparency are properly handled  
✅ **Position Control**: Place overlay at any corner with custom margins  
✅ **Backward Compatible**: Solid color patches still work as before  

## Basic Usage

### Option 1: Solid Color Patch (Default)

```python
from math_tutor.process_video import remove_watermark_from_video

# Cover watermark with white patch
result = remove_watermark_from_video(
    video_input="input_video.mp4",
    output_path="output.mp4",
    patch_width=400,
    patch_height=100,
    patch_color=(255, 255, 255),  # White
    position="bottom-right"
)
```

### Option 2: Custom Image Overlay (New!)

```python
from math_tutor.process_video import remove_watermark_from_video

# Cover watermark with your logo
result = remove_watermark_from_video(
    video_input="input_video.mp4",
    output_path="branded_video.mp4",
    patch_width=400,
    patch_height=100,
    position="bottom-right",
    overlay_image="my_logo.png"  # Local image file
)
```

### Option 3: Image from URL

```python
from math_tutor.process_video import remove_watermark_from_video

# Cover watermark with image downloaded from URL
result = remove_watermark_from_video(
    video_input="https://example.com/video.mp4",
    output_path="branded_video.mp4",
    patch_width=300,
    patch_height=80,
    position="bottom-left",
    margin_x=10,
    margin_y=10,
    overlay_image="https://example.com/watermark.png"  # Image URL
)
```

## Parameters Reference

### `remove_watermark_from_video()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_input` | str | *Required* | Path or URL to input video |
| `output_path` | str | `None` | Path for output video (auto-generated if None) |
| `patch_width` | int | `400` | Width of overlay area in pixels |
| `patch_height` | int | `100` | Height of overlay area in pixels |
| `patch_color` | tuple | `(255,255,255)` | RGB color (used only if no `overlay_image`) |
| `position` | str | `"bottom-right"` | Position: `"bottom-right"`, `"bottom-left"`, `"top-right"`, `"top-left"` |
| `margin_x` | int | `0` | Horizontal margin from edge in pixels |
| `margin_y` | int | `0` | Vertical margin from edge in pixels |
| `overlay_image` | str | `None` | Path or URL to overlay image (PNG/JPG/GIF/WEBP) |

## Position Options

```
┌─────────────────────────┐
│ top-left    top-right   │
│                         │
│                         │
│                         │
│ bottom-left bottom-right│
└─────────────────────────┘
```

### With Margins

```python
# Place logo 10px from bottom and 20px from right
remove_watermark_from_video(
    video_input="video.mp4",
    output_path="output.mp4",
    position="bottom-right",
    margin_x=20,  # 20px from right edge
    margin_y=10,  # 10px from bottom edge
    overlay_image="logo.png"
)
```

## Image Format Recommendations

### Best Practices

1. **PNG with Transparency** (Recommended)
   - Supports transparent backgrounds
   - Best for logos and branding
   - Clean edges and alpha blending

2. **JPG for Photos**
   - Good for photographic overlays
   - No transparency support
   - Smaller file sizes

3. **Size Considerations**
   - Images are automatically resized to `patch_width` x `patch_height`
   - Maintain aspect ratio in your design if possible
   - Typical sizes: 300x80, 400x100, 500x120

### Creating Overlay Images

**Example Logo Dimensions:**
```
Small:  300 x 80  pixels
Medium: 400 x 100 pixels
Large:  500 x 120 pixels
```

**Recommended Tools:**
- Adobe Photoshop
- GIMP (free)
- Canva
- Figma
- Any image editor supporting PNG with transparency

## Complete Workflow Examples

### Example 1: Generate Video + Custom Branding

```python
from math_tutor.math_ai_video_generator import generate_math_ai_video
from math_tutor.process_video import remove_watermark_from_video

# Step 1: Generate AI video
result = generate_math_ai_video(
    math_problem="Solve: x^2 + 5x + 6 = 0",
    remove_watermark=False  # We'll process manually
)

video_url = result['video_link']

# Step 2: Add custom branding
branded_video = remove_watermark_from_video(
    video_input=video_url,
    output_path="math_tutorial_branded.mp4",
    patch_width=400,
    patch_height=100,
    position="bottom-right",
    overlay_image="company_logo.png"  # Your branding!
)

print(f"Branded video saved to: {branded_video}")
```

### Example 2: Batch Processing with Different Logos

```python
from math_tutor.process_video import remove_watermark_from_video
import os

videos = ["video1.mp4", "video2.mp4", "video3.mp4"]
logos = {
    "Math Channel": "math_logo.png",
    "Science Channel": "science_logo.png",
    "Default": "generic_logo.png"
}

for video in videos:
    # Determine which logo to use
    logo = logos.get("Math Channel", logos["Default"])
    
    # Process video
    output = f"branded_{video}"
    remove_watermark_from_video(
        video_input=video,
        output_path=output,
        overlay_image=logo,
        patch_width=400,
        patch_height=100,
        position="bottom-right"
    )
    
    print(f"✅ Processed: {video} -> {output}")
```

### Example 3: Multi-Position Overlays

```python
# Add multiple overlays (run sequentially)
from math_tutor.process_video import remove_watermark_from_video

# First: Remove watermark at bottom-right
step1 = remove_watermark_from_video(
    video_input="original.mp4",
    output_path="temp_step1.mp4",
    position="bottom-right",
    overlay_image="logo.png"
)

# Second: Add branding at top-left
final = remove_watermark_from_video(
    video_input="temp_step1.mp4",
    output_path="final_branded.mp4",
    position="top-left",
    margin_x=10,
    margin_y=10,
    overlay_image="watermark.png"
)
```

## Testing

### Run the Test Suite

```bash
# Test with local files
python testing/test_image_overlay.py

# Or run the interactive demo
python demo_automated_video.py
# Choose option 3: Custom image overlay
```

### Manual Testing Checklist

- [ ] Test with local PNG file (with transparency)
- [ ] Test with local JPG file
- [ ] Test with image URL
- [ ] Test all 4 position options
- [ ] Test with custom margins
- [ ] Test with different image sizes
- [ ] Verify fallback to color patch when no image provided
- [ ] Check temp file cleanup (no leftover files)

## Troubleshooting

### Common Issues

**Issue**: `Image file not found`
```python
# Solution: Use absolute path
import os
image_path = os.path.abspath("logo.png")
```

**Issue**: `Failed to download image`
```python
# Solution: Check URL is accessible
# Test URL in browser first
# Ensure image format is supported (PNG/JPG/GIF/WEBP)
```

**Issue**: `Image appears stretched or distorted`
```python
# Solution: Match aspect ratio
# If your logo is 2:1 ratio, use dimensions like:
patch_width=400
patch_height=200  # Maintains 2:1 ratio
```

**Issue**: `MoviePy import error`
```bash
# Solution: Install MoviePy
pip install moviepy

# If still failing, try:
pip install moviepy[optional]
```

**Issue**: `Transparency not working`
```python
# Solution: Ensure you're using PNG format
# JPG does not support transparency
# Save your image as PNG with alpha channel
```

## Performance Tips

1. **Pre-resize Images**: Resize your images to target dimensions before using
2. **Use Compressed Formats**: JPG for photos, optimized PNG for graphics
3. **Local Files**: Use local files when possible (faster than downloading)
4. **Batch Processing**: Process multiple videos in parallel if possible

## Dependencies

```bash
# Required
pip install moviepy

# Optional (for better image handling)
pip install pillow
```

## API Integration

### Using with Flask API

```python
# In your route handler
from flask import request, jsonify
from math_tutor.process_video import remove_watermark_from_video

@app.route('/api/brand-video', methods=['POST'])
def brand_video():
    data = request.json
    
    result = remove_watermark_from_video(
        video_input=data['video_url'],
        output_path=f"outputs/{data['output_filename']}",
        overlay_image=data.get('logo_url'),
        patch_width=data.get('width', 400),
        patch_height=data.get('height', 100),
        position=data.get('position', 'bottom-right')
    )
    
    return jsonify({
        'status': 'success',
        'output_path': result
    })
```

## Advanced Usage

### Dynamic Logo Selection

```python
def get_logo_for_category(category):
    """Select logo based on content category"""
    logos = {
        'math': 'logos/math_logo.png',
        'science': 'logos/science_logo.png',
        'history': 'logos/history_logo.png',
    }
    return logos.get(category, 'logos/default_logo.png')

# Use in processing
category = "math"
logo = get_logo_for_category(category)

remove_watermark_from_video(
    video_input="tutorial.mp4",
    output_path="branded_tutorial.mp4",
    overlay_image=logo
)
```

### Conditional Branding

```python
def process_with_conditional_branding(video_url, user_tier):
    """Premium users get logo, free users get color patch"""
    
    if user_tier == "premium":
        # Premium: Custom logo
        overlay = "premium_logo.png"
    elif user_tier == "basic":
        # Basic: Simple branded patch
        overlay = "basic_logo.png"
    else:
        # Free: No logo, just white patch
        overlay = None
    
    return remove_watermark_from_video(
        video_input=video_url,
        output_path=f"{user_tier}_video.mp4",
        overlay_image=overlay
    )
```

## License & Attribution

When using custom overlays:
- Ensure you have rights to the logo/image
- Respect original video creator's terms
- Consider adding attribution if required

---

## Quick Reference

```python
# Minimal Example
from math_tutor.process_video import remove_watermark_from_video

# With image overlay
remove_watermark_from_video(
    "input.mp4", 
    "output.mp4", 
    overlay_image="logo.png"
)

# With color patch (no image)
remove_watermark_from_video(
    "input.mp4", 
    "output.mp4"
)
```

## Support

For issues or questions:
1. Check this guide first
2. Run test suite: `python testing/test_image_overlay.py`
3. Check MoviePy documentation for video processing issues
4. Verify image format is supported (PNG/JPG/GIF/WEBP)

---

**Last Updated**: 2024
**Feature Version**: 2.0 (Image Overlay Support)
