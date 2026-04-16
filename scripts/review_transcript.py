#!/usr/bin/env python3
"""
Review a raw VTT transcript and produce a corrected SRT file.

This script reads an auto-generated VTT transcript, applies systematic
corrections (garbled words, punctuation, British English, capitalisation,
filler removal), and outputs a clean SRT file ready for volunteer review.

Usage:
    python3 scripts/review_transcript.py <transcript_folder>
    python3 scripts/review_transcript.py 2020-08-22-i-made-millions-...

The script will:
1. Read meta.json and transcript.vtt from the folder
2. Extract and deduplicate cues from the VTT auto-caption format
3. Apply text corrections (garbled words, British English, proper nouns, etc.)
4. Capitalise "I" and proper nouns throughout
5. Remove filler words (um, uh) and fix stuttered repetitions
6. Output a numbered SRT file to revisions/1_AI_reviewed/

For multi-speaker transcripts, the AI reviewer should add speaker labels
manually after running this script, then move the file to multi_speaker/.

This script handles the mechanical cleanup. The AI reviewer still needs to:
- Read through for context-dependent garbled words (names, phrasing)
- Add punctuation (sentences, commas, question marks)
- Add speaker labels for multi-speaker videos
- Remove end-of-video fragments
- Fix any remaining errors the automated rules miss
"""

import argparse
import json
import os
import re
import sys


# ============================================================
# VTT PARSING
# ============================================================

