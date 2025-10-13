#!/usr/bin/env python3

import os
import re
from subprocess import run
import json
from datetime import datetime
import time
import argparse

DL_PATH = ".tmp/dl"


def slugify(s):
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s


def list_videos():
    return (
        run(
            [
                "yt-dlp",
                "--flat-playlist",
                "--print",
                "id",
                "https://www.youtube.com/@garyseconomics",
            ],
            capture_output=True,
            check=True,
        )
        .stdout.decode()
        .splitlines()
    )


def download_subs_lang(url: str, lang: str, auto=False):
    try:
        os.remove(f"{DL_PATH}.{lang}.vtt")
    except Exception:
        pass

    run(
        [
            "yt-dlp",
            "--write-sub",
            "--sub-lang",
            lang,
            "--skip-download",
            "--write-info-json",
            *(["--write-auto-sub"] if auto else []),
            "-o",
            DL_PATH,
            "--",
            url,
        ],
        check=True,
    )

    if not os.path.exists(f"{DL_PATH}.{lang}.vtt"):
        raise Exception("Subtitles not found for language: " + lang)

    return f"{DL_PATH}.{lang}.vtt"


def download_subs_meta(url: str):
    try:
        os.remove(f"{DL_PATH}.info.json")
    except Exception:
        pass

    run(
        [
            "yt-dlp",
            "--skip-download",
            "--write-info-json",
            "-o",
            DL_PATH,
            "--",
            url,
        ],
        check=True,
    )

    if not os.path.exists(f"{DL_PATH}.info.json"):
        raise Exception("failed to download metadata")

    with open(f"{DL_PATH}.info.json", encoding="utf-8") as meta_fd:
        return json.load(meta_fd)


def select_subs(url: str):
    meta = download_subs_meta(url)

    for src, auto in [(meta["subtitles"], False), (meta["automatic_captions"], True)]:
        for lang in ["en-GB", "en-orig", "en"]:
            if lang not in src:
                continue

            return meta, lang, auto

    return None, None, None


def step(url: str):
    yt_meta, subs_lang, is_auto = select_subs(url)
    if subs_lang is None:
        return True

    meta = {
        "fulltitle": yt_meta["title"],
        "author": yt_meta["uploader"],
        "timestamp": yt_meta["timestamp"],
        "youtube_id": yt_meta["display_id"],
        "view_count": yt_meta["view_count"],
        "like_count": yt_meta["like_count"],
        "duration_seconds": yt_meta["duration"],
        "tags": yt_meta["tags"],
        "categories": yt_meta["categories"],
        "description": yt_meta["description"],
        "is_automatic_transcript": is_auto,
        "is_short": yt_meta["media_type"] == "short",
        "thumbnail": yt_meta["thumbnails"][-1]["url"],
    }

    slug = slugify(meta["fulltitle"])
    date = datetime.fromtimestamp(meta["timestamp"]).date().isoformat()
    transcript_base = f"transcripts/{date}-{slug}"

    if os.path.exists(transcript_base):
        return False

    try:
        os.makedirs(transcript_base)

        with open(f"{transcript_base}/meta.json", "a", encoding="utf-8") as out_fd:
            json.dump(meta, out_fd, indent=2)

        path = download_subs_lang(url, subs_lang, auto=is_auto)
        os.rename(path, f"{transcript_base}/transcript.vtt")

    except Exception as ex:
        for f in os.listdir(transcript_base):
            os.remove(f"{transcript_base}/{f}")

        os.rmdir(transcript_base)
        raise ex


parser = argparse.ArgumentParser()
parser.add_argument("--offset", type=int, help="Offset to parse args from", default=0)
args = parser.parse_args()

offset = args.offset
vids = list_videos()

for i, vid in enumerate(vids):
    if i < offset:
        continue

    print(f"DOWNLOAD {vid}: #{i}/{len(vids)}")
    step(vid)
    time.sleep(0.5)
