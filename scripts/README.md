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

## review_transcript.py

Applies systematic corrections to a raw VTT transcript and produces a clean SRT file. This handles the mechanical cleanup that every transcript needs — the AI reviewer then reads through to fix context-dependent errors, add punctuation, and add speaker labels.

### What it does:

1. Parses auto-generated VTT captions (deduplicates the echo-cue format)
2. Fixes known garbled words (e.g., "lsc" → "LSE", "seat bank" → "Citibank")
3. Applies British English corrections ("realized" → "realised", "math" → "maths")
4. Capitalises proper nouns (Bank of England, Wall Street, Piketty, etc.)
5. Removes filler words ("um", "uh") and fixes stuttered repetitions
6. Capitalises "I" and contractions throughout
7. Converts currency ("45 pounds" → "£45")
8. Outputs a numbered SRT file

### Usage:

```bash
python3 scripts/review_transcript.py <transcript_folder_name>
python3 scripts/review_transcript.py 2020-08-22-i-made-millions-...
python3 scripts/review_transcript.py 2020-08-22-i-made-millions-... --dry-run
python3 scripts/review_transcript.py 2020-08-22-i-made-millions-... -o custom/path.srt
```

### After running:

The AI reviewer still needs to:
- Read through for context-dependent garbled words (names, phrasing)
- Add punctuation (periods, commas, question marks)
- Add speaker labels for multi-speaker videos and move to `multi_speaker/`
- Remove end-of-video fragments
- Update `revisions/TRANSCRIPT_STATUS.md`

## generate_corrections_doc.py

Generates a corrections document (.md) for volunteer review by comparing the reviewed SRT with the original VTT.

### What it does:

1. Finds the matching source VTT via the YouTube ID in the SRT filename
2. Parses both the original VTT and the reviewed SRT
3. Aligns cues by timestamp and computes word-level diffs
4. Groups cues into flowing paragraphs with timestamps
5. Marks changes: **bold** for additions/corrections, ~~strikethrough~~ for removals
6. Outputs an `.md` file to `revisions/2_To_be_reviewed_by_volunteers/`

### Usage:

```bash
python3 scripts/generate_corrections_doc.py <path_to_reviewed_srt>
python3 scripts/generate_corrections_doc.py revisions/1_AI_reviewed/FvOa5EmckHE__2020-08-22_....srt
python3 scripts/generate_corrections_doc.py revisions/1_AI_reviewed/multi_speaker/FvOa5EmckHE__....srt
```

### Notes:

- The SRT filename must follow the `youtubeID__date_Title.srt` format
- The script automatically looks up the source VTT by YouTube ID
- Paragraph breaks occur at speaker changes, sentence boundaries, time gaps, or word-count limits
- Punctuation-only changes are not bolded (as per CLAUDE.md instructions)
