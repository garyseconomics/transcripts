#!/usr/bin/env python3
"""
Generate a corrections document (.md) for volunteer review.

This script compares the original VTT transcript with a reviewed SRT file
and produces a markdown document showing all changes, formatted for
volunteers to read alongside the video.

Usage:
    python3 scripts/generate_corrections_doc.py <srt_file>
    python3 scripts/generate_corrections_doc.py revisions/1_AI_reviewed/FvOa5EmckHE__....srt

The script will:
1. Find the matching source VTT via the YouTube ID in the filename
2. Parse both the original VTT and the reviewed SRT
3. Align cues by timestamp
4. Diff the text to find word-level changes
5. Group cues into flowing paragraphs with timestamps
6. Mark changes: **bold** for additions/corrections, ~~strikethrough~~ for removals
7. Output an .md file to revisions/2_To_be_reviewed_by_volunteers/

The output follows the format described in CLAUDE.md:
- YouTube link at the top
- Flowing paragraphs (not one line per cue)
- Timestamps (HH:MM:SS) before each paragraph
- Bold for added/changed words, strikethrough for removed words
- Punctuation changes are NOT bolded
"""

import argparse
import difflib
import json
import os
import re
import sys


# ============================================================
# PARSING
# ============================================================

def parse_vtt_raw(vtt_path):
    """Parse VTT and extract deduplicated cues with raw (uncorrected) text.

    Returns list of dicts: [{"start": str, "end": str, "text": str}, ...]
    """
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r"\n\n+", content)
    raw_cues = []

    for block in blocks:
        lines = block.strip().split("\n")
        ts_line = None
        text_parts = []
        for line in lines:
            if "-->" in line:
                ts_line = line
            elif (
                ts_line
                and line.strip()
                and not line.startswith("WEBVTT")
                and not line.startswith("Kind:")
                and not line.startswith("Language:")
            ):
                clean = re.sub(r"<[^>]+>", "", line).strip()
                if clean:
                    text_parts.append(clean)
        if ts_line and text_parts:
            m = re.match(
                r"(\d+:\d+:\d+\.\d+)\s*-->\s*(\d+:\d+:\d+\.\d+)", ts_line
            )
            if m:
                raw_cues.append((m.group(1), m.group(2), text_parts))

    # Filter out 10ms echo cues
    merged = []
    for start, end, parts in raw_cues:
        s_ms = _ts_to_ms(start)
        e_ms = _ts_to_ms(end)
        if (e_ms - s_ms) > 15:
            new_text = parts[1] if len(parts) == 2 else parts[-1]
            merged.append({"start": start, "end": end, "text": new_text})

    return merged


def parse_srt(srt_path):
    """Parse an SRT file into cues.

    Returns list of dicts: [{"start": str, "end": str, "text": str}, ...]
    Timestamps are returned in VTT format (with dots) for consistency.
    """
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    cues = []
    blocks = re.split(r"\n\n+", content.strip())

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
        # Find timestamp line
        ts_line = None
        text_lines = []
        for line in lines:
            if "-->" in line:
                ts_line = line
            elif ts_line:
                text_lines.append(line)
            # Skip cue number lines (pure digits)

        if ts_line and text_lines:
            # Convert SRT timestamps (comma) back to VTT format (dot)
            ts_line = ts_line.replace(",", ".")
            m = re.match(
                r"(\d+:\d+:\d+\.\d+)\s*-->\s*(\d+:\d+:\d+\.\d+)", ts_line
            )
            if m:
                text = " ".join(text_lines)
                cues.append({
                    "start": m.group(1),
                    "end": m.group(2),
                    "text": text,
                })

    return cues


def _ts_to_ms(ts):
    """Convert HH:MM:SS.mmm to milliseconds."""
    h, m, rest = ts.split(":")
    s, ms = rest.split(".")
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)


def _ts_to_display(ts):
    """Convert HH:MM:SS.mmm to HH:MM:SS for display."""
    return ts.split(".")[0]


# ============================================================
# DIFFING
# ============================================================

def is_punctuation_only(word):
    """Check if a word is only punctuation (commas, periods, etc.)."""
    return bool(re.match(r'^[.,;:!?\'"()\u201c\u201d\u2018\u2019-]+$', word))


