require 'webvtt'

=begin
A Jekyll plugin that reads a VTT file and makes its cues available in the Liquid context.
Usage:
{% with_vtt path/to/file.vtt %}
  {% for cue in cues %}
    {{ cue.start }}, {{ cue.end }}, {{ cue.text }}
  {% endfor %}
{% endwith_vtt %}
=end

module Jekyll
  class WithVttTag < Liquid::Block
    def initialize(tag_name, markup, tokens)
      super
      @file_path = markup.strip
    end

    def render(context)
      file_path = Liquid::Template.parse(@file_path).render(context)
      site = context.registers[:site]
      file = File.join(site.source, '_includes', file_path)
      unless File.exist?(file)
        raise "VTT file not found: #{file_path}"
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

        context['cues'] = cues
      rescue => e
        raise "Error parsing VTT: #{e.message}"
      end

      super
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
