# Substack Article

This directory contains the Substack article.

## Files

- `post.md` - The article content in Markdown

## Publishing

### Automated (via GitHub Actions)

Uses [python-substack](https://github.com/ma2za/python-substack) library to publish via Substack's API:

1. **Set a Substack password** (if you don't have one):
   - Sign out → "Sign in with password" → "Set a new password"

2. **Add GitHub Secrets**:
   - `SUBSTACK_EMAIL` - Your Substack account email  
   - `SUBSTACK_PASSWORD` - Your Substack password

3. **Run workflow**: Actions → "Publish to Substack" → Select "publish"

### Local Publishing

```bash
export SUBSTACK_EMAIL="your@email.com"
export SUBSTACK_PASSWORD="your-password"
uv run tools/publish_to_substack.py
```

### Local Preview

```bash
# Generate HTML locally
uv run tools/convert_to_substack.py

# Output: docs/substack/post.html
```
