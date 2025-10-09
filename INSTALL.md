# Installation

This is a Jekyll-based website for hosting a FAQ and displaying video transcripts from the YouTube channel [@garyseconomics](https://www.youtube.com/@garyseconomics)

## Setup

1. Install [Ruby](https://www.ruby-lang.org/en/downloads/) and then Jekyll:

    gem install bundler jekyll

2. Install dependencies:

    bundle install

4. Run the development server:

    bundle exec jekyll serve --incremental

5. Open your browser to [localhost:4000](http://localhost:4000)

## Adding New Transcripts

Create a new file in `_posts/` with the filename pattern `YYYY-MM-DD-title.md`, with a Jekyll frontmatter including at least the following 6 keys and then VTT in the body.

```md
---
layout: post
title: "Video Title"
date: 2024-03-15
youtube_url: "VIDEO_ID"
duration: "12:34"
tags: [tag1, tag2, tag3]
---

WEBVTT

00:00:00.000  00:00:05.000
Your transcript text here...

00:00:05.000  00:00:10.000
More transcript text...
```

This data can be extracted from YouTube using tools like [github.com/dbeley/youtube_extract](https://github.com/dbeley/youtube_extract) and [github.com/ytdl-org/youtube-dl](https://github.com/ytdl-org/youtube-dl)

For example, to list the subs available from a video, run

    yt-dlp --skip-download --list-subs  "https://youtu.be/EiblHqbpXHs"

To download the English subtitles in VTT format, run

    yt-dlp --skip-download --write-subs --write-auto-subs --sub-langs "en" --sub-format "vtt"  "https://youtu.be/EiblHqbpXHs";