def parse_vtt(vtt_path):
    """Parse a VTT file and extract deduplicated cues.

    Auto-generated VTT captions have a distinctive pattern where each
    "real" cue appears twice: once with 10ms duration (echo) and once
    with the actual duration. Two-line cues show the previous line as
    context plus the new line. We extract only the new text from each
    real cue.

    Returns a list of dicts: [{"start": str, "end": str, "text": str}, ...]
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

    # Filter out 10ms echo cues — keep only cues with duration > 15ms
    merged = []
    for start, end, parts in raw_cues:
        s_ms = _ts_to_ms(start)
        e_ms = _ts_to_ms(end)
        if (e_ms - s_ms) > 15:
            # In 2-line cues, the second line is the new content
            new_text = parts[1] if len(parts) == 2 else parts[-1]
            merged.append({"start": start, "end": end, "text": new_text})

    return merged


def _ts_to_ms(ts):
    """Convert HH:MM:SS.mmm to milliseconds."""
    h, m, rest = ts.split(":")
    s, ms = rest.split(".")
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)


def _ts_to_srt(ts):
    """Convert VTT timestamp (dot) to SRT timestamp (comma)."""
    return ts.replace(".", ",")


# ============================================================
# TEXT CORRECTIONS
# ============================================================

# Garbled words commonly found in Gary's Economics transcripts.
# Format: (regex_pattern, replacement, flags)
# These are applied in order, so more specific patterns should come first.
GARBLED_WORDS = [
    # Names — most severely mangled category
    (r"\bum karma\b", "Keir Starmer", re.IGNORECASE),
    (r"\bkisarma\b", "Keir Starmer", re.IGNORECASE),
    (r"\bkistama\b", "Keir Starmer", re.IGNORECASE),
    (r"\bmark cary\b", "Mark Carney", re.IGNORECASE),
    (r"\bmark car\b", "Mark Carney", re.IGNORECASE),
    (r"\ba golden sack\b", "Goldman Sachs", re.IGNORECASE),
    (r"\bgoldman sack\b", "Goldman Sachs", re.IGNORECASE),
    (r"\bchristian g murphy\b", "Krishna Guru-Murthy", re.IGNORECASE),
    (r"\bmacaron\b", "Macron", re.IGNORECASE),
    (r"\bfreriedman\b", "Friedman", re.IGNORECASE),
    (r"\bthe same bat\b", "Usain Bolt", re.IGNORECASE),

    # Institution garbles
    (r"\blsc\b", "LSE", re.IGNORECASE),
    (r"\blsu\b", "LSE", re.IGNORECASE),
    (r"\bseat bank\b", "Citibank", re.IGNORECASE),
    (r"\blima crisis\b", "Lehman crisis", re.IGNORECASE),

    # Economic/political terms
    (r"\bwell through equality\b", "wealth inequality", re.IGNORECASE),
    (r"\bhow's price\b", "house price", re.IGNORECASE),
    (r"\bliving stands\b", "living standards", re.IGNORECASE),
    (r"\bliving stand\b", "living standards", re.IGNORECASE),
    (r"\brates attack\b", "rates of tax", re.IGNORECASE),
    (r"\bspread bank platform\b", "spread betting platform", re.IGNORECASE),
    (r"\bthrough the room\b", "through the roof", re.IGNORECASE),
    (r"\bbifocated\b", "bifurcated", re.IGNORECASE),
    (r"\bco model\b", "COVID model", re.IGNORECASE),
    (r"\btrading field\b", "trading floor", re.IGNORECASE),
    (r"\bfive percentage\b", "five percent", re.IGNORECASE),
    (r"\beconomic suppressor\b", "economics professor", re.IGNORECASE),
]

# British English corrections (American → British).
BRITISH_ENGLISH = [
    (r"\brealized\b", "realised"),
    (r"\brealize\b", "realise"),
    (r"\brecognized\b", "recognised"),
    (r"\brecognize\b", "recognise"),
    (r"\bcriticized\b", "criticised"),
    (r"\bcriticize\b", "criticise"),
    (r"\bdepoliticizing\b", "depoliticising"),
    (r"\bsystemized\b", "systemised"),
    (r"\bincentivized\b", "incentivised"),
    (r"\bincentivize\b", "incentivise"),
    (r"\borganized\b", "organised"),
    (r"\borganize\b", "organise"),
    (r"\borganizing\b", "organising"),
    (r"\borganizational\b", "organisational"),
    (r"\bmoralizing\b", "moralising"),
    (r"\bcivilized\b", "civilised"),
    (r"\bfueling\b", "fuelling"),
    (r"\bemphasized\b", "emphasised"),
    (r"\bemphasize\b", "emphasise"),
    (r"\blabor\b", "labour"),
    (r"\bfavor\b", "favour"),
    (r"\bfavorite\b", "favourite"),
    (r"\bcenter\b", "centre"),
    (r"\bmath\b", "maths"),
    (r"\bmom\b", "mum"),
]

# Proper nouns — ensure consistent capitalisation.
# Applied case-insensitively to fix whatever the auto-caption produced.
PROPER_NOUNS = [
    # Multi-word names (must come before single-word components)
    (r"\bgary stevenson\b", "Gary Stevenson"),
    (r"\bgary's economics\b", "Gary's Economics"),
    (r"\bluke cooper\b", "Luke Cooper"),
    (r"\bzoe williams\b", "Zoe Williams"),
    (r"\bjeremy corbyn\b", "Jeremy Corbyn"),
    (r"\bkeir starmer\b", "Keir Starmer"),
    (r"\brishi sunak\b", "Rishi Sunak"),
    (r"\bmark carney\b", "Mark Carney"),
    (r"\bnigel farage\b", "Nigel Farage"),
    (r"\bthomas piketty\b", "Thomas Piketty"),
    (r"\bbill gates\b", "Bill Gates"),
    (r"\bgeorge osborne\b", "George Osborne"),
    (r"\bjames meadway\b", "James Meadway"),
    (r"\bmian and sufi\b", "Mian and Sufi"),
    (r"\banother europe is possible\b", "Another Europe Is Possible"),
    (r"\banother europe\b", "Another Europe"),
    (r"\bnew economics foundation\b", "New Economics Foundation"),
    (r"\bbank of england\b", "Bank of England"),
    (r"\bcity of london\b", "City of London"),
    (r"\bfederal reserve\b", "Federal Reserve"),
    (r"\bgoldman sachs\b", "Goldman Sachs"),
    (r"\bwall street\b", "Wall Street"),
    (r"\bgreen new deal\b", "Green New Deal"),
    (r"\bgreat depression\b", "Great Depression"),
    (r"\bsecond world war\b", "Second World War"),
    (r"\bquestion time\b", "Question Time"),
    (r"\bsports direct\b", "Sports Direct"),
    (r"\btower hamlets\b", "Tower Hamlets"),
    (r"\bmiddle east\b", "Middle East"),
    (r"\bunited states\b", "United States"),
    (r"\bopen democracy\b", "openDemocracy"),
    (r"\bdaily express\b", "Daily Express"),
    (r"\bfinancial times\b", "Financial Times"),
    (r"\bnovara media\b", "Novara Media"),

    # Single-word proper nouns
    (r"\bgary\b", "Gary"),
    (r"\bgary's\b", "Gary's"),
    (r"\bpiketty\b", "Piketty"),
    (r"\bcitibank\b", "Citibank"),
    (r"\blehman\b", "Lehman"),
    (r"\boxford\b", "Oxford"),
    (r"\bcambridge\b", "Cambridge"),
    (r"\blondon\b", "London"),
    (r"\bbritain\b", "Britain"),
    (r"\bmansfield\b", "Mansfield"),
    (r"\bwigan\b", "Wigan"),
    (r"\bbrexit\b", "Brexit"),
    (r"\bmomentum\b", "Momentum"),
    (r"\bconservative\b", "Conservative"),
    (r"\bmacron\b", "Macron"),
    (r"\bfriedman\b", "Friedman"),
    (r"\bstraub\b", "Straub"),
    (r"\btrump\b", "Trump"),
    (r"\bmodi\b", "Modi"),
    (r"\bamerican\b", "American"),
    (r"\beuropean\b", "European"),
    (r"\bafrica\b", "Africa"),

    # Acronyms / initialisms
    (r"\bgdp\b", "GDP"),
    (r"\blse\b", "LSE"),
    (r"\bbbc\b", "BBC"),
    (r"\bibd\b", "IBD"),
    (r"\bcds\b", "CDS"),
    (r"\bcovid\b", "COVID"),
    (r"\bdfs\b", "DFS"),
    (r"\byoutube\b", "YouTube"),

    # These need case-sensitive matching to avoid false positives
]

# Filler words to remove
FILLERS = [r"\bum\b", r"\buh\b"]

# Stuttered repetition patterns
STUTTERS = [
    (r"\bi i\b", "I"),
    (r"\bthey they\b", "they"),
    (r"\bit's it's\b", "it's"),
    (r"\bthis is this is\b", "this is"),
    (r"\bhe he\b", "he"),
    (r"\bshe she\b", "she"),
    (r"\bdid did\b", "did"),
    (r"\bhad had\b", "had"),
    (r"\band and\b", "and"),
    (r"\bwe we\b", "we"),
    (r"\byou you\b", "you"),
    (r"\bbut but\b", "but"),
    (r"\bthe the\b", "the"),
    (r"\bthat that\b", "that"),
    (r"\bwas was\b", "was"),
    (r"\bin in\b", "in"),
    (r"\bto to\b", "to"),
    (r"\bso so\b", "so"),
    (r"\bcan can\b", "can"),
]


def apply_corrections(cues):
    """Apply all systematic text corrections to a list of cues.

    Modifies cues in place. Each cue is a dict with at least a "text" key.
    """
    for cue in cues:
        text = cue["text"]

        # Strip &nbsp;
        text = text.replace("&nbsp;", " ")

        # --- Garbled words ---
        for pattern, replacement, flags in GARBLED_WORDS:
            text = re.sub(pattern, replacement, text, flags=flags)

        # --- British English ---
        for pattern, replacement in BRITISH_ENGLISH:
            text = re.sub(pattern, replacement, text)

        # --- Proper noun capitalisation ---
        for pattern, replacement in PROPER_NOUNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # --- Remove filler words ---
        for pattern in FILLERS:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # --- Fix stuttered repetitions ---
        for pattern, replacement in STUTTERS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # --- Capitalise "I" and contractions ---
        text = re.sub(r"\bi\b", "I", text)
        text = re.sub(r"\bi'm\b", "I'm", text)
        text = re.sub(r"\bi've\b", "I've", text)
        text = re.sub(r"\bi'd\b", "I'd", text)
        text = re.sub(r"\bi'll\b", "I'll", text)

        # --- Currency: £ for pounds ---
        text = re.sub(r"\b(\d[\d,]*) pounds\b", r"£\1", text)

        # --- Capitalise after sentence-ending punctuation ---
        # (only within the cue — cross-cue capitalisation is handled at write time)
        text = re.sub(
            r'([.?!]"?\s+)([a-z])',
            lambda m: m.group(1) + m.group(2).upper(),
            text,
        )

        # --- Clean up whitespace from filler removal ---
        text = re.sub(r"  +", " ", text).strip()

        cue["text"] = text


# ============================================================
# SRT OUTPUT
# ============================================================

def write_srt(cues, output_path):
    """Write cues to an SRT file.

    Applies cross-cue capitalisation: if the previous cue ended with
    sentence-ending punctuation, capitalise the first letter of the next cue.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    lines = []
    cue_num = 0
    prev_text = ""

    for cue in cues:
        text = cue["text"]
        if not text:
            continue

        # Capitalise first letter if previous cue ended a sentence
        if prev_text and prev_text.rstrip()[-1:] in '.?!"\u201d':
            if text[0].islower():
                text = text[0].upper() + text[1:]

        cue_num += 1
        lines.append(str(cue_num))
        lines.append(f"{_ts_to_srt(cue['start'])} --> {_ts_to_srt(cue['end'])}")
        lines.append(text)
        lines.append("")
        prev_text = text

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return cue_num


