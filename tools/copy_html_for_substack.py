#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Copy HTML to clipboard for pasting into Substack.

This script reads the generated HTML and copies it to your clipboard
so you can paste it directly into Substack in HTML mode.

Run with: uv run tools/copy_html_for_substack.py
"""

import subprocess
from pathlib import Path


def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard using pbcopy (macOS)."""
    try:
        process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, close_fds=True)
        process.communicate(input=text.encode("utf-8"))
        return process.returncode == 0
    except Exception as e:
        print(f"❌ Failed to copy to clipboard: {e}")
        return False


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    html_file = project_root / "docs" / "substack" / "post.html"

    if not html_file.exists():
        print(f"❌ HTML file not found: {html_file}")
        print("Run 'make substack-prepare' first!")
        return 1

    # Read HTML
    html_content = html_file.read_text()

    # Copy to clipboard
    print("📋 Copying HTML to clipboard...")
    if copy_to_clipboard(html_content):
        print("✅ HTML copied to clipboard!")
        print()
        print("📝 Next steps:")
        print("1. Go to: https://substack.com/publish")
        print("2. Click 'New post'")
        print("3. Add title: 'How a 1991 Protocol Guards My Privately Hosted LLM'")
        print("4. Press Cmd+Shift+H (Mac) or Ctrl+Shift+H (Win) to switch to HTML mode")
        print("5. Paste (Cmd+V) - the HTML is already in your clipboard!")
        print("6. Press Cmd+Shift+H again to switch back to visual mode")
        print("7. Review and publish!")
        return 0
    else:
        print("❌ Failed to copy to clipboard")
        print(f"💡 You can manually copy from: {html_file}")
        return 1


if __name__ == "__main__":
    exit(main())
