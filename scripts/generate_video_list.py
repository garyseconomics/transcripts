#!/usr/bin/env python3
"""
Generate the video list JSON used by the MCP server's `video_list` tool.

Reads every transcripts/<folder>/meta.json and writes one JSON list with an
entry per video:

    {"id": ..., "title": ..., "published_date": "YYYY-MM-DD", "link": ...}

- YouTube Shorts (`is_short: true`) are left out.
- `published_date` comes from `timestamp`, which is the YouTube publish time
  (checked against YouTube's publishDate, premieres included), as a UTC date.
- Sorted by published_date, then id, so regenerated files diff cleanly.

--ids-from (temporary): only include the videos whose IDs appear in the
transcript file names (`<video_id>__<date>_<title>.srt`) in a folder, e.g.
the transcripts already imported into Chroma. The full list can't be trusted
yet because `is_short` is wrong in meta.json for many Shorts.

The output goes to videos_info/videos.json unless -o is given.

Usage:
    python3 scripts/generate_video_list.py
    python3 scripts/generate_video_list.py -o path/to/videos.json
    python3 scripts/generate_video_list.py \\
        --ids-from ../chatbot-database/video_transcripts/4_already_imported
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPTS_DIR = REPO_ROOT / "transcripts"
OUTPUT_DIR = REPO_ROOT / "videos_info"
REQUIRED_FIELDS = ("youtube_id", "fulltitle", "timestamp", "is_short")


def video_entry(meta):
    """Build one video list entry from a meta.json dict."""
    video_id = meta["youtube_id"]
    published = datetime.fromtimestamp(meta["timestamp"], timezone.utc)
    return {
        "id": video_id,
        "title": meta["fulltitle"],
        "published_date": published.date().isoformat(),
        "link": f"https://www.youtube.com/watch?v={video_id}",
    }


def read_ids_from_folder(folder):
    """Return the video IDs found in `<video_id>__...` file names in a folder."""
    if not folder.is_dir():
        raise ValueError(f"not a folder: {folder}")
    return {p.name.split("__")[0] for p in folder.iterdir() if p.is_file() and "__" in p.name}


def build_video_list(transcripts_dir):
    """Return (videos, number_of_shorts_skipped). Raises ValueError on bad data."""
    videos = {}
    shorts = 0
    meta_paths = sorted(transcripts_dir.glob("*/meta.json"))
    if not meta_paths:
        raise ValueError(f"no meta.json files found in {transcripts_dir}")

    for path in meta_paths:
        with open(path, encoding="utf-8") as f:
            meta = json.load(f)

        missing = [k for k in REQUIRED_FIELDS if k not in meta]
        if missing:
            raise ValueError(f"{path}: missing fields {', '.join(missing)}")

        if meta["is_short"]:
            shorts += 1
            continue

        entry = video_entry(meta)
        video_id = entry["id"]
        if video_id in videos:
            raise ValueError(f"{path}: duplicate video_id {video_id}")
        videos[video_id] = entry

    ordered = sorted(videos.values(), key=lambda v: (v["published_date"], v["id"]))
    return ordered, shorts


def main():
    parser = argparse.ArgumentParser(
        description="Generate the video list JSON for the MCP server."
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=OUTPUT_DIR / "videos.json",
        help="output file (default: videos_info/videos.json)",
    )
    parser.add_argument(
        "--ids-from",
        type=Path,
        metavar="FOLDER",
        help="only include videos whose IDs appear in the transcript file "
             "names in FOLDER (temporary)",
    )
    args = parser.parse_args()

    try:
        videos, shorts = build_video_list(TRANSCRIPTS_DIR)
        if args.ids_from:
            wanted = read_ids_from_folder(args.ids_from)
            videos = [v for v in videos if v["id"] in wanted]
            missing = sorted(wanted - {v["id"] for v in videos})
            if missing:
                print(
                    f"Warning: {len(missing)} IDs from {args.ids_from} have no "
                    f"meta.json in this repo (or are Shorts): {', '.join(missing)}",
                    file=sys.stderr,
                )
            if not videos:
                raise ValueError(f"none of the IDs in {args.ids_from} were found")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(
        f"Wrote {len(videos)} videos to {args.output} "
        f"({shorts} Shorts skipped, "
        f"{videos[0]['published_date']} to {videos[-1]['published_date']})"
    )


if __name__ == "__main__":
    main()
