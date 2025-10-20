#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "markdown",
#     "beautifulsoup4",
# ]
# ///
"""Convert Substack post from Markdown to HTML with GitHub-hosted images.

This script:
1. Reads docs/substack/post.md
2. Converts to HTML
3. Updates image URLs to use GitHub raw URLs
4. Saves to docs/substack/post.html

Run with: uv run tools/convert_to_substack.py
"""

import markdown
from pathlib import Path
from bs4 import BeautifulSoup


def convert_to_substack():
    """Convert markdown post to Substack-ready HTML."""

    # Paths
    project_root = Path(__file__).parent.parent
    md_file = project_root / "docs" / "substack" / "post.md"
    output_file = project_root / "docs" / "substack" / "post.html"

    if not md_file.exists():
        print(f"❌ Source file not found: {md_file}")
        return 1

    # Read markdown
    print(f"📖 Reading: {md_file}")
    content = md_file.read_text()

    # Pre-process: Convert relative image paths in HTML tags before markdown conversion
    content = content.replace('src="../images/', 'src="docs/images/')

    # Convert to HTML
    print("🔄 Converting Markdown to HTML...")
    html = markdown.markdown(
        content, extensions=["fenced_code", "tables", "nl2br"], output_format="html5"
    )

    # Parse and enhance HTML
    soup = BeautifulSoup(html, "html.parser")

    # Convert relative image paths to absolute GitHub URLs
    base_url = "https://raw.githubusercontent.com/okigan/revproxauth/main/"
    image_count = 0

    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src.startswith("docs/"):
            img["src"] = base_url + src
            image_count += 1
            print(f"  ✓ Updated image: {src} → {img['src']}")
        elif src.startswith("../images/"):
            # Handle relative paths from docs/substack/
            clean_path = "docs/" + src.replace("../images/", "images/")
            img["src"] = base_url + clean_path
            image_count += 1
            print(f"  ✓ Updated image: {src} → {img['src']}")

    # Remove any style attributes - let Substack handle styling
    for tag in soup.find_all(True):
        if tag.has_attr("style"):
            del tag["style"]

    # Simplify code blocks - remove inline styles that confuse Substack
    # Substack will apply its own styling to <code> and <pre> tags

    # Save HTML
    output_file.write_text(str(soup), encoding="utf-8")

    print("\n✅ Conversion complete!")
    print(f"📝 Output: {output_file}")
    print(f"🖼️  Updated {image_count} image URL(s)")
    print("\n📋 Next steps:")
    print(f"   1. Open {output_file} in a web browser")
    print("   2. Select all (Cmd+A) and copy (Cmd+C)")
    print("   3. Go to Substack and create a new post")
    print("   4. Add the title manually")
    print("   5. Paste into the post body - Substack will format it!")
    print("   6. Review and publish!")
    print(
        "\nNote: The HTML is now clean without inline styles for better Substack compatibility"
    )

    return 0


if __name__ == "__main__":
    exit(convert_to_substack())
