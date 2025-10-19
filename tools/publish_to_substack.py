#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-substack",
#     "markdown",
#     "beautifulsoup4",
# ]
# ///
"""Publish to Substack using the python-substack API library.

This script uses the unofficial python-substack library:
https://github.com/ma2za/python-substack

Requires environment variables:
- SUBSTACK_EMAIL: Your Substack account email
- SUBSTACK_PASSWORD: Your Substack account password

Run with: uv run tools/publish_to_substack.py
"""

import os
import sys
from pathlib import Path
import markdown
from bs4 import BeautifulSoup
from substack import Api
from substack.post import Post


def load_post_markdown():
    """Load the markdown post content."""
    project_root = Path(__file__).parent.parent
    md_file = project_root / "docs" / "substack" / "post.md"

    if not md_file.exists():
        print(f"❌ Post not found: {md_file}")
        sys.exit(1)

    return md_file.read_text()


def parse_markdown_to_substack_format(md_content: str) -> list:
    """Parse markdown content and convert to Substack post format.

    Converts markdown to HTML first, then parses into Substack's content blocks.
    """
    # Convert markdown to HTML for easier parsing
    html = markdown.markdown(md_content, extensions=["fenced_code", "tables", "nl2br"])

    soup = BeautifulSoup(html, "html.parser")
    base_url = "https://raw.githubusercontent.com/okigan/revproxauth/main/"

    content_blocks = []

    for element in soup.children:
        if not hasattr(element, "name"):
            continue

        # Paragraphs
        if element.name == "p":
            text_content = []
            for child in element.children:
                if hasattr(child, "name"):
                    if child.name == "strong":
                        text_content.append(
                            {"content": child.get_text(), "marks": [{"type": "strong"}]}
                        )
                    elif child.name == "em":
                        text_content.append(
                            {"content": child.get_text(), "marks": [{"type": "em"}]}
                        )
                    elif child.name == "code":
                        text_content.append(
                            {"content": child.get_text(), "marks": [{"type": "code"}]}
                        )
                    elif child.name == "a":
                        text_content.append(
                            {
                                "content": child.get_text(),
                                "marks": [
                                    {"type": "link", "href": child.get("href", "")}
                                ],
                            }
                        )
                    elif child.name == "img":
                        # Images should be their own block
                        src = child.get("src", "")
                        if src.startswith("docs/"):
                            src = base_url + src
                        content_blocks.append({"type": "captionedImage", "src": src})
                        continue
                else:
                    text = str(child).strip()
                    if text:
                        text_content.append({"content": text})

            if text_content:
                if len(text_content) == 1 and isinstance(
                    text_content[0].get("content"), str
                ):
                    content_blocks.append(
                        {"type": "paragraph", "content": text_content[0]["content"]}
                    )
                else:
                    content_blocks.append(
                        {"type": "paragraph", "content": text_content}
                    )

        # Headers
        elif element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(element.name[1])
            content_blocks.append(
                {"type": "heading", "level": level, "content": element.get_text()}
            )

        # Images (standalone)
        elif element.name == "img":
            src = element.get("src", "")
            if src.startswith("docs/"):
                src = base_url + src
            content_blocks.append({"type": "captionedImage", "src": src})

        # Code blocks
        elif element.name == "pre":
            code = element.find("code")
            if code:
                content_blocks.append({"type": "code", "content": code.get_text()})

        # Lists
        elif element.name in ["ul", "ol"]:
            for li in element.find_all("li", recursive=False):
                content_blocks.append(
                    {"type": "paragraph", "content": f"• {li.get_text()}"}
                )

    return content_blocks


def publish_to_substack(post_content: list, title: str, subtitle: str = ""):
    """Publish content to Substack using the python-substack library."""

    # Get credentials from environment
    email = os.getenv("SUBSTACK_EMAIL")
    password = os.getenv("SUBSTACK_PASSWORD")

    if not email or not password:
        print("❌ Missing required environment variables:")
        print("   SUBSTACK_EMAIL - Your Substack account email")
        print("   SUBSTACK_PASSWORD - Your Substack account password")
        print("")
        print("Set a password if you don't have one:")
        print("   1. Sign out of Substack")
        print("   2. At sign-in page, click 'Sign in with password'")
        print("   3. Choose 'Set a new password'")
        sys.exit(1)

    print("🔐 Authenticating with Substack...")
    try:
        api = Api(email=email, password=password)
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        sys.exit(1)

    print("✓ Authenticated successfully")

    # Get user ID
    user_id = api.get_user_id()
    print(f"✓ User ID: {user_id}")

    # Get primary publication
    publication = api.get_user_primary_publication()
    print(f"✓ Publication: {publication.get('name', 'Unknown')}")

    # Create post
    print("\n� Creating post draft...")
    post = Post(title=title, subtitle=subtitle, user_id=user_id)

    # Add content blocks
    for block in post_content:
        post.add(block)

    # Create draft
    print("💾 Saving draft to Substack...")
    draft = api.post_draft(post.get_draft())
    draft_id = draft.get("id")

    print(f"✓ Draft created with ID: {draft_id}")

    # Pre-publish (validates the draft)
    print("🔍 Validating draft...")
    api.prepublish_draft(draft_id)
    print("✓ Draft validated")

    print("\n✅ Draft created successfully!")
    print(f"📝 Review your draft at: https://substack.com/publish/post/{draft_id}")
    print("\nTo publish, you can:")
    print("  1. Manually publish from the Substack web interface")
    print("  2. Or uncomment the api.publish_draft() line in this script")

    # Uncomment to automatically publish:
    # print("\n🚀 Publishing draft...")
    # api.publish_draft(draft_id)
    # print("✅ Post published!")


def main():
    """Main entry point."""
    print("🚀 Publishing to Substack using python-substack library")
    print("=" * 60)
    print()

    # Load markdown
    print("📖 Loading post...")
    md_content = load_post_markdown()

    # Parse content
    print("� Converting markdown to Substack format...")
    content_blocks = parse_markdown_to_substack_format(md_content)
    print(f"✓ Converted {len(content_blocks)} content blocks")

    # Publish
    title = "How a 1991 Protocol Guards My Privately Hosted LLM"
    subtitle = "I built a reverse proxy that reuses my existing RADIUS auth to guard self-hosted LLM and other web services"

    publish_to_substack(content_blocks, title, subtitle)

    print("\n✨ Done!")


if __name__ == "__main__":
    main()
