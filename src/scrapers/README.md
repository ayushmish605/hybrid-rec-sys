# Scrapers Module

## 🎯 YOUR RESPONSIBILITY

**Team**: Web Scraping  
**Status**: COMPLETE AND WORKING ✅  
**Dependencies**: None (scrapers are independent)

---

## Purpose
Collect movie data from multiple web sources. Scrapers return data structures - they DON'T handle sentiment analysis or complex database operations.

---

## What Scrapers Do ✅

### Your Job:
1. Fetch data from web sources (IMDb, Reddit, Twitter, etc.)
2. Parse HTML/JSON responses into clean data structures
3. Handle rate limiting and errors
4. Return dictionaries/lists with standardized formats

### NOT Your Job:
- ❌ Sentiment analysis (NLP team handles this)
- ❌ Review quality weighting (NLP team handles this)
- ❌ Complex database operations (database team handles this)
- ❌ Recommendation algorithms (ML team handles this)

---

## Components

### 1. `gemini_search.py` - AI-Powered Search Term Generator ✅

**Status**: WORKING  
**Purpose**: Generate smart search terms using Google Gemini AI

**Input:**
```python
title = "Inception"
year = 2010
genres = ["Action", "Sci-Fi", "Thriller"]
overview = "A thief who steals corporate secrets..."
```

**Output:**
```python
{
    'reddit': ['Inception discussion', 'Inception analysis reddit', ...],
    'twitter': ['#Inception', '#InceptionMovie', ...],
    'imdb': ['Inception', 'Inception 2010', ...],
    'general': ['Inception review', 'Inception explained', ...]
}
```

**Usage:**
```python
from scrapers.gemini_search import GeminiSearchTermGenerator

gemini = GeminiSearchTermGenerator()
terms = gemini.generate_search_terms(title, year, genres, overview)
```

**Requirements:**
- `GEMINI_API_KEY` in `.env` file
- Google Generative AI Python SDK

---

### 2. `imdb_scraper.py` - IMDb Rating & Review Scraper ✅

**Status**: WORKING  
**Purpose**: Scrape ratings and reviews from IMDb

#### Method 1: `scrape_movie_rating()` - Get Just the Rating

**Input:**
```python
title = "Inception"
year = 2010
```

**Output:**
```python
{
    'rating': 8.8,
    'vote_count': 2400000,
    'imdb_id': 'tt1375666'
}
```

**Usage:**
```python
from scrapers.imdb_scraper import IMDbScraper

imdb = IMDbScraper(rate_limit=2.0)  # 2 seconds between requests
rating_data = imdb.scrape_movie_rating(title="Inception", year=2010)
```

#### Method 2: `scrape_movie_reviews()` - Get Full Reviews

**Input:**
```python
title = "Inception"
year = 2010
max_reviews = 50
```

**Output:**
```python
[
    {
        'source': 'imdb',
        'source_id': 'imdb_rw1234567',
        'imdb_id': 'tt1375666',
        'title': 'A Masterpiece',
        'text': 'This movie is absolutely incredible...',
        'rating': 10.0,
        'author': 'john_smith',
        'review_date': datetime(2010, 7, 20),
        'helpful_count': 542,
        'review_length': 850,
        'word_count': 150,
        'scraped_at': datetime(2024, 12, 7)
    },
    # ... more reviews
]
```

**Usage:**
```python
reviews = imdb.scrape_movie_reviews(
    title="Inception",
    year=2010,
    max_reviews=50
)
```

**Features:**
- Automatic movie search by title/year
- Rate limiting (default 2 seconds between requests)
- Pagination support for large review counts
- Error handling and logging

**Requirements:**
- No API key needed (web scraping)
- `requests`, `beautifulsoup4` packages

---

### 3. `reddit_scraper.py` - Reddit Discussion Scraper ⚠️

**Status**: READY (needs API keys to test)  
**Purpose**: Scrape movie discussions from Reddit

**Input:**
```python
search_terms = ["Inception discussion", "Inception analysis"]
subreddits = ["movies", "truefilm", "moviesuggestions"]
max_results_per_term = 25
```

**Output:**
```python
[
    {
        'source': 'reddit',
        'source_id': 'reddit_abc123',
        'subreddit': 'movies',
        'title': 'Inception - What did the ending mean?',
        'text': 'Just watched Inception and...',
        'score': 1542,
        'num_comments': 234,
        'author': 'movie_fan_99',
        'created_utc': datetime(2024, 1, 15),
        'post_url': 'https://reddit.com/r/movies/...'
    },
    # ... more posts
]
```

**Usage:**
```python
from scrapers.reddit_scraper import RedditScraper

reddit = RedditScraper()
posts = reddit.search_posts(
    search_terms=["Inception discussion"],
    subreddits=["movies"],
    max_results_per_term=25
)
```