# ============================================================
# FILENAME GENERATION
# ============================================================

def make_srt_filename(meta, folder_name):
    """Generate the SRT filename from metadata.

    Format: youtubeID__date_Title_Words.srt
    """
    youtube_id = meta["youtube_id"]
    title = meta.get("fulltitle", folder_name)

    # Clean title for filename: keep alphanumeric and spaces, then replace
    clean = re.sub(r"[^a-zA-Z0-9 ]", "", title)
    words = clean.split()
    # Truncate to keep filename reasonable
    title_part = "_".join(w.capitalize() for w in words[:10])

    # Extract date from folder name (YYYY-MM-DD prefix)
    date_match = re.match(r"(\d{4}-\d{2}-\d{2})", folder_name)
    date_part = date_match.group(1) if date_match else "unknown-date"

    return f"{youtube_id}__{date_part}_{title_part}.srt"


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Review a VTT transcript and produce a corrected SRT file."
    )
    parser.add_argument(
        "folder",
        help="Transcript folder name (under transcripts/) or full path.",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output SRT path. Default: auto-generated in revisions/1_AI_reviewed/.",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Parse and correct but don't write the file. Print stats instead.",
    )
    args = parser.parse_args()

    # Resolve paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)

    folder = args.folder
    # If just a folder name, prepend transcripts/
    if not os.path.isdir(folder):
        folder = os.path.join(repo_root, "transcripts", folder)
    if not os.path.isdir(folder):
        print(f"Error: folder not found: {folder}", file=sys.stderr)
        sys.exit(1)

    folder_name = os.path.basename(folder)

    # Read metadata
    meta_path = os.path.join(folder, "meta.json")
    if not os.path.exists(meta_path):
        print(f"Error: no meta.json in {folder}", file=sys.stderr)
        sys.exit(1)

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # Read VTT
    vtt_path = os.path.join(folder, "transcript.vtt")
    if not os.path.exists(vtt_path):
        print(f"Error: no transcript.vtt in {folder}", file=sys.stderr)
        sys.exit(1)

    is_auto = meta.get("is_automatic_transcript", True)
    youtube_id = meta.get("youtube_id", "unknown")
    title = meta.get("fulltitle", folder_name)
    duration = meta.get("duration_seconds", 0)

    print(f"Title:     {title}")
    print(f"YouTube:   https://www.youtube.com/watch?v={youtube_id}")
    print(f"Duration:  {duration // 60}m {duration % 60}s")
    print(f"Auto-cap:  {is_auto}")
    print()

    # Parse VTT
    print("Parsing VTT...")
    cues = parse_vtt(vtt_path)
    print(f"  Extracted {len(cues)} cues")

    if not is_auto:
        print()
        print("Note: This is NOT an auto-generated transcript.")
        print("It may only need format conversion, not content correction.")
        print("The script will still apply corrections — review the output.")
        print()

    # Apply corrections
    print("Applying corrections...")
    apply_corrections(cues)

    # Determine output path
    srt_name = make_srt_filename(meta, folder_name)
    if args.output:
        output_path = args.output
    else:
        output_path = os.path.join(
            repo_root, "revisions", "1_AI_reviewed", srt_name
        )

    if args.dry_run:
        print(f"\n[dry run] Would write to: {output_path}")
        print(f"[dry run] {len(cues)} cues")
        # Print first 20 cues as sample
        print("\nSample (first 20 cues):")
        for i, cue in enumerate(cues[:20]):
            print(f"  {i+1}. [{cue['start']}] {cue['text']}")
        return

    # Write SRT
    n = write_srt(cues, output_path)
    print(f"  Wrote {n} cues to {output_path}")

    print()
    print("Done. Next steps for the AI reviewer:")
    print("  1. Read through the SRT and fix context-dependent errors")
    print("     (garbled names, phrasing that only makes sense in context)")
    print("  2. Add punctuation (periods, commas, question marks)")
    print("  3. Check for multi-speaker content — if so, add speaker labels")
    print("     and move the file to revisions/1_AI_reviewed/multi_speaker/")
    print("  4. Remove any end-of-video fragments")
    print("  5. Update revisions/TRANSCRIPT_STATUS.md")


if __name__ == "__main__":
    main()
