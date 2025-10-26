# Transcript Management Scripts

This directory contains scripts for managing, converting, and validating transcripts for Gary's Economics.

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

## process_video.py

This script downloads VTT caption files for a specific YouTube video and creates a corresponding Jekyll post file.

### What it does:

1. Takes a YouTube video ID as a command-line argument
2. Downloads video metadata using yt-dlp
3. Downloads all available English VTT subtitle files (manual or auto-generated)
4. Copies VTT files to `_includes/captions/` named by YouTube ID
5. Creates a Jekyll post markdown file in `_posts/` with YAML front matter

### Usage:

```bash
python3 scripts/process_video.py VIDEO_ID
```

For example, to process a video with ID `Ja9dTjY3uWU`:

```bash
python3 scripts/process_video.py Ja9dTjY3uWU
```

The script will:
- Download video metadata from YouTube
- Download VTT subtitle files (prioritizes manual over auto-generated)
- Copy VTT files to `_includes/captions/VIDEO_ID.vtt`
- Create a post file in `_posts/YYYY-MM-DD-slug.md`
- Report progress and any issues encountered

### Output Format:

**Post files** (`_posts/YYYY-MM-DD-slug.md`):
- YAML front matter with complete metadata (title, date, youtube_id, view_count, like_count, tags, categories, description, etc.)
- Properly escaped titles and descriptions for YAML compatibility
- Reference to caption file

**Caption files** (`_includes/captions/YOUTUBE_ID.vtt`):
- WebVTT format subtitle files
- Named by YouTube video ID
- Additional language variants named as `YOUTUBE_ID.lang.vtt` if available

### Notes:

- Requires yt-dlp to be installed (`pip install yt-dlp`)
- Will not overwrite existing post or caption files
- Prioritizes manual subtitles over auto-generated ones
- Downloads English subtitles in order of preference: en-GB, en-orig, en
- The script requires Python 3.6+

## linter.py

This script validates consistency between `_posts` and `_includes/captions` directories.

### What it does:

1. Scans all VTT files in `_includes/captions/`
2. Scans all post files in `_posts/`
3. Verifies that each VTT file has a corresponding post with matching YouTube ID
4. Verifies that each post has at least one corresponding VTT file
5. Reports any inconsistencies or missing files

### Usage:

```bash
python3 scripts/linter.py
```

The script will:
- Check all VTT files have corresponding posts
- Check all posts have corresponding VTT files
- Report posts with multiple VTT language variants
- Provide a summary of findings

### Output:

The linter will report:
- Number of unique YouTube IDs with VTT files
- Number of posts with YouTube IDs
- Any VTT files without corresponding posts (errors)
- Any posts without corresponding VTT files (errors)
- Posts with multiple VTT language variants (informational)

### Exit Codes:

- `0`: All checks passed
- `1`: Errors found or exception occurred

### Notes:

- Should be run after adding new content to verify consistency
- Useful for CI/CD pipelines to ensure data integrity
- The script requires Python 3.6+