**Requirements:**
- Reddit API credentials in `.env`:
  ```
  REDDIT_CLIENT_ID=your_client_id
  REDDIT_CLIENT_SECRET=your_secret
  REDDIT_USER_AGENT=movie_scraper/1.0
  ```
- `praw` package (Python Reddit API Wrapper)

**How to Get API Keys:**
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Select "script" type
4. Copy client ID and secret to `.env`

---

### 4. `twitter_scraper.py` - Twitter/X Sentiment Scraper ⚠️

**Status**: READY (but Twitter restricts scraping)  
**Purpose**: Scrape tweets about movies

**Input:**
```python
search_terms = ["#Inception", "Inception movie"]
max_tweets_per_term = 50
```

**Output:**
```python
[
    {
        'source': 'twitter',
        'source_id': 'twitter_1234567890',
        'text': 'Just watched #Inception again. Still mind-blowing!',
        'author': '@movie_lover',
        'likes': 42,
        'retweets': 12,
        'created_at': datetime(2024, 12, 1),
        'tweet_url': 'https://twitter.com/...'
    },
    # ... more tweets
]
```

**Usage:**
```python
from scrapers.twitter_scraper import TwitterScraper

twitter = TwitterScraper()
tweets = twitter.search_tweets(
    search_terms=["#Inception"],
    max_tweets_per_term=50
)
```

**Requirements:**
- `snscrape` package (no API key needed)
- ⚠️ Twitter/X is actively restricting scraping - may not work reliably

---

### 5. `rotten_tomatoes_scraper.py` - Rotten Tomatoes Scores 📋

**Status**: PLANNED (not yet implemented)  
**Purpose**: Scrape Tomatometer and Audience scores

---

## Testing Your Scrapers

### Quick Test: Use the New Test Notebook

```bash
jupyter notebook notebooks/test_scrapers.ipynb
```

