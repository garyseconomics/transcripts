#!/usr/bin/env python3
"""
Update script that combines download.py and convert_transcripts.py functionality.

This script downloads YouTube video transcripts and directly creates Jekyll posts
and VTT caption files. It also supports updating existing posts with current
view counts and like counts.
"""

import os
import re
import json
from subprocess import run
from datetime import datetime
import time
import argparse
import shutil


def slugify(s):
    """Convert string to URL-friendly slug."""
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s


def list_videos():
    """Get list of all video IDs from the YouTube channel."""
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


def download_subs_lang(url: str, lang: str, dl_path: str, auto=False):
    """Download subtitles for a specific language."""
    try:
        os.remove(f"{dl_path}.{lang}.vtt")
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
            dl_path,
            "--",
            url,
        ],
        check=True,
    )

    if not os.path.exists(f"{dl_path}.{lang}.vtt"):
        raise Exception("Subtitles not found for language: " + lang)

    return f"{dl_path}.{lang}.vtt"


def download_subs_meta(url: str, dl_path: str):
    """Download video metadata from YouTube."""
    try:
        os.remove(f"{dl_path}.info.json")
    except Exception:
        pass

    run(
        [
            "yt-dlp",
            "--skip-download",
            "--write-info-json",
            "-o",
            dl_path,
            "--",
            url,
        ],
        check=True,
    )

    if not os.path.exists(f"{dl_path}.info.json"):
        raise Exception("failed to download metadata")

    with open(f"{dl_path}.info.json", encoding="utf-8") as meta_fd:
        return json.load(meta_fd)


def select_subs(url: str, dl_path: str):
    """Select the best available subtitles for a video."""
    meta = download_subs_meta(url, dl_path)

    for src, auto in [(meta["subtitles"], False), (meta["automatic_captions"], True)]:
        for lang in ["en-GB", "en-orig", "en"]:
            if lang not in src:
                continue

            return meta, lang, auto

    return None, None, None


