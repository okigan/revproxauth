#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "playwright",
# ]
# ///
"""Generate Mermaid diagrams as PNG files for the Substack article.

This script converts Mermaid diagram code to PNG images using Playwright.
It reads .mmd files from docs/mermaid/ and generates corresponding PNG files.

Run with: uv run tools/generate_mermaid_diagrams.py
"""

from pathlib import Path
from playwright.sync_api import sync_playwright


def generate_mermaid_png(mermaid_code: str, output_path: Path, scale: float = 2.0):
    """Generate a PNG from Mermaid code using Playwright."""

    # Create HTML with Mermaid
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({{ 
                startOnLoad: true,
                theme: 'default',
                securityLevel: 'loose'
            }});
        </script>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                background: white;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            .mermaid {{
                font-family: 'Arial', sans-serif;
            }}
        </style>
    </head>
    <body>
        <div class="mermaid">
{mermaid_code}
        </div>
    </body>
    </html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=scale)
        page.set_content(html_content)

        # Wait for Mermaid to render
        page.wait_for_timeout(2000)

        # Get the mermaid element and take screenshot
        element = page.query_selector(".mermaid svg")
        if element:
            element.screenshot(path=str(output_path))
            print(f"✓ Generated: {output_path}")
        else:
            print(f"✗ Failed to generate: {output_path}")

        browser.close()


def main():
    """Generate all Mermaid diagrams as PNG files."""
    project_root = Path(__file__).parent.parent
    mermaid_dir = project_root / "docs" / "mermaid"
    output_dir = project_root / "docs" / "images"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all .mmd files
    mermaid_files = list(mermaid_dir.glob("*.mmd"))

    if not mermaid_files:
        print(f"No .mmd files found in {mermaid_dir}")
        return

    print("Generating Mermaid diagrams...")
    print(f"Source directory: {mermaid_dir}")
    print(f"Output directory: {output_dir}")
    print()

    generated = []
    for mermaid_file in sorted(mermaid_files):
        # Read the Mermaid code
        mermaid_code = mermaid_file.read_text()

        # Generate output filename (replace .mmd with .png)
        output_path = output_dir / f"{mermaid_file.stem}.png"

        generate_mermaid_png(mermaid_code, output_path)
        generated.append(f"docs/images/{output_path.name}")

    print()
    print("Done! Generated diagrams:")
    for path in generated:
        print(f"  - {path}")


if __name__ == "__main__":
    main()
