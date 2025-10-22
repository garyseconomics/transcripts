# Transcript Conversion Scripts

This directory contains scripts for managing and converting transcripts for Gary's Economics.

## convert_transcripts.py

This script converts transcript data from the `./transcripts` folder into the Jekyll format used by `_posts` and `_includes/captions`.

### What it does:

1. Reads all folders in `./transcripts/`
2. Extracts metadata from `meta.json` files
3. Generates Jekyll post markdown files in `_posts/` with YAML front matter
4. Copies `transcript.vtt` files to `_includes/captions/` named by YouTube ID

### Usage:

```bash
python3 scripts/convert_transcripts.py
```

The script will:
- Process all transcript folders
- Skip folders that already have corresponding posts
- Report progress for each conversion
- Provide a summary at the end

### Output Format:

**Post files** (`_posts/YYYY-MM-DD-slug.md`):
- YAML front matter with metadata (title, date, youtube_id, etc.)
- Title and descriptions properly escaped for YAML
- Tags and categories as lists
- Reference to caption file

**Caption files** (`_includes/captions/YOUTUBE_ID.vtt`):
- WebVTT format subtitle files
- Named by YouTube video ID for easy reference

### Notes:

- The script will not overwrite existing posts (by design)
- Special characters in titles and descriptions are properly escaped
- Multi-line descriptions use YAML literal block scalar format
- The script requires Python 3.6+
