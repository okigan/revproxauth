# Tools

Utility scripts for the revproxauth project.

## Generating Mermaid Diagrams

The `generate_mermaid_diagrams.py` script converts Mermaid diagram definitions to PNG images for use in the Substack article and documentation.

### Usage

```bash
# Run with uv (automatically installs dependencies)
uv run tools/generate_mermaid_diagrams.py
```

### Output

Generated PNG files are saved to `docs/images/`:
- `problem-diagram.png` - Shows the insecure port forwarding problem
- `solution-diagram.png` - Shows the complete architecture with RADIUS auth

### Updating Diagrams

1. Edit Mermaid files in `docs/mermaid/` (e.g., `problem-diagram.mmd`)
2. Or create new `.mmd` files in that directory
3. Run the script: `uv run tools/generate_mermaid_diagrams.py`
4. PNG files with matching names will be generated in `docs/images/`
5. Commit both the `.mmd` source files and generated PNG files

### Dependencies

The script uses:
- `playwright` - For headless browser automation to render Mermaid diagrams
- Mermaid.js (loaded via CDN in the HTML)

The script header includes inline dependency metadata for `uv`, so dependencies are automatically managed.

## Other Scripts

- `build_guide.py` - Generates documentation from markdown
- `create_homelab_diagram.py` - Creates architecture diagrams using the diagrams library
- `generate_homelab_diagram.py` - Alternative diagram generation script
