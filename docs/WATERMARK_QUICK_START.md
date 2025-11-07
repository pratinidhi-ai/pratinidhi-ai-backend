# Quick Start - Video Watermark Removal

## 🚀 Two Simple Options

### Option 1: White Patch (Simple & Fast)

```python
from math_tutor.process_video import remove_watermark_with_patch

remove_watermark_with_patch(
    video_input="my_video.mp4",
    output_path="clean_video.mp4"
)
```

### Option 2: Custom Logo (Professional)

```python
from math_tutor.process_video import remove_watermark_with_image

remove_watermark_with_image(
    video_input="my_video.mp4",
    overlay_image="my_logo.png",
    output_path="branded_video.mp4"
)
```

---

## 🎯 Choose Your Function

| I want to... | Use this function |
|--------------|-------------------|
| Cover watermark with white/black/color | `remove_watermark_with_patch()` |
| Add my logo/branding | `remove_watermark_with_image()` |

---

## 📖 Full Examples

### White Patch at Bottom-Right

```python
from math_tutor.process_video import remove_watermark_with_patch

remove_watermark_with_patch(
    video_input="tutorial.mp4",
    output_path="tutorial_clean.mp4",
    patch_width=400,           # 400 pixels wide
    patch_height=100,          # 100 pixels tall
    patch_color=(255, 255, 255),  # White color
    position="bottom-right"    # Bottom-right corner
)
```

### Logo Overlay at Bottom-Left

```python
from math_tutor.process_video import remove_watermark_with_image

remove_watermark_with_image(
    video_input="tutorial.mp4",
    overlay_image="company_logo.png",
    output_path="tutorial_branded.mp4",
    patch_width=300,           # Resize logo to 300px
    patch_height=80,           # Resize logo to 80px
    position="bottom-left",
    margin_x=10,              # 10px from left edge
    margin_y=10               # 10px from bottom edge
)
```

---

## 🎨 Color Options

```python
# White (default)
patch_color=(255, 255, 255)

# Black
patch_color=(0, 0, 0)

# Gray
patch_color=(128, 128, 128)

# Custom RGB
patch_color=(100, 150, 200)
```

---

## 📍 Position Options

```
┌──────────────────────┐
│ top-left  top-right  │
│                      │
│ bottom-left          │
│         bottom-right │
└──────────────────────┘
```

```python
position="bottom-right"  # Default
position="bottom-left"
position="top-right"
position="top-left"
```

---

## 🖼️ Supported Image Formats

- ✅ PNG (recommended - supports transparency)
- ✅ JPG
- ✅ GIF
- ✅ WEBP

---

## 🔗 Video from URL

Both functions support video URLs:

```python
# Patch
remove_watermark_with_patch(
    video_input="https://example.com/video.mp4",
    output_path="output.mp4"
)

# Image
remove_watermark_with_image(
    video_input="https://example.com/video.mp4",
    overlay_image="logo.png",
    output_path="output.mp4"
)
```

And image URLs too:

```python
remove_watermark_with_image(
    video_input="https://example.com/video.mp4",
    overlay_image="https://example.com/logo.png",
    output_path="output.mp4"
)
```

---

## 🧪 Try It Now

```bash
# Interactive demo with 4 options
python demo_automated_video.py
```

Choose:
1. Generate video + white patch removal
2. Generate video only
3. Custom image overlay (bring your own video URL)
4. White patch only (bring your own video URL)

---

## 📚 More Info

- **Full Guide**: `TWO_FUNCTIONS_GUIDE.md`
- **Image Overlay Details**: `IMAGE_OVERLAY_GUIDE.md`
- **Tests**: `testing/test_image_overlay.py`

---

## ❓ Quick Troubleshooting

**Q: Can I use both patch and image?**  
A: Not in one call. Run the function twice - first patch, then image on the output.

**Q: How do I adjust the size?**  
A: Use `patch_width` and `patch_height` parameters.

**Q: Can I use a transparent PNG?**  
A: Yes! Use `remove_watermark_with_image()` with a PNG file.

**Q: What if I want a different color?**  
A: Use `patch_color=(R, G, B)` with `remove_watermark_with_patch()`.

---

## ⚡ That's It!

You now have two simple functions:
- **`remove_watermark_with_patch()`** - for colors
- **`remove_watermark_with_image()`** - for images

Pick one and go! 🚀