This notebook tests ONLY the scrapers:
- ✅ Gemini search term generation
- ✅ IMDb rating scraping
- ✅ IMDb review scraping
- ⚠️ Reddit (if you have API keys)
- ⚠️ Twitter (if it's working)

**No database complexity, no sentiment analysis - just pure scraper validation.**

### Manual Testing

```python
# Test Gemini
from scrapers.gemini_search import GeminiSearchTermGenerator
gemini = GeminiSearchTermGenerator()
terms = gemini.generate_search_terms("Inception", 2010, ["Sci-Fi"], "Dream heist movie")
print(terms)

# Test IMDb rating
from scrapers.imdb_scraper import IMDbScraper
imdb = IMDbScraper()
rating = imdb.scrape_movie_rating("Inception", 2010)
print(rating)

# Test IMDb reviews
reviews = imdb.scrape_movie_reviews("Inception", 2010, max_reviews=5)
print(f"Got {len(reviews)} reviews")
```

---

## Rate Limiting & Best Practices

### Rate Limits
- **IMDb**: 2 seconds between requests (default)
- **Reddit**: Managed by PRAW library
- **Twitter**: May be rate-limited by platform
- **Gemini**: API quota managed by Google

### Best Practices
1. **Always use rate limiting** - Don't hammer servers
2. **Handle errors gracefully** - Networks fail, sites change
3. **Log everything** - Use the logger utility
4. **Test incrementally** - Start with 1 movie, then scale up
5. **Respect robots.txt** - Be a good web citizen

---

## Data Flow

```
1. YOUR SCRAPERS collect raw data
      ↓
2. Return clean data structures (dicts/lists)
      ↓
3. Database team saves to database
      ↓
4. NLP team processes text (sentiment, quality)
      ↓
5. ML team uses for recommendations
```

**Your responsibility ends at step 2!**

---

## Integration Points

### For Database Team
Scrapers return data - you save it:

```python
from scrapers.imdb_scraper import IMDbScraper
from database.db import SessionLocal
from database.models import Movie, Review

imdb = IMDbScraper()

# Get reviews
reviews = imdb.scrape_movie_reviews("Inception", 2010, max_reviews=50)

# Database team saves them
db = SessionLocal()
for review_data in reviews:
    review = Review(
        movie_id=some_movie_id,
        source=review_data['source'],
        text=review_data['text'],
        rating=review_data['rating'],
        # ... etc
    )
    db.add(review)
db.commit()
```

### For NLP Team
You get the raw text from scrapers:

```python
from preprocessing.sentiment_analysis import analyze_sentiment
from preprocessing.review_weighting import calculate_review_weight

# Scrapers provide this
review_text = "This movie was absolutely amazing!"

# NLP team processes it
sentiment = analyze_sentiment(review_text, method='vader')
weight = calculate_review_weight({'text': review_text, 'helpful_count': 42})
```

---

## API Keys You Need

Add to `.env` file:

```bash
# REQUIRED for Gemini search terms
GEMINI_API_KEY=your_google_ai_key_here

# OPTIONAL for Reddit scraping
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
REDDIT_USER_AGENT=movie_scraper/1.0

# NOT NEEDED (snscrape handles Twitter)
# TWITTER_BEARER_TOKEN=
```

---

## Current Status

| Scraper | Status | API Key Needed | Works? |
|---------|--------|----------------|--------|
| Gemini Search | ✅ Complete | Yes (GEMINI_API_KEY) | ✅ Yes |
| IMDb Rating | ✅ Complete | No | ✅ Yes |
| IMDb Reviews | ✅ Complete | No | ✅ Yes |
| Reddit | ✅ Ready | Yes (REDDIT_*) | ⚠️ Untested |
| Twitter | ✅ Ready | No | ⚠️ Unreliable |
| Rotten Tomatoes | 📋 Planned | No | ❌ Not yet |

---

## Next Steps for Scraping Team

1. ✅ **Test all scrapers** using `notebooks/test_scrapers.ipynb`
2. ⚠️ **Get Reddit API keys** (optional but recommended)
3. ✅ **Validate data structures** match the formats above
4. 📋 **Document any edge cases** you find
5. 📋 **Write error handling** for network failures
6. 📋 **Add logging** for debugging

---

## Questions?

- **Scraper not working?** Check logs in `logs/app.log`
- **Rate limited?** Increase `rate_limit` parameter
- **Data structure questions?** See output formats above
- **Integration questions?** Contact database or NLP teams


## Components

### 1. `gemini_search.py` - AI-Powered Search Term Generator
- **Purpose**: Generate smart search terms using Google Gemini AI
- **Input**: 
  - Movie title (str)
  - Release year (int)
  - Genres (list of str)
  - Overview/description (str)
- **Output**: Dictionary with platform-specific search terms:
  ```python
  {
      'reddit': ['search term 1', 'search term 2', ...],
      'twitter': ['#hashtag1', '#hashtag2', ...],
      'imdb': ['imdb search 1', ...],
      'general': ['general term 1', ...]
  }
  ```
- **Usage**: Call `generate_search_terms(title, year, genres, overview)`

### 2. `imdb_scraper.py` - IMDb Scraper
- **Purpose**: Scrape movie ratings and reviews from IMDb
- **Input**:
  - Movie title (str)
  - Release year (int, optional)
  - IMDb ID (str, optional - if unknown, will search)
- **Output**:
  - **Rating**: Dictionary with `rating`, `vote_count`, `imdb_id`
  - **Reviews**: List of review dictionaries with text, rating, author, date, etc.
- **Usage**:
  - `scrape_movie_rating(title, year)` - Get just the rating
  - `scrape_movie_reviews(title, year, max_reviews)` - Get full reviews

### 3. `reddit_scraper.py` - Reddit Scraper
- **Purpose**: Scrape movie discussions from Reddit
- **Input**:
  - Search terms (list of str)
  - Subreddits to search (list of str)
  - Max results per term (int)
- **Output**: List of post/comment dictionaries with text, score, subreddit, etc.
- **Requirements**: Reddit API credentials in `.env` (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)

### 4. `twitter_scraper.py` - Twitter Scraper
- **Purpose**: Scrape movie tweets and discussions
- **Input**:
  - Search terms (list of str)
  - Max tweets per term (int)
- **Output**: List of tweet dictionaries with text, likes, retweets, date, etc.
- **Note**: Uses snscrape (no API key needed)

### 5. `rotten_tomatoes_scraper.py` - Rotten Tomatoes Scraper
- **Purpose**: Scrape critic and audience scores from Rotten Tomatoes
- **Input**:
  - Movie title (str)
  - Release year (int, optional)
- **Output**: Dictionary with `tomatometer`, `audience_score`, `critic_consensus`, etc.

## Data Flow
1. **Gemini** generates search terms → Saves to `MovieSearchTerm` table
2. **IMDb** scrapes rating → Updates `Movie.imdb_rating` field
3. **IMDb** scrapes reviews → Saves to `Review` table with `source='imdb'`
4. **Reddit/Twitter** scrape posts → Saves to `Review` table with respective sources
5. **Rotten Tomatoes** scrapes scores → Updates movie metadata

## Error Handling
- All scrapers include rate limiting (configurable delay between requests)
- Retries with exponential backoff
- Comprehensive logging to `logs/` directory
- Graceful degradation (if one source fails, others continue)

## Rate Limits
- IMDb: 2 seconds between requests (default)
- Reddit: PRAW manages rate limits automatically
- Twitter: snscrape handles throttling
- Gemini: API quota managed by Google
