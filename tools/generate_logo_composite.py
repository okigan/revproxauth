#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pillow",
# ]
# ///
"""Generate a composite image of technology logos.

This script:
1. Reads individual logo images from docs/images/vendor/logos/
2. Composes them into a single horizontal banner
3. Saves to docs/images/tech-stack.png

Run with: uv run tools/generate_logo_composite.py
"""

from pathlib import Path
from PIL import Image


def create_logo_composite():
    """Create a composite image of technology logos."""

    project_root = Path(__file__).parent.parent
    logos_dir = project_root / "docs" / "images" / "vendor" / "logos"
    output_file = project_root / "docs" / "images" / "tech-stack.png"

    # Logo files in order
    logo_files = ["synology.png", "unifi.png", "llama.png", "python.png", "docker.png"]

    # Target height for all logos
    target_height = 100
    spacing = 20  # pixels between logos
    padding = 10  # padding around the composite

    print("📸 Loading and resizing logos...")
    images = []
    for logo_file in logo_files:
        logo_path = logos_dir / logo_file
        if not logo_path.exists():
            print(f"❌ Logo not found: {logo_path}")
            return 1

        img = Image.open(logo_path)
        # Convert to RGBA if needed
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Calculate new width to maintain aspect ratio
        aspect_ratio = img.width / img.height
        new_width = int(target_height * aspect_ratio)

        # Resize with high-quality resampling
        resized = img.resize((new_width, target_height), Image.Resampling.LANCZOS)
        images.append(resized)
        print(
            f"  ✓ Loaded {logo_file}: {img.width}x{img.height} → {new_width}x{target_height}"
        )

    # Calculate total width
    total_width = (
        sum(img.width for img in images) + spacing * (len(images) - 1) + 2 * padding
    )
    total_height = target_height + 2 * padding

    print(f"\n🎨 Creating composite image: {total_width}x{total_height}...")

    # Create white background
    composite = Image.new("RGBA", (total_width, total_height), (255, 255, 255, 255))

    # Paste logos
    x_offset = padding
    for img in images:
        # Center vertically
        y_offset = padding + (target_height - img.height) // 2
        composite.paste(img, (x_offset, y_offset), img)
        x_offset += img.width + spacing

    # Save as PNG
    output_file.parent.mkdir(parents=True, exist_ok=True)
    composite.save(output_file, "PNG", optimize=True)

    print("\n✅ Composite image saved!")
    print(f"📝 Output: {output_file}")
    print(f"📐 Size: {total_width}x{total_height}px")

    return 0


if __name__ == "__main__":
    exit(create_logo_composite())
