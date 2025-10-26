;(() => {
  function setupSearch() {
    const searchInput = document.getElementById('search-input');
    const clearBtn = document.getElementById('clear-search');

    if (!searchInput) return;

    searchInput.addEventListener('input', function () {
      const query = this.value.toLowerCase().trim();
      if (query) {
        if(clearBtn) clearBtn.style.display = 'block';
        highlightSearchResults(query);
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

  function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function getVisibleTranscriptLines() {
    // Get only the lines from the currently visible language
    const visibleTranscript = document.querySelector('.transcript-language:not([style*="display: none"])');
    if (visibleTranscript) {
      return visibleTranscript.querySelectorAll('.transcript-line');
    }
    // Fallback to all lines if no language selector is present
    return document.querySelectorAll('.transcript-line');
  }

  function highlightSearchResults(query) {
    const lines = getVisibleTranscriptLines();

    lines.forEach((line) => {
      const textElement = line.querySelector('.transcript-text');
      const originalText = textElement.textContent;
      if (originalText.toLowerCase().includes(query)) {
        line.style.display = '';
        const regex = new RegExp('(' + escapeRegex(query) + ')', 'gi');
        const highlightedText = originalText.replace(regex, '<span class="highlight">$1</span>');
        textElement.innerHTML = highlightedText;
      } else {
        line.style.display = 'none';
      }
    });
  }

  function clearHighlights() {
    const lines = getVisibleTranscriptLines();
    lines.forEach((line) => {
      line.style.display = '';
      const textElement = line.querySelector('.transcript-text');
      textElement.innerHTML = textElement.textContent; // Reset to original text
    });
  }

  setupSearch();
})();
