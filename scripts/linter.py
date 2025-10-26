#!/usr/bin/env python3
"""
Linter to check consistency between _posts and _includes/captions.

This script verifies that:
1. For each VTT file in _includes/captions, there is a corresponding _posts file
   with the same YouTube ID in its frontmatter
2. For each _posts file, there is at least one VTT file in _includes/captions
   with the YouTube ID as the base name
"""

import os
import re
import sys
import traceback
from pathlib import Path


def extract_youtube_id_from_vtt_filename(filename):
    """Extract YouTube ID from VTT filename.
    
    Files can be named like:
    - VIDEO_ID.vtt (primary)
    - VIDEO_ID.lang.vtt (language variants)
    """
    # Remove .vtt extension
    name = filename.replace('.vtt', '')
    
    # If it has a language suffix (e.g., VIDEO_ID.en-GB), split and take first part
    parts = name.split('.')
    return parts[0]


def extract_youtube_id_from_post(post_path):
    """Extract YouTube ID from post file's frontmatter."""
    try:
        with open(post_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract frontmatter (between --- markers)
        frontmatter_match = re.search(r'^---\s*\n(.*?)\n---', content, re.MULTILINE | re.DOTALL)
        if not frontmatter_match:
            return None
        
        frontmatter = frontmatter_match.group(1)
        
        # Extract youtube_id field
        youtube_id_match = re.search(r'^youtube_id:\s*(.+?)\s*$', frontmatter, re.MULTILINE)
        if youtube_id_match:
            return youtube_id_match.group(1).strip()
        
        return None
    except Exception as e:
        print(f"⚠️  Error reading {post_path}: {e}")
        return None


def get_all_vtt_files(captions_dir):
    """Get all VTT files and their base YouTube IDs."""
    vtt_files = {}
    
    if not os.path.exists(captions_dir):
        return vtt_files
    
    for filename in os.listdir(captions_dir):
        if filename.endswith('.vtt'):
            youtube_id = extract_youtube_id_from_vtt_filename(filename)
            if youtube_id not in vtt_files:
                vtt_files[youtube_id] = []
            vtt_files[youtube_id].append(filename)
    
    return vtt_files


def get_all_posts(posts_dir):
    """Get all post files and their YouTube IDs."""
    posts = {}
    
    if not os.path.exists(posts_dir):
        return posts
    
    for filename in os.listdir(posts_dir):
        if filename.endswith('.md'):
            post_path = os.path.join(posts_dir, filename)
            youtube_id = extract_youtube_id_from_post(post_path)
            if youtube_id:
                posts[youtube_id] = filename
    
    return posts


def lint():
    """Run linting checks."""
    # Change to repository root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    os.chdir(repo_root)
    
    captions_dir = os.path.join('_includes', 'captions')
    posts_dir = '_posts'
    
    print("Linting transcript consistency...")
    print("=" * 60)
    
    # Get all VTT files and posts
    vtt_files = get_all_vtt_files(captions_dir)
    posts = get_all_posts(posts_dir)
    
    print(f"📊 Found {len(vtt_files)} unique YouTube IDs in VTT files")
    print(f"📊 Found {len(posts)} posts with YouTube IDs")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # Check 1: For each VTT file, ensure there's a corresponding post
    print("\n🔍 Checking VTT files have corresponding posts...")
    vtt_without_post = []
    for youtube_id, files in vtt_files.items():
        if youtube_id not in posts:
            vtt_without_post.append((youtube_id, files))
            errors.append(f"VTT file(s) {files} for YouTube ID '{youtube_id}' has no corresponding post")
    
    if vtt_without_post:
        print(f"❌ Found {len(vtt_without_post)} VTT file(s) without corresponding posts:")
        for youtube_id, files in vtt_without_post:
            print(f"   - {youtube_id}: {', '.join(files)}")
    else:
        print("✅ All VTT files have corresponding posts")
    
    # Check 2: For each post, ensure there's at least one VTT file
    print("\n🔍 Checking posts have corresponding VTT files...")
    posts_without_vtt = []
    for youtube_id, post_file in posts.items():
        if youtube_id not in vtt_files:
            posts_without_vtt.append((youtube_id, post_file))
            errors.append(f"Post '{post_file}' for YouTube ID '{youtube_id}' has no corresponding VTT file")
    
    if posts_without_vtt:
        print(f"❌ Found {len(posts_without_vtt)} post(s) without corresponding VTT files:")
        for youtube_id, post_file in posts_without_vtt:
            print(f"   - {youtube_id}: {post_file}")
    else:
        print("✅ All posts have corresponding VTT files")
    
    # Check 3: Report on posts with multiple VTT variants
    print("\n📋 Posts with multiple VTT language variants:")
    multi_vtt = [(youtube_id, files) for youtube_id, files in vtt_files.items() if len(files) > 1]
    if multi_vtt:
        for youtube_id, files in multi_vtt:
            print(f"   - {youtube_id}: {', '.join(files)}")
    else:
        print("   (none)")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Linting Summary")
    print("=" * 60)
    
    if errors:
        print(f"❌ Found {len(errors)} error(s):")
        for error in errors:
            print(f"   - {error}")
        print("\n❌ Linting failed!")
        return False
    else:
        print("✅ All checks passed!")
        print(f"   - {len(vtt_files)} YouTube IDs with VTT files")
        print(f"   - {len(posts)} posts with YouTube IDs")
        print(f"   - {len(multi_vtt)} videos with multiple VTT variants")
        return True


def main():
    """Main entry point."""
    try:
        success = lint()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
