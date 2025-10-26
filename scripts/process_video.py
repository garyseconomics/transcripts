#!/usr/bin/env python3
"""
Process a YouTube video: download VTT files and create Jekyll post.

This script downloads VTT caption files for a YouTube video using yt-dlp
and creates a corresponding Jekyll post file in _posts/ with YAML front matter.
"""

import os
import sys
import json
import re
import argparse
import traceback
from subprocess import run
from datetime import datetime
import shutil


def slugify(s):
    """Convert string to URL-friendly slug."""
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s


def download_metadata(video_id):
    """Download video metadata using yt-dlp."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    dl_path = ".tmp/dl"
    
    # Create temp directory if it doesn't exist
    os.makedirs(".tmp", exist_ok=True)
    
    # Remove existing metadata file if present
    try:
        os.remove(f"{dl_path}.info.json")
    except FileNotFoundError:
        pass
    
    # Download metadata
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
        raise RuntimeError("Failed to download metadata")
    
    with open(f"{dl_path}.info.json", encoding="utf-8") as f:
        return json.load(f)


def download_subtitles(video_id, metadata):
    """Download VTT subtitle files for all available English variants."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    dl_path = ".tmp/dl"
    
    # Determine which subtitles to download
    subtitles = metadata.get("subtitles", {})
    auto_captions = metadata.get("automatic_captions", {})
    
    # Priority order for English subtitles
    lang_priority = ["en-GB", "en-orig", "en"]
    
    downloaded_files = []
    
    # Try manual subtitles first
    for lang in lang_priority:
        if lang in subtitles:
            # Remove existing file if present
            try:
                os.remove(f"{dl_path}.{lang}.vtt")
            except FileNotFoundError:
                pass
            
            run(
                [
                    "yt-dlp",
                    "--write-sub",
                    "--sub-lang",
                    lang,
                    "--skip-download",
                    "-o",
                    dl_path,
                    "--",
                    url,
                ],
                check=True,
            )
            
            if os.path.exists(f"{dl_path}.{lang}.vtt"):
                downloaded_files.append((f"{dl_path}.{lang}.vtt", lang, False))
    
    # If no manual subtitles, try auto-generated
    if not downloaded_files:
        for lang in lang_priority:
            if lang in auto_captions:
                # Remove existing file if present
                try:
                    os.remove(f"{dl_path}.{lang}.vtt")
                except FileNotFoundError:
                    pass
                
                run(
                    [
                        "yt-dlp",
                        "--write-auto-sub",
                        "--sub-lang",
                        lang,
                        "--skip-download",
                        "-o",
                        dl_path,
                        "--",
                        url,
                    ],
                    check=True,
                )
                
                if os.path.exists(f"{dl_path}.{lang}.vtt"):
                    downloaded_files.append((f"{dl_path}.{lang}.vtt", lang, True))
                    break  # Only download first auto-caption variant
    
    return downloaded_files


