# Manual Testing Guide for Multilingual VTT Support

## Prerequisites
- Jekyll development environment set up
- Repository cloned locally
- Test post created: `_posts/2025-10-26-test-multilingual-transcript.md`

## Test Cases

### Test 1: Language Detection
**Objective**: Verify that the plugin correctly detects all 63 language files for video `Ja9dTjY3uWU`

**Steps**:
1. Build the site: `bundle exec jekyll build`
2. Check the build output for errors related to VTT parsing
3. Look for warnings about unparseable VTT files

**Expected Result**:
- Build completes successfully
- No errors about missing VTT files
- May see warnings for any corrupted VTT files (acceptable)

### Test 2: Language Selector Display
**Objective**: Verify that the language selector appears and contains all languages

**Steps**:
1. Build and serve the site: `bundle exec jekyll serve`
2. Navigate to the test post: `/transcript/test-multilingual-transcript/`
3. Locate the language selector dropdown above the transcript

**Expected Result**:
- Language selector dropdown is visible
- Dropdown contains all available languages
- "English" is selected by default
- Languages are sorted with English variants first, then alphabetically

### Test 3: Language Switching
**Objective**: Verify that switching languages updates the displayed transcript

**Steps**:
1. On the test post page, note the first few lines of the transcript
2. Select "French" from the language dropdown
3. Observe the transcript content

**Expected Result**:
- Transcript content changes to French
- Timestamps remain the same
- French text is visible and properly formatted

### Test 4: Language Preference Persistence
**Objective**: Verify that language preference is saved and restored

**Steps**:
1. On the test post page, select a non-English language (e.g., "German")
2. Refresh the page
3. Observe which language is selected

**Expected Result**:
- Selected language (German) is automatically restored
- Transcript displays in German immediately

### Test 5: Search Functionality
**Objective**: Verify that search works within the selected language

**Steps**:
1. Select "English" as the language
2. Enter a search term that appears in the English transcript (e.g., "economics")
3. Observe the search results
4. Switch to "French"
5. Observe what happens to the search

**Expected Result**:
- English results are highlighted when English is selected
- Search clears automatically when switching to French
- Search input is empty after language switch

### Test 6: Backward Compatibility
**Objective**: Verify that existing posts with single VTT files still work

**Steps**:
1. Navigate to an existing post (e.g., `/transcript/making-money-my-first-bonus-investment-advice-a-warning/`)
2. Check if the transcript displays correctly
3. Check if there's a language selector

**Expected Result**:
- Transcript displays normally
- Language selector appears if multiple languages exist, otherwise hidden
- No JavaScript errors in console

### Test 7: Mobile Responsiveness
**Objective**: Verify that the language selector works on mobile devices

**Steps**:
1. Open the test post on a mobile device or resize browser to mobile width
2. Locate the language selector
3. Try switching languages

**Expected Result**:
- Language selector is visible and usable on mobile
- Dropdown is properly styled for mobile
- Language switching works correctly

### Test 8: URL Direct Access
**Objective**: Verify that the page loads correctly with saved language preference

**Steps**:
1. Select a non-default language (e.g., "Japanese")
2. Copy the page URL
3. Open the URL in a new browser tab/window (same browser)

**Expected Result**:
- Page loads with Japanese selected
- Transcript displays in Japanese
- No flash of English content before switching

### Test 9: Multiple Browser Sessions
**Objective**: Verify that language preferences are browser-specific

**Steps**:
1. In Browser A, select "French"
2. In Browser B (different browser/incognito), visit the same page

**Expected Result**:
- Browser A shows French
- Browser B shows default (English)
- Preferences are independent

### Test 10: Performance with Many Languages
**Objective**: Verify that loading 63 languages doesn't cause performance issues

**Steps**:
1. Open browser developer tools (Network tab)
2. Load the test post page
3. Monitor load time and network requests
4. Check JavaScript console for errors

**Expected Result**:
- Page loads in reasonable time (< 3 seconds on average connection)
- No excessive network requests
- No JavaScript errors
- Language switching is instant (< 100ms)

## Automated Testing

For automated testing, run:
```bash
# Test plugin logic
ruby /tmp/test_vtt_plugin.rb

# Test backward compatibility
ruby /tmp/test_backward_compat.rb
```

## Debugging Tips

If issues occur:

1. **Check VTT file format**: Ensure VTT files are valid WebVTT format
2. **Check file naming**: Verify files follow `<video_id>.<lang>.vtt` pattern
3. **Check browser console**: Look for JavaScript errors
4. **Check Jekyll build output**: Look for plugin errors or warnings
5. **Clear localStorage**: Try `localStorage.clear()` in console to reset preferences
6. **Check file permissions**: Ensure VTT files are readable

## Success Criteria

All tests should pass with:
- ✅ No build errors
- ✅ All 63 languages detected and selectable
- ✅ Language switching works smoothly
- ✅ Search works correctly with language selector
- ✅ Preferences persist across page loads
- ✅ Backward compatibility maintained
- ✅ No performance degradation
- ✅ Mobile responsive
