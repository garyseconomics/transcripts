# Transcript Conversion Scripts

This directory contains scripts for managing and converting transcripts for Gary's Economics.

## download.py

This script downloads YouTube video transcripts from the Gary's Economics channel and saves them in the `./transcripts` folder format with metadata and VTT files.

### What it does:

1. Fetches the list of all videos from the YouTube channel
2. For each video, downloads metadata (title, views, likes, etc.)
3. Downloads English subtitles (preferring manual subtitles over auto-generated)
4. Saves data to `./transcripts/YYYY-MM-DD-slug/` folders with:
   - `meta.json`: Video metadata
   - `transcript.vtt`: WebVTT subtitle file

### Usage:

```bash
python3 scripts/download.py [--offset N]
```

**Options:**
- `--offset N`: Start processing from video number N (useful for resuming interrupted downloads)

### Notes:

- Requires `yt-dlp` to be installed
- Skips videos that already have transcript folders
- Applies rate limiting (0.5s delay between videos) to avoid API restrictions
- Prefers subtitles in order: en-GB → en-orig → en
- Downloads both manual and auto-generated subtitles if manual are not available

## update.py

This script combines the functionality of `download.py` and `convert_transcripts.py`, downloading transcripts and directly creating Jekyll posts and VTT caption files. It also supports updating existing posts with current view counts and like counts.

### What it does:

1. Fetches the list of all videos from the YouTube channel
2. Identifies existing posts by reading all `youtube_id` values from `_posts/` files
3. For videos **not yet in the site**:
   - Downloads metadata and subtitles from YouTube
   - Creates Jekyll post in `_posts/` with YAML front matter
   - Copies VTT file to `_includes/captions/` named by YouTube ID
4. When using `--update` flag, for **all existing videos**:
   - Fetches current metadata from YouTube
   - Updates `view_count` and `like_count` in the corresponding `_posts/` file

### Usage:

```bash
# Download new videos and create posts
python3 scripts/update.py

# Update view and like counts for all existing posts
python3 scripts/update.py --update

# Start from a specific offset
python3 scripts/update.py --offset 50
```

**Options:**
- `--update`: Update existing posts with current view_count and like_count
- `--offset N`: Start processing from video number N

### Output Format:

**Post files** (`_posts/YYYY-MM-DD-slug.md`):
- YAML front matter with metadata (title, date, youtube_id, view_count, like_count, etc.)
- Title and descriptions properly escaped for YAML
- Tags and categories as lists
- Reference to caption file

**Caption files** (`_includes/captions/YOUTUBE_ID.vtt`):
- WebVTT format subtitle files
- Named by YouTube video ID for easy reference

### Notes:

- Requires `yt-dlp` to be installed
- Creates `_posts/` and `_includes/captions/` directories if they don't exist
- Special characters in titles and descriptions are properly escaped
- Multi-line descriptions use YAML literal block scalar format
- Applies rate limiting (0.5s delay between videos)
- In update mode, only fetches metadata (faster than full download)

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
