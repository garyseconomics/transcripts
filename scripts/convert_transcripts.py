#!/usr/bin/env python3
"""
Convert transcripts from ./transcripts format to Jekyll _posts and _includes/captions format.

This script reads transcript folders containing meta.json and transcript.vtt files,
then generates:
1. Jekyll post markdown files in _posts/ with YAML front matter
2. VTT caption files in _includes/captions/ named by youtube_id
"""

import os
import json
from datetime import datetime
import shutil


def convert_transcript(transcript_dir):
    """Convert a single transcript folder to Jekyll format."""
    
    # Read metadata
    meta_path = os.path.join(transcript_dir, 'meta.json')
    if not os.path.exists(meta_path):
        print(f"⚠️  Skipping {transcript_dir}: no meta.json found")
        return False
    
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    # Read transcript VTT file
    vtt_path = os.path.join(transcript_dir, 'transcript.vtt')
    if not os.path.exists(vtt_path):
        print(f"⚠️  Skipping {transcript_dir}: no transcript.vtt found")
        return False
    
    # Extract required fields
    youtube_id = meta.get('youtube_id')
    if not youtube_id:
        print(f"⚠️  Skipping {transcript_dir}: no youtube_id in metadata")
        return False
    
    title = meta.get('fulltitle', '')
    author = meta.get('author', 'Garys Economics')
    timestamp = meta.get('timestamp', 0)
    date = datetime.fromtimestamp(timestamp).date().isoformat()
    view_count = meta.get('view_count', 0)
    like_count = meta.get('like_count', 0)
    duration_seconds = meta.get('duration_seconds', 0)
    tags = meta.get('tags', [])
    categories = meta.get('categories', [])
    description = meta.get('description', '')
    thumbnail = meta.get('thumbnail', f'https://i.ytimg.com/vi/{youtube_id}/maxresdefault.jpg')
    
    # Generate post filename (date + slug from folder name)
    folder_name = os.path.basename(transcript_dir)
    # The folder name already has the date prefix, use it as-is
    post_filename = f"{folder_name}.md"
    post_path = os.path.join('_posts', post_filename)
    
    # Generate caption filename
    caption_filename = f"{youtube_id}.vtt"
    caption_path = os.path.join('_includes', 'captions', caption_filename)
    
    # Create _posts directory if it doesn't exist
    os.makedirs('_posts', exist_ok=True)
    
    # Create _includes/captions directory if it doesn't exist
    os.makedirs(os.path.join('_includes', 'captions'), exist_ok=True)
    
    # Check if post already exists
    if os.path.exists(post_path):
        print(f"⏭️  Skipping {folder_name}: post already exists")
        return False
    
    # Create Jekyll post with front matter
    with open(post_path, 'w', encoding='utf-8') as f:
        f.write('---\n')
        f.write('layout: post\n')
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
            # For multi-line descriptions, use YAML literal block scalar
            if '\n' in description or len(description) > 80:
                f.write('description: |\n')
                for line in description.split('\n'):
                    f.write(f'  {line}\n')
            else:
                f.write(f'description: {description}\n')
        
        f.write(f'thumbnail: {thumbnail}\n')
        f.write(f'channel_url: https://www.youtube.com/@garyseconomics\n')
        f.write(f'caption_file: captions/{caption_filename}\n')
        f.write('---\n')
    
    # Copy VTT file to captions directory
    shutil.copy2(vtt_path, caption_path)
    
    print(f"✅ Converted {folder_name}")
    return True


def main():
    """Main conversion function."""
    
    # Change to repository root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    os.chdir(repo_root)
    
    transcripts_dir = 'transcripts'
    
    if not os.path.exists(transcripts_dir):
        print(f"❌ Error: {transcripts_dir} directory not found")
        return
    
    # Get all transcript folders
    transcript_folders = sorted([
        os.path.join(transcripts_dir, d) 
        for d in os.listdir(transcripts_dir)
        if os.path.isdir(os.path.join(transcripts_dir, d))
    ])
    
    print(f"Found {len(transcript_folders)} transcript folders")
    print("=" * 60)
    
    converted_count = 0
    skipped_count = 0
    
    for folder in transcript_folders:
        if convert_transcript(folder):
            converted_count += 1
        else:
            skipped_count += 1
    
    print("=" * 60)
    print(f"✅ Conversion complete!")
    print(f"   Converted: {converted_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Total: {len(transcript_folders)}")


if __name__ == '__main__':
    main()