def create_post(metadata, video_id):
    """Create Jekyll post file with front matter."""
    title = metadata.get("title", "")
    author = metadata.get("uploader", "Garys Economics")
    timestamp = metadata.get("timestamp", 0)
    date = datetime.fromtimestamp(timestamp).date().isoformat()
    view_count = metadata.get("view_count", 0)
    like_count = metadata.get("like_count", 0)
    duration_seconds = metadata.get("duration", 0)
    tags = metadata.get("tags", [])
    categories = metadata.get("categories", [])
    description = metadata.get("description", "")
    thumbnails = metadata.get("thumbnails", [])
    thumbnail = thumbnails[-1]["url"] if thumbnails else f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
    
    # Generate post filename
    slug = slugify(title)
    post_filename = f"{date}-{slug}.md"
    post_path = os.path.join("_posts", post_filename)
    
    # Check if post already exists
    if os.path.exists(post_path):
        print(f"⚠️  Post already exists: {post_path}")
        return False, post_path
    
    # Create _posts directory if it doesn't exist
    os.makedirs("_posts", exist_ok=True)
    
    # Create Jekyll post with front matter
    with open(post_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write("layout: post\n")
        
        # Quote title if it contains special YAML characters
        if ":" in title or "#" in title or "@" in title or "[" in title or "]" in title:
            safe_title = title.replace('"', '\\"')
            f.write(f'title: "{safe_title}"\n')
        else:
            f.write(f"title: {title}\n")
        
        f.write(f"author: {author}\n")
        f.write(f"date: {date}\n")
        f.write(f"youtube_url: https://www.youtube.com/watch?v={video_id}\n")
        f.write(f"youtube_id: {video_id}\n")
        f.write(f"view_count: {view_count}\n")
        f.write(f"like_count: {like_count}\n")
        f.write(f"duration_seconds: {duration_seconds}\n")
        
        if tags:
            f.write("tags:\n")
            for tag in tags:
                f.write(f"- {tag}\n")
        
        if categories:
            f.write("categories:\n")
            for category in categories:
                f.write(f"- {category}\n")
        
        # Write description
        if description:
            # Use YAML literal block scalar for multi-line or special descriptions
            if "\n" in description or len(description) > 80 or ":" in description or "#" in description:
                f.write("description: |\n")
                for line in description.split("\n"):
                    f.write(f"  {line}\n")
            else:
                f.write(f"description: {description}\n")
        
        f.write(f"thumbnail: {thumbnail}\n")
        f.write("channel_url: https://www.youtube.com/@garyseconomics\n")
        f.write(f"caption_file: captions/{video_id}.vtt\n")
        f.write("---\n")
    
    return True, post_path


def copy_vtt_files(downloaded_files, video_id):
    """Copy VTT files to _includes/captions directory."""
    captions_dir = os.path.join("_includes", "captions")
    os.makedirs(captions_dir, exist_ok=True)
    
    copied_files = []
    
    for file_path, lang, is_auto in downloaded_files:
        # Primary file uses just the video ID
        if not copied_files:
            dest_path = os.path.join(captions_dir, f"{video_id}.vtt")
        else:
            # Additional files include language code
            dest_path = os.path.join(captions_dir, f"{video_id}.{lang}.vtt")
        
        if os.path.exists(dest_path):
            print(f"⚠️  Caption file already exists: {dest_path}")
        else:
            shutil.copy2(file_path, dest_path)
            copied_files.append(dest_path)
            print(f"✅ Copied caption: {dest_path} ({'auto' if is_auto else 'manual'})")
    
    return copied_files


def process_video(video_id):
    """Process a YouTube video: download VTT and create post."""
    # Change to repository root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    os.chdir(repo_root)
    
    print(f"Processing video: {video_id}")
    print("=" * 60)
    
    # Download metadata
    print("📥 Downloading metadata...")
    metadata = download_metadata(video_id)
    print(f"✅ Video: {metadata.get('title', 'Unknown')}")
    
    # Download subtitles
    print("📥 Downloading VTT files...")
    downloaded_files = download_subtitles(video_id, metadata)
    
    if not downloaded_files:
        print("❌ No English subtitles found for this video")
        return False
    
    print(f"✅ Downloaded {len(downloaded_files)} VTT file(s)")
    
    # Copy VTT files to captions directory
    print("📝 Copying VTT files to _includes/captions/...")
    copied_files = copy_vtt_files(downloaded_files, video_id)
    
    # Create post
    print("📝 Creating Jekyll post...")
    created, post_path = create_post(metadata, video_id)
    
    if created:
        print(f"✅ Created post: {post_path}")
    
    print("=" * 60)
    print("✅ Processing complete!")
    
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download VTT files and create Jekyll post for a YouTube video"
    )
    parser.add_argument(
        "video_id",
        help="YouTube video ID (e.g., Ja9dTjY3uWU)"
    )
    
    args = parser.parse_args()
    
    try:
        success = process_video(args.video_id)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
