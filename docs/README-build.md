# Regenerating the setup guide

The setup guide is built from `docs/setup-guide.md` using a uv script that outputs to `docs/setup-guide.html`.

## Architecture

- **Source**: `docs/setup-guide.md` - Markdown content with H2 headings as slides
- **Template**: `docs/_template.html` - HTML carousel structure with `{{SLIDES}}` placeholder
- **Build**: `tools/build_guide.py` - uv script with inline dependencies
- **Output**: `docs/setup-guide.html` - Generated file (do not edit manually)

## Prerequisites

Install `uv` if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Build the guide

```bash
make build-guide
```

Or run directly:

```bash
uv run tools/build_guide.py
```

The script uses inline dependencies (PEP 723 style) and uv will automatically install `markdown` and `beautifulsoup4` in an isolated environment.

## Adding images to slides

To add an image to a slide, use standard markdown image syntax anywhere in the section:

```markdown
## 1. Install RADIUS Server

Description text here...

![Image description](images/screenshot.png)

More content...
```

The build script will:
- Detect the image and display it on the slide
- Use a placeholder icon (🖼️) if no image is provided

Images should be placed in `docs/images/` directory.

## Output

The generated file is `docs/setup-guide.html` - this file is generated from the template and should not be edited manually. Make all changes in `docs/setup-guide.md` instead.

## Previewing

```bash
make serve-guide
```

Then open http://localhost:8000/setup-guide.html in your browser.
