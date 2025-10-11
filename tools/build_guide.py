#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "markdown",
#     "beautifulsoup4",
# ]
# ///

"""
Build the setup guide HTML from markdown source.

This script converts docs/setup-guide.md into docs/setup-guide.html
using a carousel-based template.
"""

import sys
from pathlib import Path

import markdown
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
MD_FILE = ROOT / "docs" / "setup-guide.md"
TEMPLATE = ROOT / "docs" / "_template.html"
OUT_FILE = ROOT / "docs" / "setup-guide.html"


def main():
    if not MD_FILE.exists():
        print(f"Markdown source not found: {MD_FILE}", file=sys.stderr)
        sys.exit(1)

    if not TEMPLATE.exists():
        print(f"Template not found: {TEMPLATE}", file=sys.stderr)
        sys.exit(1)

    md_text = MD_FILE.read_text(encoding="utf-8")
    html_body = markdown.markdown(md_text, extensions=["fenced_code", "tables"])

    # Read template and find the slides placeholder
    template = TEMPLATE.read_text(encoding="utf-8")

    soup = BeautifulSoup(html_body, "html.parser")

    slides_html = []
    # For each H2 (which corresponds to steps in our markdown), create a carousel-slide
    headings = soup.find_all("h2")
    for idx, section in enumerate(headings, 1):
        title = section.get_text()
        # Extract step number if present (e.g., "1. Install RADIUS Server" -> "1")
        step_num = str(idx)
        if title and title[0].isdigit():
            # Extract the number at the start
            step_num = title.split(".")[0].strip()
            # Remove the number from title for display
            title_parts = title.split(".", 1)
            if len(title_parts) > 1:
                title = title_parts[1].strip()

        elems = []
        image_html = ""
        for sib in section.next_siblings:
            # stop at the next header
            if getattr(sib, "name", None) in ("h1", "h2"):
                break
            # Check if this is an img tag
            if getattr(sib, "name", None) == "p":
                img_tag = sib.find("img")
                if img_tag and img_tag.get("src"):
                    # Found an image - use it instead of placeholder
                    img_src = img_tag.get("src")
                    img_alt = img_tag.get("alt", title)
                    image_html = f'<img src="{img_src}" alt="{img_alt}" class="slide-image" />'
                    continue  # Don't add the img paragraph to body content
            elems.append(str(sib))
        body_html = "\n".join(elems).strip()

        # Build image container - use real image if found, otherwise placeholder
        if image_html:
            image_container = f"""<div class="slide-image-container">
                            {image_html}
                        </div>"""
        else:
            image_container = f"""<div class="slide-image-container">
                            <div class="image-placeholder">
                                <div class="image-placeholder-icon">🖼️</div>
                                <div class="image-placeholder-text">Screenshot: {title}</div>
                            </div>
                        </div>"""

        slide = f"""                    <div class="carousel-slide">
                        <div class="step-number">{step_num}</div>
                        <h2 class="slide-title">{title}</h2>
                        <div class="slide-description">{body_html}</div>
                        {image_container}
                    </div>"""
        slides_html.append(slide)

    # Replace {{SLIDES}} placeholder in template
    slides_block = "\n".join(slides_html)
    output = template.replace("{{SLIDES}}", slides_block)

    OUT_FILE.write_text(output, encoding="utf-8")
    print(f"Generated: {OUT_FILE}")


if __name__ == "__main__":
    main()
