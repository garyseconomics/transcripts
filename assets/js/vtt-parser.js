// VTT Parser - Pure JavaScript
;(() => {
  // Parse VTT format transcript
  function parseVTT(vttText) {
    const lines = vttText.split('\n');
    const entries = [];
    let currentEntry = null;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      // Skip WEBVTT header, metadata, and empty lines
      if (line === '' || line.startsWith('WEBVTT') || line.startsWith('NOTE') || line.startsWith('Kind:') || line.startsWith('Language:')) {
        continue;
      }

      // Check if line contains a timestamp
      if (line.includes('-->')) {
        // If there was a previous entry that hasn't been saved, save it now.
        if (currentEntry) {
            entries.push(currentEntry);
        }

        const timestamps = line.split('-->').map((t) => t.trim());
        currentEntry = {
          start: timestamps[0],
          end: timestamps[1],
          text: '',
        };
      } else if (currentEntry && line !== '') {
        // Add text to the current entry
        currentEntry.text += (currentEntry.text ? ' ' : '') + line;
      }
    }

    // Add the last entry if it exists
    if (currentEntry) {
      entries.push(currentEntry);
    }

    return entries;
  }

  // Convert timestamp to seconds
  function timestampToSeconds(timestamp) {
    // Handle timestamps with milliseconds
    const [time, milliseconds] = timestamp.split('.');
    const parts = time.split(':');
    let seconds = 0;

    if (parts.length === 3) {
      seconds = parseInt(parts[0], 10) * 3600 + parseInt(parts[1], 10) * 60 + parseInt(parts[2], 10);
    } else if (parts.length === 2) {
      seconds = parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
    }

    if (milliseconds) {
      seconds += parseFloat(`0.${milliseconds}`);
    }

    return seconds;
  }

  // Render transcript entries as HTML
  function renderTranscript(entries, youtubeUrl) {
    const container = document.getElementById('transcript-content');
    if (!container) return;

    // Clear existing content
    container.innerHTML = '';

    entries.forEach((entry, index) => {
      const lineDiv = document.createElement('div');
      lineDiv.className = 'transcript-line';
      lineDiv.dataset.index = index;

      // Create timestamp link
      const timestampLink = document.createElement('a');
      timestampLink.className = 'transcript-timestamp';
      timestampLink.textContent = entry.start.split('.')[0]; // Display without milliseconds
      timestampLink.href = '#';

      if (youtubeUrl) {
        const seconds = Math.floor(timestampToSeconds(entry.start));
        const youtubeTimestampUrl = youtubeUrl + (youtubeUrl.includes('?') ? '&' : '?') + 't=' + seconds + 's';
        timestampLink.href = youtubeTimestampUrl;
        timestampLink.target = '_blank';
        timestampLink.rel = 'noopener noreferrer';
      }

      // Create text paragraph
      const textP = document.createElement('p');
      textP.className = 'transcript-text';
      textP.textContent = entry.text;

      lineDiv.appendChild(timestampLink);
      lineDiv.appendChild(textP);
      container.appendChild(lineDiv);
    });
  }

  // Search functionality
  function setupSearch(entries) {
    const searchInput = document.getElementById('search-input');
    const clearBtn = document.getElementById('clear-search');

    if (!searchInput) return;

    searchInput.addEventListener('input', function () {
      const query = this.value.toLowerCase().trim();

      if (query) {
        if(clearBtn) clearBtn.style.display = 'block';
        highlightSearchResults(entries, query);
      } else {
        if(clearBtn) clearBtn.style.display = 'none';
        clearHighlights();
      }
    });

    if (clearBtn) {
      clearBtn.addEventListener('click', function () {
        searchInput.value = '';
        this.style.display = 'none';
        clearHighlights();
      });
    }
  }

  // Highlight search results
  function highlightSearchResults(entries, query) {
    const lines = document.querySelectorAll('.transcript-line');

    lines.forEach((line, index) => {
      const textP = line.querySelector('.transcript-text');
      const originalText = entries[index].text;

      if (originalText.toLowerCase().includes(query)) {
        // Show line
        line.style.display = 'flex'; // Use flex to align items properly

        // Highlight matching text
        const regex = new RegExp('(' + escapeRegex(query) + ')', 'gi');
        const highlightedText = originalText.replace(regex, '<span class="highlight">$1</span>');
        textP.innerHTML = highlightedText;
      } else {
        // Hide non-matching lines
        line.style.display = 'none';
      }
    });
  }

  // Clear highlights
  function clearHighlights() {
    const lines = document.querySelectorAll('.transcript-line');
    lines.forEach((line) => {
      line.style.display = 'flex'; // Use flex to align items properly
      const textP = line.querySelector('.transcript-text');
      // Restore original text from entry to avoid issues with innerHTML
      const entryIndex = parseInt(line.dataset.index, 10);
      // This part requires access to entries, simplified here by just using textContent
      if (textP) {
         textP.innerHTML = textP.textContent;
      }
    });
  }

  // Escape regex special characters
  function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  // Initialize on page load
  document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('transcript-content');
    if (!container) return;

    // Get VTT content from the page
    const vttContent = container.textContent.trim();
    const youtubeUrl = container.dataset.youtubeUrl;
    
    // Check if the content looks like a VTT file
    if (vttContent.includes('WEBVTT')) {
      const entries = parseVTT(vttContent);
      renderTranscript(entries, youtubeUrl);
      setupSearch(entries);
    } else {
        console.error("Could not find WEBVTT content in the container.");
    }
  });
})();