def get_existing_youtube_ids():
    """Get a list of all existing YouTube IDs from _posts directory."""
    existing_ids = {}
    posts_dir = "_posts"
    
    if not os.path.exists(posts_dir):
        return existing_ids
    
    for filename in os.listdir(posts_dir):
        if not filename.endswith(".md"):
            continue
        
        filepath = os.path.join(posts_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extract youtube_id from front matter
            match = re.search(r'^youtube_id:\s*(.+)$', content, re.MULTILINE)
            if match:
                youtube_id = match.group(1).strip()
                existing_ids[youtube_id] = filepath
    
    return existing_ids


def update_post_counts(filepath: str, view_count: int, like_count: int):
    """Update view_count and like_count in an existing post file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update view_count
    content = re.sub(
        r'^view_count:\s*\d+$',
        f'view_count: {view_count}',
        content,
        flags=re.MULTILINE
    )
    
    # Update like_count
    content = re.sub(
        r'^like_count:\s*\d+$',
        f'like_count: {like_count}',
        content,
        flags=re.MULTILINE
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def create_jekyll_post(meta: dict, vtt_path: str, slug: str, date: str):
    """Create a Jekyll post with front matter and copy VTT file."""
    # Extract required fields
    youtube_id = meta.get('youtube_id')
    title = meta.get('fulltitle', '')
    author = meta.get('author', 'Garys Economics')
    view_count = meta.get('view_count', 0)
    like_count = meta.get('like_count', 0)
    duration_seconds = meta.get('duration_seconds', 0)
    tags = meta.get('tags', [])
    categories = meta.get('categories', [])
    description = meta.get('description', '')
    thumbnail = meta.get('thumbnail', f'https://i.ytimg.com/vi/{youtube_id}/maxresdefault.jpg')
    
    # Generate post filename
    post_filename = f"{date}-{slug}.md"
    post_path = os.path.join('_posts', post_filename)
    
    # Generate caption filename
    caption_filename = f"{youtube_id}.vtt"
    caption_path = os.path.join('_includes', 'captions', caption_filename)
    
    # Create directories if they don't exist
    os.makedirs('_posts', exist_ok=True)
    os.makedirs(os.path.join('_includes', 'captions'), exist_ok=True)
    
    # Create Jekyll post with front matter
    with open(post_path, 'w', encoding='utf-8') as f:
        f.write('---\n')
        f.write('layout: post\n')
        # Quote title if it contains special YAML characters
        if ':' in title or '#' in title or '@' in title or '[' in title or ']' in title:
            # Escape double quotes in title and wrap in quotes
            safe_title = title.replace('"', '\\"')
            f.write(f'title: "{safe_title}"\n')
        else:
            f.write(f'title: {title}\n')
        f.write(f'author: {author}\n')
        f.write(f'date: {date}\n')
        f.write(f'youtube_url: https://www.youtube.com/watch?v={youtube_id}\n')
        f.write(f'youtube_id: {youtube_id}\n')
        f.write(f'view_count: {view_count}\n')
        f.write(f'like_count: {like_count}\n')
        f.write(f'duration_seconds: {duration_seconds}\n')
        
        if tags:
            f.write('tags:\n')
            for tag in tags:
                f.write(f'- {tag}\n')
        
        if categories:
            f.write('categories:\n')
            for category in categories:
                f.write(f'- {category}\n')
        
        # Write description, escaping if needed
        if description:
            # Check if description contains special YAML characters
            needs_quoting = ':' in description or '#' in description or '@' in description
            # For multi-line descriptions, use YAML literal block scalar
            if '\n' in description:
                f.write('description: |\n')
                for line in description.split('\n'):
                    f.write(f'  {line}\n')
            elif len(description) > 80 or needs_quoting:
                # Use YAML literal block scalar for long or special descriptions
                f.write('description: |\n')
                f.write(f'  {description}\n')
            else:
                f.write(f'description: {description}\n')
        
        f.write(f'thumbnail: {thumbnail}\n')
        f.write(f'channel_url: https://www.youtube.com/@garyseconomics\n')
        f.write(f'caption_file: captions/{caption_filename}\n')
        f.write('---\n')
    
    # Copy VTT file to captions directory
    shutil.copy2(vtt_path, caption_path)
    
    return post_path


def process_video(video_id: str, dl_path: str, existing_ids: dict, update_mode: bool = False):
    """Process a single video - download and create/update post."""
    url = video_id
    
    # Check if this video already exists
    if video_id in existing_ids:
        if update_mode:
            # Update mode: fetch metadata and update counts
            try:
                meta = download_subs_meta(url, dl_path)
                view_count = meta.get('view_count', 0)
                like_count = meta.get('like_count', 0)
                
                update_post_counts(existing_ids[video_id], view_count, like_count)
                print(f"✅ Updated {video_id}: views={view_count}, likes={like_count}")
                return True
            except Exception as ex:
                print(f"⚠️  Failed to update {video_id}: {ex}")
                return False
        else:
            # Not in update mode, skip existing videos
            print(f"⏭️  Skipping {video_id}: already exists")
            return False
    
    # Video doesn't exist, create new post
    try:
        yt_meta, subs_lang, is_auto = select_subs(url, dl_path)
        if subs_lang is None:
            print(f"⚠️  No subtitles found for {video_id}")
            return False
        
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
            "is_short": yt_meta.get("media_type") == "short",
            "thumbnail": yt_meta["thumbnails"][-1]["url"],
        }
        
        slug = slugify(meta["fulltitle"])
        date = datetime.fromtimestamp(meta["timestamp"]).date().isoformat()
        
        # Download subtitles
        vtt_path = download_subs_lang(url, subs_lang, dl_path, auto=is_auto)
        
        # Create Jekyll post and copy VTT
        post_path = create_jekyll_post(meta, vtt_path, slug, date)
        
        # Clean up temporary VTT file
        try:
            os.remove(vtt_path)
        except:
            pass
        
        print(f"✅ Created {video_id}: {meta['fulltitle']}")
        return True
        
    except Exception as ex:
        print(f"⚠️  Failed to process {video_id}: {ex}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Download YouTube transcripts and create/update Jekyll posts'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Update existing posts with current view and like counts'
    )
    parser.add_argument(
        '--offset',
        type=int,
        default=0,
        help='Offset to start processing from'
    )
    args = parser.parse_args()
    
    # Change to repository root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    os.chdir(repo_root)
    
    # Create temporary directory
    dl_path = ".tmp/dl"
    os.makedirs(os.path.dirname(dl_path), exist_ok=True)
    
    # Get existing YouTube IDs
    existing_ids = get_existing_youtube_ids()
    print(f"Found {len(existing_ids)} existing posts")
    
    # Get list of videos from channel
    print("Fetching video list from channel...")
    vids = list_videos()
    print(f"Found {len(vids)} videos on channel")
    print("=" * 60)
    
    created_count = 0
    updated_count = 0
    skipped_count = 0
    failed_count = 0
    
    for i, vid in enumerate(vids):
        if i < args.offset:
            continue
        
        print(f"Processing #{i+1}/{len(vids)}: {vid}")
        
        if process_video(vid, dl_path, existing_ids, update_mode=args.update):
            if vid in existing_ids:
                updated_count += 1
            else:
                created_count += 1
        else:
            if vid in existing_ids and not args.update:
                skipped_count += 1
            else:
                failed_count += 1
        
        # Rate limiting
        time.sleep(0.5)
    
    print("=" * 60)
    print("✅ Processing complete!")
    print(f"   Created: {created_count}")
    print(f"   Updated: {updated_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Failed: {failed_count}")
    print(f"   Total: {len(vids)}")


if __name__ == '__main__':
    main()