def diff_texts(original, corrected):
    """Produce a marked-up version showing changes between original and corrected.

    Returns a string with **bold** for additions/changes and ~~strikethrough~~
    for removals. Punctuation-only changes are not bolded.
    """
    # Tokenise into words, keeping punctuation attached
    orig_words = original.split()
    corr_words = corrected.split()

    if orig_words == corr_words:
        return corrected

    matcher = difflib.SequenceMatcher(None, orig_words, corr_words)
    result = []

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            result.extend(corr_words[j1:j2])

        elif op == "replace":
            old_chunk = " ".join(orig_words[i1:i2])
            new_chunk = " ".join(corr_words[j1:j2])
            # Check if the only difference is punctuation or capitalisation
            old_stripped = re.sub(r'[^\w\s]', '', old_chunk).lower()
            new_stripped = re.sub(r'[^\w\s]', '', new_chunk).lower()

            if old_stripped == new_stripped:
                # Only punctuation/capitalisation changed — show corrected
                # without bold but mark significant capitalisations
                for w_old, w_new in zip(orig_words[i1:i2], corr_words[j1:j2]):
                    bare_old = re.sub(r'[^\w]', '', w_old)
                    bare_new = re.sub(r'[^\w]', '', w_new)
                    if bare_old.lower() == bare_new.lower():
                        # Same word, maybe cap change
                        if bare_old != bare_new and len(bare_new) > 1:
                            # Significant cap change (proper noun) — bold the caps
                            result.append(_mark_cap_changes(w_old, w_new))
                        else:
                            result.append(w_new)
                    else:
                        result.append(f"~~{w_old}~~ **{w_new}**")
                # Handle length mismatch
                if i2 - i1 < j2 - j1:
                    for w in corr_words[j1 + (i2 - i1):j2]:
                        result.append(f"**{w}**")
                elif i2 - i1 > j2 - j1:
                    for w in orig_words[i1 + (j2 - j1):i2]:
                        result.append(f"~~{w}~~")
            else:
                # Actual word change
                result.append(f"~~{old_chunk}~~")
                result.append(f"**{new_chunk}**")

        elif op == "insert":
            for w in corr_words[j1:j2]:
                if is_punctuation_only(w):
                    result.append(w)
                else:
                    result.append(f"**{w}**")

        elif op == "delete":
            for w in orig_words[i1:i2]:
                result.append(f"~~{w}~~")

    return " ".join(result)


def _mark_cap_changes(old_word, new_word):
    """Mark capitalisation changes in a word by bolding changed letters.

    For proper nouns like 'london' -> 'London', produces '**L**ondon'.
    For acronyms like 'gdp' -> 'GDP', produces '**GDP**'.
    """
    # If all letters changed case, bold the whole word
    old_letters = re.sub(r'[^\w]', '', old_word)
    new_letters = re.sub(r'[^\w]', '', new_word)

    if old_letters.lower() != new_letters.lower():
        return f"~~{old_word}~~ **{new_word}**"

    # If it's an acronym (all caps, short), bold the whole thing
    if new_letters.isupper() and len(new_letters) <= 5:
        return f"**{new_word}**"

    # Otherwise mark individual letter changes
    result = []
    # Reconstruct with bold on changed characters
    oi = 0
    for ch in new_word:
        if oi < len(old_word) and ch.lower() == old_word[oi].lower():
            if ch != old_word[oi]:
                result.append(f"**{ch}**")
            else:
                result.append(ch)
            oi += 1
        else:
            result.append(ch)
            if oi < len(old_word):
                oi += 1

    return "".join(result)


# ============================================================
# PARAGRAPH GROUPING
# ============================================================

