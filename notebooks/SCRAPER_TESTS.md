# Scraper Testing Notebook

## Purpose
Test ONLY the web scrapers - no sentiment analysis, no SQL complexity.
This notebook validates that all scrapers work correctly and return proper data structures.

## What We Test
1. ✅ Gemini AI Search Term Generator
2. ✅ IMDb Rating Scraper
3. ✅ IMDb Review Scraper
4. ✅ Reddit Scraper (optional - needs API keys)
5. ✅ Twitter Scraper (optional - uses snscrape)

## What We DON'T Test
- ❌ Sentiment analysis (handled by NLP team)
- ❌ Review weighting (handled by NLP team)
- ❌ Complex database operations
- ❌ Recommendation models

---

## Step 1: Setup & Imports
