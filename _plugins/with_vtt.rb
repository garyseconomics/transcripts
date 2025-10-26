require 'webvtt'

=begin
A Jekyll plugin that reads VTT files (including localized versions) and makes their cues available in the Liquid context.
Usage:
{% with_vtt path/to/file.vtt %}
  {% for cue in cues %}
    {{ cue.start }}, {{ cue.end }}, {{ cue.text }}
  {% endfor %}
{% endwith_vtt %}

The plugin automatically detects and loads all localized versions of a VTT file.
For example, if you specify "captions/video123.vtt", it will also find:
- video123.en.vtt
- video123.fr.vtt
- video123.de.vtt
etc.

Available variables in the Liquid context:
- cues: Array of cues from the default language
- languages: Array of available language objects with 'code', 'name', and 'cues'
- default_language: The language code of the default language
=end

module Jekyll
  class WithVttTag < Liquid::Block
    # Language code to name mapping for common languages
    LANGUAGE_NAMES = {
      'en' => 'English',
      'en-GB' => 'English (UK)',
      'en-US' => 'English (US)',
      'es' => 'Spanish',
      'fr' => 'French',
      'de' => 'German',
      'it' => 'Italian',
      'pt' => 'Portuguese',
      'pt-BR' => 'Portuguese (Brazil)',
      'ru' => 'Russian',
      'ja' => 'Japanese',
      'ko' => 'Korean',
      'zh-Hans' => 'Chinese (Simplified)',
      'zh-Hant' => 'Chinese (Traditional)',
      'ar' => 'Arabic',
      'hi' => 'Hindi',
      'nl' => 'Dutch',
      'pl' => 'Polish',
      'tr' => 'Turkish',
      'sv' => 'Swedish',
      'da' => 'Danish',
      'fi' => 'Finnish',
      'no' => 'Norwegian',
      'cs' => 'Czech',
      'hu' => 'Hungarian',
      'ro' => 'Romanian',
      'el' => 'Greek',
      'he' => 'Hebrew',
      'iw' => 'Hebrew',
      'id' => 'Indonesian',
      'th' => 'Thai',
      'vi' => 'Vietnamese',
      'uk' => 'Ukrainian',
      'ca' => 'Catalan',
      'hr' => 'Croatian',
      'sk' => 'Slovak',
      'bg' => 'Bulgarian',
      'lt' => 'Lithuanian',
      'sl' => 'Slovenian',
      'et' => 'Estonian',
      'lv' => 'Latvian',
      'sr' => 'Serbian',
      'bn' => 'Bengali',
      'ta' => 'Tamil',
      'te' => 'Telugu',
      'mr' => 'Marathi',
      'gu' => 'Gujarati',
      'kn' => 'Kannada',
      'ml' => 'Malayalam',
      'pa' => 'Punjabi',
      'ur' => 'Urdu',
      'fa' => 'Persian',
      'sw' => 'Swahili',
      'ms' => 'Malay',
      'fil' => 'Filipino',
      'af' => 'Afrikaans',
      'sq' => 'Albanian',
      'am' => 'Amharic',
      'hy' => 'Armenian',
      'az' => 'Azerbaijani',
      'eu' => 'Basque',
      'be' => 'Belarusian',
      'bs' => 'Bosnian',
      'my' => 'Burmese',
      'ceb' => 'Cebuano',
      'co' => 'Corsican',
      'eo' => 'Esperanto',
      'fj' => 'Fijian',
      'fy' => 'Frisian',
      'gl' => 'Galician',
      'ka' => 'Georgian',
      'gn' => 'Guarani',
      'ht' => 'Haitian Creole',
      'ha' => 'Hausa',
      'haw' => 'Hawaiian',
      'hmn' => 'Hmong',
      'is' => 'Icelandic',
      'ig' => 'Igbo',
      'ga' => 'Irish',
      'jv' => 'Javanese',
      'kk' => 'Kazakh',
      'km' => 'Khmer',
      'rw' => 'Kinyarwanda',
      'ku' => 'Kurdish',
      'ky' => 'Kyrgyz',
      'lo' => 'Lao',
      'la' => 'Latin',
      'lb' => 'Luxembourgish',
      'mk' => 'Macedonian',
      'mg' => 'Malagasy',
      'mt' => 'Maltese',
      'mi' => 'Maori',
      'mn' => 'Mongolian',
      'ne' => 'Nepali',
      'ny' => 'Nyanja',
      'or' => 'Odia',
      'ps' => 'Pashto',
      'sm' => 'Samoan',
      'gd' => 'Scottish Gaelic',
      'sn' => 'Shona',
      'sd' => 'Sindhi',
      'si' => 'Sinhala',
      'so' => 'Somali',
      'st' => 'Sotho',
      'su' => 'Sundanese',
      'tg' => 'Tajik',
      'tt' => 'Tatar',
      'tk' => 'Turkmen',
      'ug' => 'Uyghur',
      'uz' => 'Uzbek',
      'cy' => 'Welsh',
      'xh' => 'Xhosa',
      'yi' => 'Yiddish',
      'yo' => 'Yoruba',
      'zu' => 'Zulu',
      'ay' => 'Aymara',
      'bho' => 'Bhojpuri',
      'dv' => 'Dhivehi',
      'dz' => 'Dzongkha',
      'ee' => 'Ewe',
      'fo' => 'Faroese',
      'gaa' => 'Ga',
      'gv' => 'Manx',
      'iu' => 'Inuktitut',
      'kha' => 'Khasi',
      'kl' => 'Greenlandic',
      'lg' => 'Luganda',
      'mfe' => 'Mauritian Creole',
      'br' => 'Breton',
      'ba' => 'Bashkir'
    }

    def initialize(tag_name, markup, tokens)
      super
      @file_path = markup.strip
    end

    def render(context)
      file_path = Liquid::Template.parse(@file_path).render(context)
      site = context.registers[:site]
      
      # Find all localized versions of the VTT file
      languages = find_all_languages(site, file_path)
      
      if languages.empty?
        raise "No VTT files found for: #{file_path}"
      end

      # Determine the default language (prefer 'en', then 'en-GB', then first available)
      default_lang = languages.find { |l| l['code'] == 'en' } ||
                     languages.find { |l| l['code'] == 'en-GB' } ||
                     languages.first

      # Set context variables
      context['languages'] = languages
      context['default_language'] = default_lang['code']
      context['cues'] = default_lang['cues']

      super
    end

    def find_all_languages(site, file_path)
      includes_dir = File.join(site.source, '_includes')
      
      # Extract the base path and filename from the provided path
      dir_path = File.dirname(file_path)
      filename = File.basename(file_path)
      
      # Determine the base filename (without language code)
      # Handle patterns like: video.vtt, video.en.vtt, video.en-GB.vtt
      base_name = filename.sub(/\.vtt$/, '')
      
      # If the base_name already has a language code, extract the video ID
      # Pattern: <video_id>.<lang>.vtt or just <video_id>.vtt
      video_id = base_name.split('.').first
      
      # Find all matching VTT files in the directory
      search_pattern = File.join(includes_dir, dir_path, "#{video_id}*.vtt")
      matching_files = Dir.glob(search_pattern)
      
      languages = []
      
      matching_files.each do |file|
        # Extract language code from filename
        # Patterns: video_id.vtt (default), video_id.en.vtt, video_id.en-GB.vtt
        basename = File.basename(file, '.vtt')
        parts = basename.split('.')
        
        # Determine language code
        lang_code = if parts.length == 1
                     # Just video_id.vtt - treat as 'en' (English)
                     'en'
                   elsif parts.length == 2
                     # video_id.lang.vtt
                     parts[1]
                   elsif parts.length >= 3
                     # video_id.lang-region.vtt (e.g., en-GB)
                     parts[1..-1].join('.')
                   else
                     'unknown'
                   end
        
        begin
          vtt = WebVTT.read(file)
          cues = vtt.cues.map do |cue|
            {
              'start' => cue.start_in_sec.to_i,
              'end' => cue.end_in_sec.to_i,
              'timestamp' => format_time(cue.start_in_sec.to_i),
              'text' => cue.text
            }
          end
          
          # Get language name from our mapping, or use the code itself
          lang_name = LANGUAGE_NAMES[lang_code] || lang_code.upcase
          
          languages << {
            'code' => lang_code,
            'name' => lang_name,
            'cues' => cues
          }
        rescue => e
          # Skip files that can't be parsed
          Jekyll.logger.warn "Warning: Could not parse VTT file #{file}: #{e.message}"
        end
      end
      
      # Sort languages: English first, then alphabetically by name
      languages.sort_by do |lang|
        case lang['code']
        when 'en' then '0'
        when 'en-GB' then '1'
        when 'en-US' then '2'
        else "3#{lang['name']}"
        end
      end
    end

    def format_time(seconds)
      hours = seconds / 3600
      minutes = (seconds % 3600) / 60
      secs = seconds % 60
      sprintf("%02d:%02d:%02d", hours, minutes, secs)
    end
  end
end

Liquid::Template.register_tag('with_vtt', Jekyll::WithVttTag)
