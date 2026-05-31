# Contributing to 二舅妈急了

Thanks for helping improve this media-literacy satire tool.

## Good First Contributions

- Documentation improvements in Chinese or English.
- Safer prompt wording.
- Better safety filters for high-risk topics.
- UI fixes for mobile browsers.
- Tests for parsing, safety filtering, and output warnings.
- Deployment notes for local-only or private-family use.

## Development

```bash
cd 源码/后端
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python main.py
```

Run basic checks:

```bash
python -m compileall .
ruff check .
pytest
```

## Pull Requests

1. Keep each pull request focused.
2. Explain the safety impact of the change.
3. Do not remove satire labels, warning text, or watermarks.
4. Include screenshots for UI changes.
5. Do not commit `.env`, API keys, generated private content, or family-chat screenshots.

## Safety Boundary

This project is for media-literacy education. Contributions that make it easier to produce unmarked misinformation, harassment, or political manipulation will not be accepted.
