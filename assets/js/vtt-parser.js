// VTT Parser - Pure JavaScript
;(() => {
  // Parse VTT format transcript
  function parseVTT(vttText) {
    const lines = vttText.split("\n")
    const entries = []
    let currentEntry = null

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim()

      // Skip WEBVTT header and empty lines
      if (line === "" || line.startsWith("WEBVTT") || line.startsWith("NOTE")) {
        continue
      }

      // Check if line contains timestamp
      if (line.includes("")) {
        const timestamps = line.split("").map((t) => t.trim())
        currentEntry = {
          start: timestamps[0],
          end: timestamps[1],
          text: "",
        }
      } else if (currentEntry && line !== "") {
        // Add text to current entry
        currentEntry.text += (currentEntry.text ? " " : "") + line
      } else if (currentEntry && line === "") {
        // Entry complete
        entries.push(currentEntry)
        currentEntry = null
      }
    }

    // Add last entry if exists
    if (currentEntry) {
      entries.push(currentEntry)
    }

    return entries
  }

  // Convert timestamp to seconds
  function timestampToSeconds(timestamp) {
    const parts = timestamp.split(":")
    if (parts.length === 3) {
      const hours = Number.parseInt(parts[0], 10)
      const minutes = Number.parseInt(parts[1], 10)
      const seconds = Number.parseFloat(parts[2])
      return hours * 3600 + minutes * 60 + seconds
    } else if (parts.length === 2) {
      const minutes = Number.parseInt(parts[0], 10)
      const seconds = Number.parseFloat(parts[1])
      return minutes * 60 + seconds
    }
    return 0
  }

  // Render transcript entries as HTML
  function renderTranscript(entries, youtubeUrl) {
    const container = document.getElementById("transcript-content")
    if (!container) return

    // Clear existing content
    container.innerHTML = ""

    entries.forEach((entry, index) => {
      const lineDiv = document.createElement("div")
      lineDiv.className = "transcript-line"
      lineDiv.dataset.index = index

      // Create timestamp link
      const timestampLink = document.createElement("a")
      timestampLink.className = "transcript-timestamp"
      timestampLink.textContent = entry.start
      timestampLink.href = "#"

      if (youtubeUrl) {
        const seconds = Math.floor(timestampToSeconds(entry.start))
        const youtubeTimestampUrl = youtubeUrl + (youtubeUrl.includes("?") ? "&" : "?") + "t=" + seconds + "s"
        timestampLink.href = youtubeTimestampUrl
        timestampLink.target = "_blank"
        timestampLink.rel = "noopener noreferrer"
      }

      // Create text paragraph
      const textP = document.createElement("p")
      textP.className = "transcript-text"
      textP.textContent = entry.text

      lineDiv.appendChild(timestampLink)
      lineDiv.appendChild(textP)
      container.appendChild(lineDiv)
    })
  }

  // Search functionality
  function setupSearch(entries) {
    const searchInput = document.getElementById("search-input")
    const clearBtn = document.getElementById("clear-search")

    if (!searchInput) return

    searchInput.addEventListener("input", function () {
      const query = this.value.toLowerCase().trim()

      if (query) {
        clearBtn.style.display = "block"
        highlightSearchResults(entries, query)
      } else {
        clearBtn.style.display = "none"
        clearHighlights()
      }
    })

    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        searchInput.value = ""
        this.style.display = "none"
        clearHighlights()
      })
    }
  }

  // Highlight search results
  function highlightSearchResults(entries, query) {
    const lines = document.querySelectorAll(".transcript-line")

    lines.forEach((line, index) => {
      const textP = line.querySelector(".transcript-text")
      const originalText = entries[index].text

      if (originalText.toLowerCase().includes(query)) {
        // Show line
        line.style.display = "block"

        // Highlight matching text
        const regex = new RegExp("(" + escapeRegex(query) + ")", "gi")
        const highlightedText = originalText.replace(regex, '<span class="highlight">$1</span>')
        textP.innerHTML = highlightedText
      } else {
        // Hide non-matching lines
        line.style.display = "none"
      }
    })
  }

  // Clear highlights
  function clearHighlights() {
    const lines = document.querySelectorAll(".transcript-line")
    lines.forEach((line) => {
      line.style.display = "block"
      const textP = line.querySelector(".transcript-text")
      textP.innerHTML = textP.textContent
    })
  }

  // Escape regex special characters
  function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  }

  // Initialize on page load
  document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("transcript-content")
    if (!container) return

    // Get VTT content from the page
    const vttContent = container.textContent.trim()
    const youtubeUrl = container.dataset.youtubeUrl

    // Parse and render
    if (vttContent.startsWith("<p>WEBVTT")) {
      const entries = parseVTT(vttContent)
      renderTranscript(entries, youtubeUrl)
      setupSearch(entries)
    }
  })
})()
