#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Notify that Substack publishing must be done manually.

Substack's Cloudflare protection makes automated publishing unreliable.
This script confirms that HTML content is ready and provides instructions.
"""

import os
import sys
from pathlib import Path


def main():
    """Main entry point - display manual publishing instructions."""
    project_root = Path(__file__).parent.parent
    html_file = project_root / "docs" / "substack" / "post.html"

    if not html_file.exists():
        print(f"❌ Post HTML not found: {html_file}")
        print("Make sure the prepare-content job has run first!")
        sys.exit(1)

    publish_mode = os.getenv("PUBLISH_MODE", "draft")

    print("\n" + "=" * 70)
    print("📝 SUBSTACK PUBLISHING - MANUAL STEPS REQUIRED")
    print("=" * 70)
    print()
    print("⚠️  Automated publishing is blocked by Cloudflare protection.")
    print(f"📄 HTML content ready at: {html_file}")
    print(f"📤 Mode: {publish_mode.upper()}")
    print()
    print("=" * 70)
    print("HOW TO PUBLISH:")
    print("=" * 70)
    print()
    print("1. Download workflow artifacts containing post.html")
    print("2. Open post.html and copy ALL the HTML content")
    print("3. Go to: https://[your-substack].substack.com/publish")
    print("4. Click 'New post'")
    print("5. Add title: 'How a 1991 Protocol Guards My Privately Hosted LLM'")
    print("6. Add subtitle (optional)")
    print("7. Press Cmd+Shift+H (Mac) or Ctrl+Shift+H (Win) for HTML mode")
    print("8. Paste the HTML content")
    print("9. Review the formatted post")
    if publish_mode == "publish":
        print("10. Click 'Publish' and confirm")
    else:
        print("10. Click 'Save' to save as draft")
    print()
    print("=" * 70)
    print("✅ Content is ready!")
    print("=" * 70)


if __name__ == "__main__":
    main()
