# RT Search Issues Analysis

## Problem Investigation

Based on the code review and scraping logs, the RT search implementation has several issues that can cause movies to not be found even when they exist on RT.

## Identified Issues

### 1. **Search Query Encoding**
**Location**: `_search_via_selenium()` line ~164
```python
search_url = f"{self.BASE_URL}/search?search={title}"
```

**Problem**: Title is not URL-encoded. Titles with special characters like:
- "Once Upon a Time... in Hollywood" (dots, spaces)
- "Don't Worry Darling" (apostrophe)
- "Murder Mystery 2" (numbers)

May not be properly encoded in the URL.

**Fix**: Use `urllib.parse.quote()` to encode the title

---

### 2. **Fuzzy Matching Too Strict**
**Location**: `_titles_match()` lines ~242-277

**Current logic**:
```python
if search_norm == result_norm:
    return True
if search_norm in result_norm or result_norm in search_norm:
    return True
return False
```

**Problems**:
- Fails on "Once Upon a Time in Hollywood" vs "Once Upon a Time... in Hollywood"
- Fails on sequels: "Murder Mystery" vs "Murder Mystery 2"
- Fails when RT uses different formats

**Examples of failures**:
- Search: "Space Sweepers" → RT: "Space Sweeper" (singular vs plural)
- Search: "The Ritual" → RT might just be "Ritual"
- Search: "Murder Mystery 2" → RT might be "Murder Mystery 2" or "Murder Mystery: Part 2"

**Fix**: Use fuzzy string matching (Levenshtein distance or similar)

---

### 3. **Article Removal Too Aggressive**
**Location**: `_titles_match()` normalize function

**Current**:
```python
for article in ['the ', 'a ', 'an ']:
    if title.startswith(article):
        title = title[len(article):]
```

**Problem**: Only removes articles at the start, but RT might:
- Include them when search doesn't: "The Ritual" vs "Ritual"
- Put them at the end: "Ritual, The"
- Use them inconsistently

---

### 4. **Wait Time Too Short**
**Location**: `_search_via_selenium()` line ~168

```python
wait = WebDriverWait(self.driver, 10)
wait.until(EC.presence_of_element_located((By.TAG_NAME, "search-page-media-row")))
```

**Problem**: 10 seconds might not be enough for slow connections or slow RT responses. RT's search page is JavaScript-heavy.

**Fix**: Increase to 15-20 seconds

---

### 5. **No Logging of What Was Actually Found**
**Location**: `_search_via_selenium()`

**Problem**: When search fails, we don't log what results were actually found. This makes debugging impossible.

**Fix**: Log all results found, not just the match

---

### 6. **Year Matching Too Strict for Some Cases**
**Location**: `_search_via_selenium()` lines ~214-220

```python
if year and result_year:
    try:
        result_year_int = int(result_year)
        if abs(result_year_int - year) > 1:  # Allow 1 year difference
            logger.debug(f"Year mismatch: {result_title} ({result_year} vs {year})")
            continue
```

**Problem**: ±1 year is good, but some movies have:
- Festival release year vs wide release year (can be 2+ years apart)
- International release year differences

**Fix**: Make year tolerance configurable, increase to ±2 years

---

## Recommended Fixes

### Priority 1 (Critical):
1. ✅ Add URL encoding for search query
2. ✅ Improve fuzzy matching (use better string similarity)
3. ✅ Log all search results for debugging

### Priority 2 (Important):
4. ✅ Increase wait time to 15 seconds
5. ✅ Increase year tolerance to ±2 years
6. ✅ Better article handling (remove from both ends, check "The X" vs "X, The")

### Priority 3 (Nice to have):
7. Try multiple search variations if first fails
8. Cache successful slug lookups
9. Add manual override mapping for known problem movies

---

## Testing Needed

After fixes, test these known difficult cases:
- "Once Upon a Time... in Hollywood" (2019) - dots and ellipsis
- "Space Sweepers" (2021) - might be "Space Sweeper" on RT
- "Don't Worry Darling" (2022) - apostrophe
- "Murder Mystery 2" (2023) - sequel numbering

---

## Implementation Plan

1. Fix URL encoding
2. Add detailed debug logging
3. Improve string matching with similarity scoring
4. Increase wait time and year tolerance
5. Test with all database movies
6. Document which movies still fail and why
