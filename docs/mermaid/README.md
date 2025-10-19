# Mermaid Diagram Sources

This directory contains Mermaid diagram source files (`.mmd`) that are converted to PNG images for the Substack article and documentation.

## Files

- `problem-diagram.mmd` - Shows the insecure port forwarding problem
- `solution-diagram.mmd` - Shows the complete architecture with RADIUS authentication

## Editing Diagrams

1. Edit the `.mmd` files directly in this directory
2. Use standard Mermaid syntax (see [Mermaid documentation](https://mermaid.js.org/))
3. Run `uv run tools/generate_mermaid_diagrams.py` to regenerate PNG files
4. PNG files are saved to `docs/images/` with matching names

## Adding New Diagrams

1. Create a new `.mmd` file in this directory (e.g., `my-diagram.mmd`)
2. Add your Mermaid code
3. Run `uv run tools/generate_mermaid_diagrams.py`
4. A `my-diagram.png` will be generated in `docs/images/`
5. Reference it in markdown: `![Description](docs/images/my-diagram.png)`

## Testing Diagrams

You can preview Mermaid diagrams using:
- [Mermaid Live Editor](https://mermaid.live/)
- VS Code with the Mermaid extension
- Any markdown preview that supports Mermaid

## Supported Diagram Types

The script supports all Mermaid diagram types:
- Flowcharts (`graph`, `flowchart`)
- Sequence diagrams (`sequenceDiagram`)
- Class diagrams (`classDiagram`)
- State diagrams (`stateDiagram`)
- Entity relationship diagrams (`erDiagram`)
- And more...