def group_into_paragraphs(cues, max_words=200, min_words=50):
    """Group consecutive cues into paragraphs of flowing text.

    Breaks at:
    - Speaker label changes (e.g., [Gary] -> [Luke])
    - Natural sentence boundaries when approaching max_words
    - Special cues like [Music], [Applause]

    Returns list of dicts: [{"timestamp": str, "text": str}, ...]
    """
    paragraphs = []
    current_words = []
    current_ts = None
    word_count = 0

    for cue in cues:
        text = cue["text"].strip()
        if not text:
            continue

        # Start first paragraph
        if current_ts is None:
            current_ts = _ts_to_display(cue["start"])

        # Check for speaker label at start of this cue
        has_speaker = bool(re.match(r"^\[(?:Gary|Luke|Zoe|Host|Guest)\]", text))

        # Check if previous paragraph should end
        should_break = False

        if has_speaker and current_words:
            # Speaker change — always break
            should_break = True
        elif word_count >= max_words and current_words:
            # Over max — break at next sentence end
            last = " ".join(current_words)
            if last.rstrip()[-1:] in ".?!":
                should_break = True
        elif word_count >= min_words and current_words:
            # Over min — break if last cue ended a sentence
            last_word = current_words[-1] if current_words else ""
            if last_word.rstrip()[-1:] in ".?!" and not has_speaker:
                # Only break at natural pause points when near max
                if word_count >= max_words * 0.7:
                    should_break = True

        # Special cues that stand alone
        is_special = text.startswith("[Music]") or text.startswith("[Applause]")
        if is_special and current_words:
            should_break = True

        if should_break:
            paragraphs.append({
                "timestamp": current_ts,
                "text": " ".join(current_words),
            })
            current_words = []
            word_count = 0
            current_ts = _ts_to_display(cue["start"])

        current_words.append(text)
        word_count += len(text.split())

        if is_special:
            paragraphs.append({
                "timestamp": current_ts if not should_break else _ts_to_display(cue["start"]),
                "text": " ".join(current_words),
            })
            current_words = []
            word_count = 0
            current_ts = None

    # Flush remaining
    if current_words:
        paragraphs.append({
            "timestamp": current_ts,
            "text": " ".join(current_words),
        })

    return paragraphs


# ============================================================
# ALIGNMENT & DOCUMENT GENERATION
# ============================================================

def align_and_diff(orig_cues, srt_cues):
    """Align original and corrected cues by timestamp, then diff.

    Returns a list of dicts with the corrected text and diff markup,
    plus the start timestamp from the SRT.
    """
    # Build a mapping from start timestamp -> original text
    orig_map = {}
    for cue in orig_cues:
        key = cue["start"]
        orig_map[key] = cue["text"]

    result_cues = []
    for cue in srt_cues:
        corrected = cue["text"]
        original = orig_map.get(cue["start"], "")

        if original:
            marked = diff_texts(original, corrected)
        else:
            # No matching original — everything is new
            marked = corrected

        result_cues.append({
            "start": cue["start"],
            "end": cue["end"],
            "text": corrected,
            "marked": marked,
        })

    return result_cues


