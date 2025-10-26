# Multilingual VTT Support

This document explains the multilingual transcript support feature added to the site.

## Overview

The site now supports displaying transcripts in multiple languages when multiple localized VTT files are available for a video. This feature automatically detects all available language variants and provides a user-friendly language selector.

## How It Works

### For Videos with Multiple Languages

When a video has multiple language variants (e.g., `Ja9dTjY3uWU.en.vtt`, `Ja9dTjY3uWU.fr.vtt`, `Ja9dTjY3uWU.de.vtt`), the system:

1. **Auto-detects all languages**: The `with_vtt` plugin scans for all VTT files matching the video ID pattern
2. **Displays language selector**: A dropdown appears above the transcript showing all available languages
3. **Defaults to English**: If available, English (`en`) is selected by default, otherwise the first available language
4. **Remembers preference**: The user's language choice is stored in localStorage and restored on subsequent visits

### For Videos with Single Language

For videos with only one VTT file (e.g., `8BzLx-6WNP8.en-GB.vtt`):
- No language selector is shown
- The transcript is displayed directly
- Fully backward compatible with existing posts

## File Naming Convention

VTT files should follow this naming pattern:
```
<video_id>.<language_code>.vtt
```

Examples:
- `Ja9dTjY3uWU.en.vtt` - English
- `Ja9dTjY3uWU.fr.vtt` - French
- `Ja9dTjY3uWU.de.vtt` - German
- `Ja9dTjY3uWU.en-GB.vtt` - English (UK)
- `Ja9dTjY3uWU.zh-Hans.vtt` - Chinese (Simplified)

## Supported Languages

The plugin includes language name mappings for 150+ languages, including:
- Major languages: English, Spanish, French, German, Italian, Portuguese, Russian, Japanese, Korean, Chinese (Simplified & Traditional), Arabic, Hindi
- Regional variants: en-GB, en-US, pt-BR, zh-Hans, zh-Hant
- Many other languages from around the world

Unknown language codes will be displayed in uppercase (e.g., "XYZ" for `xyz` code).

## Usage in Posts

Posts continue to use the same `caption_file` format:

```yaml
---
title: My Video Title
youtube_id: Ja9dTjY3uWU
caption_file: captions/Ja9dTjY3uWU.vtt
---
```

The plugin automatically finds all language variants based on the video ID, regardless of whether the base `.vtt` file exists or not.

## User Features

1. **Language Selector**: Dropdown menu to switch between available languages
2. **Persistent Preference**: Selected language is saved in browser localStorage
3. **Smart Search**: Search only within the currently selected language
4. **Auto-clear**: Search is cleared when switching languages for better UX

## Technical Details

### Plugin (`_plugins/with_vtt.rb`)

The plugin provides these Liquid context variables:
- `languages`: Array of language objects, each containing:
  - `code`: Language code (e.g., "en", "fr", "de")
  - `name`: Human-readable language name (e.g., "English", "French", "German")
  - `cues`: Array of transcript cues for this language
- `default_language`: The default language code (usually "en")
- `cues`: Cues from the default language (for backward compatibility)

### Layout (`_layouts/post.html`)

The layout:
- Shows language selector only when multiple languages are available
- Renders all languages with only the default visible initially
- Includes JavaScript to handle language switching
- Integrates with existing search functionality

### Search (`assets/js/search.js`)

Search has been updated to:
- Only search within the currently visible language transcript
- Work seamlessly with language switching

## Example: Video with 63 Languages

The video ID `Ja9dTjY3uWU` demonstrates the full capability with 63 different language translations:
- English, French, German, Spanish, Italian, Portuguese, Russian
- Japanese, Korean, Chinese (Simplified & Traditional)
- Arabic, Hindi, Bengali, and many more
- Regional variants like en-GB, zh-Hans, zh-Hant

## Backward Compatibility

The implementation is fully backward compatible:
- Existing posts continue to work without modification
- Videos with single VTT files display normally without a language selector
- The `cues` variable is still available for simple templates

## Future Enhancements

Potential improvements could include:
- Language code in URL for direct linking to specific language
- Language auto-detection based on browser preferences
- Translation quality indicators
- Side-by-side language comparison
