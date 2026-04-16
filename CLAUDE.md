# Transcript Review & Export

This project contains video transcripts from the YouTube channel **Gary's Economics**. The speaker is **Gary Stevenson**, a British former trader based in London who discusses economics, inequality, housing, and tax policy.

## Project goal

Produce reviewed, corrected versions of all transcripts in SRT format. The auto-generated VTT transcripts contain frequent errors (garbled words, mishearings, americanisms, dropped words). Each transcript needs to be reviewed and exported as a clean SRT file.

## Folder structure

- **`transcripts/`** — Auto-extracted transcripts. Each video has its own subfolder (named `YYYY-MM-DD-video-title`) containing a `transcript.vtt` and a `meta.json`.
- **`revisions/`** — All reviewed transcripts, organised by stage in the review pipeline. Filename format: `youtubeID__date_video_title.srt`.
  - **`revisions/0_agency_reviewed/`** — Transcripts reviewed by the agency. These serve as the gold standard for quality.
  - **`revisions/1_AI_reviewed/`** — AI-reviewed transcripts in SRT format. New AI-reviewed transcripts go here.
    - **`revisions/1_AI_reviewed/multi_speaker/`** — Transcripts with more than one speaker (e.g., interviews, panel appearances). These require human review to verify speaker identification.
  - **`revisions/2_To_be_reviewed_by_volunteers/`** — Corrections documents (`.md` files) for volunteers to review. This folder is shared with volunteers directly.
    - **`revisions/2_To_be_reviewed_by_volunteers/done/`** — Corrections documents that have already been reviewed by a volunteer. Moved here to avoid duplicate work.
  - **`revisions/3_volunteer_reviewed/`** — Transcripts that have been through both AI and volunteer review. These are ready for export.
  - **`revisions/TRANSCRIPT_STATUS.md`** — Tracks which transcripts have been reviewed and which are next. Consult this to find the next transcript to review.

## Review workflow

The full process for getting transcripts reviewed and into production:

1. **AI reviews the transcript** — The AI reviews the raw VTT transcript following the correction instructions below, producing a clean SRT file in `revisions/1_AI_reviewed/`.

2. **AI generates a corrections document** — The AI creates a `.md` file in `revisions/2_To_be_reviewed_by_volunteers/` with:
   - A link to the YouTube video at the top
   - The full transcript grouped into paragraphs of flowing text — **not** one line per cue
   - Each paragraph preceded by a single timestamp (`HH:MM:SS`) indicating where it starts in the video
   - Sentences are never split across paragraphs — keep whole sentences together, grouping by natural topic or paragraph breaks in the speech
   - Corrected or added **words** marked in bold, removed words in ~~strikethrough~~, unchanged text shown without markup
   - Do **not** bold added punctuation (commas, periods, etc.) — just insert it normally. Only bold word-level changes.
   - See `revisions/2_To_be_reviewed_by_volunteers/done/EiblHqbpXHs__2020-07-14_How_COVID-19_Makes_the_Rich_Richer.md` for an example.

3. **Volunteers review** — Volunteers watch the video, read along with the corrections document, and edit it where they spot issues. They send the edited file back (by email, most likely).

4. **AI incorporates volunteer revisions** — The volunteer's edited file is placed in `revisions/3_volunteer_reviewed/` (typically `.txt` or `.md`). The AI then:
   1. **Generates a changes review document** — Compares the volunteer's edits against the corrections document that was sent to them (in `revisions/2_To_be_reviewed_by_volunteers/done/`). Produces a `.md` file showing the final text with only the volunteer's changes highlighted: **bold** for additions, ~~strikethrough~~ for removals. This lets us visually check what the volunteer changed before applying anything.
      - Volunteer markup convention: `//added text//` = volunteer added this, `\\removed text\\` = volunteer removed this.
   2. **Applies approved changes to the SRT** — After the review document is checked, the AI applies the accepted volunteer changes to the AI-reviewed SRT (from `revisions/1_AI_reviewed/`), producing the final SRT in `revisions/3_volunteer_reviewed/`.

5. **Export to chatbot repo** — The final reviewed SRT is copied to [`garyseconomics/chatbot/docs/video_transcripts/to_be_imported`](https://github.com/garyseconomics/chatbot/tree/main/docs/video_transcripts/to_be_imported).

## Helper scripts

Two scripts in `scripts/` automate the mechanical parts of the review process. Run the first to get a head start on the SRT, then do manual corrections, then run the second to generate the volunteer document.

### Step 1: `scripts/review_transcript.py`

Parses a raw VTT, applies all systematic corrections (garbled words, British English, proper nouns, fillers, stutters, capitalisation), and outputs a clean SRT.

```bash
python3 scripts/review_transcript.py <transcript_folder_name>
python3 scripts/review_transcript.py 2020-08-22-i-made-millions-... --dry-run
```

The output SRT still needs manual work by the AI reviewer:
- Read through for **context-dependent garbled words** (names, phrasing that only makes sense in context)
- Add **punctuation** (periods, commas, question marks)
- Add **speaker labels** for multi-speaker videos and move the file to `multi_speaker/`
- Remove **end-of-video fragments**
- Update `revisions/TRANSCRIPT_STATUS.md`

### Step 2: `scripts/generate_corrections_doc.py`

Compares a reviewed SRT with its source VTT and generates the corrections markdown for volunteers. Automatically finds the source VTT by YouTube ID, computes word-level diffs, groups into paragraphs, and marks changes with bold/strikethrough.

```bash
python3 scripts/generate_corrections_doc.py revisions/1_AI_reviewed/FvOa5EmckHE__2020-08-22_....srt
```

## Exporting VTT to SRT

When asked to export a reviewed `.vtt` to `.srt`, apply these format changes:

1. Remove the `WEBVTT` header and any metadata lines (`Kind:`, `Language:`, etc.)
2. Add sequential cue numbers (1, 2, 3...) before each timestamp
3. Replace `.` with `,` in timestamps (e.g., `00:00:06.640` → `00:00:06,640`)
4. Replace `-->` with ` --> ` (SRT uses the same arrow format)
5. Strip `&nbsp;` entities from the text — SRT does not use them
6. Keep a blank line between each cue block
7. End the file with a blank line

## Reviewing a VTT transcript

See [transcript_correction_instructions.md](transcript_correction_instructions.md) for
the full correction instructions (garbled words, punctuation, British English,
capitalisation, speaker identification, etc.).

## Review sources

Two sources of manually reviewed transcripts exist in `revisions/`:
- **Agency** — most transcripts were corrected by an agency following Gary's team
  instructions. Their approach is the gold standard and takes precedence.
- **Volunteer** — some transcripts (e.g., Avocado Toast 2021-12-30) were done by
  volunteers, whose approach differs (e.g., preserves fillers, no punctuation added).

When resolving conflicting approaches, always follow the agency's pattern. The agency
removes fillers and adds full punctuation; some volunteers preserved fillers and added
no punctuation.

## Conventions

- **No row numbers in `TRANSCRIPT_STATUS.md`** — numbered rows require rewriting the
  entire file when a transcript is added. Use unnumbered rows, keep counts in the
  summary stats at the top.