def generate_document(youtube_id, title, paragraphs):
    """Generate the markdown corrections document."""
    lines = []
    lines.append(f"# {title} — Corrections")
    lines.append("")
    lines.append(f"https://www.youtube.com/watch?v={youtube_id}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for para in paragraphs:
        lines.append(para["timestamp"])
        lines.append(para["text"])
        lines.append("")

    return "\n".join(lines)


# ============================================================
# SOURCE FOLDER LOOKUP
# ============================================================

def find_source_folder(youtube_id, repo_root):
    """Find the transcript source folder for a YouTube ID."""
    transcripts_dir = os.path.join(repo_root, "transcripts")
    if not os.path.isdir(transcripts_dir):
        return None

    for name in os.listdir(transcripts_dir):
        folder = os.path.join(transcripts_dir, name)
        if not os.path.isdir(folder):
            continue
        meta_path = os.path.join(folder, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            if meta.get("youtube_id") == youtube_id:
                return folder

    return None


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate a corrections document for volunteer review."
    )
    parser.add_argument(
        "srt_file",
        help="Path to the reviewed SRT file.",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output .md path. Default: auto-generated in revisions/2_To_be_reviewed_by_volunteers/.",
    )
    args = parser.parse_args()

    # Resolve paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)

    srt_path = args.srt_file
    if not os.path.isfile(srt_path):
        srt_path = os.path.join(repo_root, srt_path)
    if not os.path.isfile(srt_path):
        print(f"Error: SRT file not found: {args.srt_file}", file=sys.stderr)
        sys.exit(1)

    # Extract YouTube ID from filename (format: YTID__date_Title.srt)
    srt_basename = os.path.basename(srt_path)
    yt_match = re.match(r"^([^_]+)__", srt_basename)
    if not yt_match:
        print(
            f"Error: cannot extract YouTube ID from filename: {srt_basename}",
            file=sys.stderr,
        )
        print("Expected format: youtubeID__date_Title.srt", file=sys.stderr)
        sys.exit(1)

    youtube_id = yt_match.group(1)

    # Find source folder
    source_folder = find_source_folder(youtube_id, repo_root)
    if not source_folder:
        print(
            f"Error: cannot find source transcript folder for YouTube ID: {youtube_id}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Load metadata
    meta_path = os.path.join(source_folder, "meta.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    title = meta.get("fulltitle", srt_basename)
    vtt_path = os.path.join(source_folder, "transcript.vtt")

    print(f"Title:     {title}")
    print(f"YouTube:   https://www.youtube.com/watch?v={youtube_id}")
    print(f"SRT:       {srt_path}")
    print(f"VTT:       {vtt_path}")
    print()

    # Parse both files
    print("Parsing files...")
    orig_cues = parse_vtt_raw(vtt_path)
    srt_cues = parse_srt(srt_path)
    print(f"  Original VTT: {len(orig_cues)} cues")
    print(f"  Reviewed SRT: {len(srt_cues)} cues")

    # Align and diff
    print("Computing diffs...")
    diffed_cues = align_and_diff(orig_cues, srt_cues)

    # Group into paragraphs using the marked-up text
    print("Grouping into paragraphs...")
    paragraphs = group_into_paragraphs(diffed_cues)

    # Group marked cues into paragraphs.
    # Break on: speaker changes, [Music]/[Applause], sentence ends near
    # word limit, and time gaps (fallback for transcripts without punctuation).
    MAX_WORDS = 200
    SOFT_WORDS = 120  # start looking for break points
    FORCE_WORDS = 300  # force break even mid-sentence
    TIME_GAP_MS = 30000  # 30s gap forces a paragraph break

    marked_paragraphs = []
    current_marked = []
    current_ts = None
    current_start_ms = 0
    word_count = 0

    for cue in diffed_cues:
        text = cue["marked"].strip()
        if not text:
            continue

        cue_ms = _ts_to_ms(cue["start"])

        if current_ts is None:
            current_ts = _ts_to_display(cue["start"])
            current_start_ms = cue_ms

        has_speaker = bool(re.match(r"^\[(?:Gary|Luke|Zoe|Host|Guest)\]", text))
        is_special = text.startswith("[Music]") or text.startswith("[Applause]")

        should_break = False

        # Always break on speaker change
        if has_speaker and current_marked:
            should_break = True
        # Always break before special cues
        elif is_special and current_marked:
            should_break = True
        # Force break at hard word limit
        elif word_count >= FORCE_WORDS and current_marked:
            should_break = True
        # Break at sentence end when over soft limit
        elif word_count >= SOFT_WORDS and current_marked:
            last = " ".join(current_marked)
            if last.rstrip()[-1:] in '.?!"':
                should_break = True
        # Break on time gap (fallback for unpunctuated text)
        if (
            not should_break
            and current_marked
            and word_count >= 60
            and (cue_ms - current_start_ms) >= TIME_GAP_MS
        ):
            should_break = True

        if should_break:
            marked_paragraphs.append({
                "timestamp": current_ts,
                "text": " ".join(current_marked),
            })
            current_marked = []
            word_count = 0
            current_ts = _ts_to_display(cue["start"])
            current_start_ms = cue_ms

        current_marked.append(text)
        word_count += len(re.sub(r"[~*]", "", text).split())

        if is_special:
            marked_paragraphs.append({
                "timestamp": current_ts,
                "text": " ".join(current_marked),
            })
            current_marked = []
            word_count = 0
            current_ts = None

    if current_marked:
        marked_paragraphs.append({
            "timestamp": current_ts,
            "text": " ".join(current_marked),
        })

    # Generate document
    print("Generating document...")
    doc = generate_document(youtube_id, title, marked_paragraphs)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        md_name = srt_basename.replace(".srt", ".md")
        output_path = os.path.join(
            repo_root,
            "revisions",
            "2_To_be_reviewed_by_volunteers",
            md_name,
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(doc)

    print(f"  Wrote {len(marked_paragraphs)} paragraphs to {output_path}")
    print()
    print("Done. The corrections document is ready for volunteer review.")
    print("Next steps:")
    print("  1. Skim through the document to check the diff markup looks sensible")
    print("  2. Share the .md file with volunteers")


if __name__ == "__main__":
    main()
