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

    # Add some basic styling for code blocks
    for code in soup.find_all("code"):
        if not code.parent or code.parent.name != "pre":
            # Inline code - add subtle background
            code["style"] = (
                "background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; font-family: monospace;"
            )

    for pre in soup.find_all("pre"):
        # Block code - add styling
        pre["style"] = (
            "background-color: #f6f8fa; padding: 16px; border-radius: 6px; overflow-x: auto; font-family: monospace;"
        )

    # Save HTML
    output_file.write_text(str(soup), encoding="utf-8")

    print("\n✅ Conversion complete!")
    print(f"📝 Output: {output_file}")
    print(f"🖼️  Updated {image_count} image URL(s)")
    print("\n📋 Next steps:")
    print(f"   1. Open {output_file}")
    print("   2. Copy the HTML content")
    print("   3. Paste into Substack editor (HTML mode: Cmd+Shift+H)")
    print("   4. Review and publish!")

    return 0


if __name__ == "__main__":
    exit(convert_to_substack())
