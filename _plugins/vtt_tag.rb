require 'webvtt'

module Jekyll
  class VttIncludeTag < Liquid::Tag
    def initialize(tag_name, inputs, tokens)
      super
      @inputs = inputs.strip
      @file_path, @youtube_url = @inputs.split(',').map(&:strip)
    end

    def render(context)
      file_path = Liquid::Template.parse(@file_path).render(context)
      youtube_url = Liquid::Template.parse(@youtube_url).render(context)
      site = context.registers[:site]
      file = File.join(site.source, '_includes', file_path)
      unless File.exist?(file)
        raise "VTT file not found: #{file_path}"
      end

      begin
        vtt = WebVTT.read(file)
        subtitles = vtt.cues.map do |cue|
          {
            start: cue.start_in_sec.to_i,
            end: cue.end_in_sec.to_i,
            text: cue.text
          }
        end
        render_subtitles(subtitles, youtube_url)
      rescue => e
        raise "Error parsing VTT: #{e.message}"
      end
    end

    private
    def render_subtitles(subtitles, youtube_url)
      html = '<div>'
      subtitles.each do |sub|
        escaped_text = sub[:text].gsub('<', '&lt;').gsub('>', '&gt;')
        html += <<~HTML
          <div class="transcript-line">
            <a class="transcript-timestamp" href="#{youtube_url}&t=#{sub[:start]}s" target="_blank" rel="noopener noreferrer">#{format_time(sub[:start])}</a>
            <p class="transcript-text">#{escaped_text}</p>
          </div>
        HTML
      end
      html += '</div>'
      html
    end

    def format_time(seconds)
      hours = seconds / 3600
      minutes = (seconds % 3600) / 60
      secs = seconds % 60
      sprintf("%02d:%02d:%02d", hours, minutes, secs)
    end
  end
end

Liquid::Template.register_tag('vtt_include', Jekyll::VttIncludeTag)
