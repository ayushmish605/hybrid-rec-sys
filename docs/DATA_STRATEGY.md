# Data Strategy: TMDB CSV + Live Scraping

## Overview
This system uses a **hybrid data approach** combining:
1. **TMDB CSV dataset** - Base movie metadata (2000 movies, 2016-2024)
2. **Live scraping** - Current reviews and ratings from multiple sources

## Data Sources & Priority

### 1. TMDB CSV (Base Metadata)
**Location**: `/data/tmdb_commercial_movies_2016_2024.csv`

**Contains**:
- Movie titles, release dates/years
- Genres, plot overviews
- TMDB ratings (`vote_average`, `vote_count`)
- Popularity scores
- Runtime, language
- Budget, revenue (if available)

**Use for**: 
- Initial movie database population
- Genre/metadata filtering
- Baseline ratings (if IMDb not available)

### 2. IMDb Scraping (Live, Highest Priority)
**Source**: https://www.imdb.com

**Contains**:
- **Current ratings** (more recent than TMDB CSV)
- User reviews (high quality, verified purchases)
- Critic reviews
- Vote counts

**Rating Comparison Logic**:
```python
# If IMDb rating exists AND is different from TMDB:
if imdb_rating and imdb_rating != tmdb_rating:
    # Use IMDb rating (more current)
    final_rating = imdb_rating
    rating_source = "imdb"
    rating_updated_at = now()
else:
    # Fallback to TMDB
    final_rating = tmdb_rating
    rating_source = "tmdb_csv"
```

**Why IMDb takes priority**:
- TMDB CSV is static (collected at specific point in time)
- IMDb ratings update continuously as users vote
- Example: A movie released in 2024 may have had 5.0 rating initially, but now has 7.5
- We want the **most recent** rating for better recommendations

### 3. Other Review Sources
- **Reddit**: User discussions, theories, opinions
- **Twitter**: Real-time reactions, trending sentiment
- **Rotten Tomatoes**: Critic + audience scores

## Database Schema

```sql
CREATE TABLE movies (
    id INTEGER PRIMARY KEY,
    title VARCHAR(500),
    release_year INTEGER,
    genres VARCHAR(500),  -- Pipe-separated: "Action|Sci-Fi|Thriller"
    overview TEXT,
    
    -- TMDB Data (from CSV)
    tmdb_rating FLOAT,        -- vote_average from CSV (0-10)
    tmdb_vote_count INTEGER,  -- vote_count from CSV
    popularity FLOAT,         -- TMDB popularity score
    
    -- IMDb Data (scraped live, potentially more current)
    imdb_id VARCHAR(20),      -- e.g., "tt1375666"
    imdb_rating FLOAT,        -- Live scraped (0-10)
    imdb_vote_count INTEGER,  -- Live vote count
    scraped_at DATETIME,      -- Last scrape timestamp
    
    created_at DATETIME,
    updated_at DATETIME
);
```

## Data Loading Workflow

### Step 1: Load TMDB CSV
```bash
# Place CSV in data folder
cp ~/Downloads/tmdb_commercial_movies_2016_2024.csv data/

# Load into database
python -m src.data_ingestion.tmdb_loader data/tmdb_commercial_movies_2016_2024.csv
```

**Result**: 2000 movies with base metadata, TMDB ratings

### Step 2: Scrape Live Data
```bash
# Scrape all sources (IMDb, Reddit, Twitter, RT)
python src/main.py scrape --parallel --workers 4
```

**For each movie**:
1. Generate smart search terms (Gemini AI)
2. Search IMDb for movie
3. Extract **current IMDb rating** and reviews
4. Compare with TMDB rating:
   - If IMDb rating exists → Update `imdb_rating`, set `scraped_at`
   - If significantly different → Log the difference
   - Keep TMDB rating as fallback
5. Scrape Reddit discussions using search terms
6. Scrape Twitter reactions
7. Scrape Rotten Tomatoes reviews

### Step 3: Rating Selection Logic

**In recommendation model**:
```python
def get_movie_rating(movie):
    """Get most reliable rating for movie"""
    
    # Priority 1: Recent IMDb scrape (< 7 days old)
    if movie.imdb_rating and movie.scraped_at:
        days_old = (now() - movie.scraped_at).days
        if days_old < 7:
            return movie.imdb_rating
    
    # Priority 2: TMDB rating (from CSV)
    if movie.tmdb_rating:
        return movie.tmdb_rating
    
    # Priority 3: Calculate from reviews
    if movie.reviews:
        return calculate_weighted_rating(movie.reviews)
    
    return None  # No rating available
```

## Rating Difference Handling

**Scenario 1: IMDb is higher**
```
Movie: "The Batman" (2022)
TMDB CSV (Oct 2024): 7.8/10 (500K votes)
IMDb Live (Dec 2025): 8.2/10 (650K votes)
→ Use IMDb 8.2 (more recent, more votes)
```

**Scenario 2: IMDb is lower**
```
Movie: "Controversial Film" (2023)
TMDB CSV (Oct 2024): 6.5/10 (100K votes)
IMDb Live (Dec 2025): 5.8/10 (150K votes)
→ Use IMDb 5.8 (reflects newer opinions)
```

**Scenario 3: IMDb not found**
```
Movie: "Obscure Indie" (2020)
TMDB CSV: 6.0/10 (500 votes)
IMDb Live: Not found
→ Use TMDB 6.0 (only option)
```

## Benefits of This Approach

1. **Comprehensive metadata**: TMDB CSV provides rich baseline
2. **Current ratings**: IMDb scraping ensures up-to-date scores
3. **Fallback safety**: TMDB ratings available if scraping fails
4. **Rich reviews**: Multiple sources for NLP analysis
5. **Efficient**: Load 2000 movies instantly, scrape details as needed

## Implementation Files

- `src/data_ingestion/tmdb_loader.py` - Load TMDB CSV
- `src/scrapers/imdb_scraper.py` - Scrape IMDb ratings/reviews
- `src/scrapers/orchestrator.py` - Coordinate all scrapers
- `src/database/models.py` - Database schema with dual ratings
- `src/models/recommender.py` - Rating selection logic

## Next Steps

1. Place CSV in `/data/` folder
2. Run TMDB loader to populate database
3. Configure Reddit API credentials
4. Run scraping orchestrator
5. System automatically uses most current ratings
