# Data Directory

## Purpose
Storage for all data files used by the hybrid recommendation system.

## Directory Structure

```
data/
├── tmdb_commercial_movies_2016_2024.csv    # Input: TMDB movie dataset
├── database/                                # Output: SQLite database
│   └── movie_recommender.db                # Main database file
└── README.md                               # This file
```

## Files

### Input Data

#### `tmdb_commercial_movies_2016_2024.csv` (Required)
- **Purpose**: Source movie dataset from TMDB
- **Size**: ~2000 movies (2016-2024)
- **Format**: CSV with columns:
  - `title`: Movie title
  - `release_date`: YYYY-MM-DD format
  - `vote_average`: TMDB rating (0-10)
  - `vote_count`: Number of TMDB votes
  - `genres`: Genre names or IDs
  - `overview`: Movie description
  - `popularity`: Popularity score
  - `runtime`: Duration in minutes
  - `original_language`: Language code
- **Where to get**: Download from your TMDB source
- **How to add**: 
  ```bash
  cp ~/Downloads/tmdb_commercial_movies_2016_2024.csv data/
  ```

### Output Data

#### `database/movie_recommender.db` (Auto-generated)
- **Purpose**: SQLite database storing all processed data
- **Created by**: Running notebooks or calling `init_db()`
- **Size**: Grows as you scrape more data
- **Tables**:
  - `movies`: Core movie information (from CSV + scraped data)
  - `reviews`: User reviews from all sources
  - `movie_search_terms`: AI-generated search terms
  - `users`: User profiles (for collaborative filtering)
  - `ratings`: User-movie ratings (for collaborative filtering)
- **Backup**: Copy this file to backup all your work
  ```bash
  cp data/database/movie_recommender.db data/database/backup_$(date +%Y%m%d).db
  ```

## Data Flow

```
1. Input CSV → Load into database (TMDB ratings)
     ↓
2. Generate search terms with Gemini AI
     ↓
3. Scrape IMDb ratings (overwrites/augments TMDB ratings)
     ↓
4. Scrape reviews from IMDb, Reddit, Twitter
     ↓
5. Process reviews (sentiment analysis, quality scoring)
     ↓
6. Train recommendation models on processed data
```

## Data Management

### Adding More Movies
1. Get new TMDB CSV with additional movies
2. Run notebook cells that load CSV
3. System automatically skips duplicates (by title + year)

### Resetting Database
```bash
# WARNING: This deletes all scraped data!
rm data/database/movie_recommender.db
```

### Exporting Data
```python
from database.db import SessionLocal
from database.models import Movie
import pandas as pd

db = SessionLocal()
movies = db.query(Movie).all()

df = pd.DataFrame([{
    'title': m.title,
    'year': m.release_year,
    'tmdb_rating': m.tmdb_rating,
    'imdb_rating': m.imdb_rating,
    'genres': m.genres
} for m in movies])

df.to_csv('data/exported_movies.csv', index=False)
```

## Storage Estimates

| Data Type | Count | Size |
|-----------|-------|------|
| CSV (2000 movies) | 2000 rows | ~5 MB |
| Database (movies only) | 2000 records | ~2 MB |
| + IMDb ratings | +2000 ratings | ~3 MB |
| + Search terms | +20,000 terms | ~5 MB |
| + Reviews (50/movie) | +100,000 reviews | ~200 MB |
| **Total (full scrape)** | | **~215 MB** |

## Backup Strategy

**Recommended:**
1. Backup database after major scraping runs
2. Keep CSV file safe (it's your source of truth for metadata)
3. Git ignore large data files (already configured in `.gitignore`)

**Automated backup:**
```bash
# Add to crontab for daily backup
0 2 * * * cp /path/to/data/database/movie_recommender.db /path/to/backups/db_$(date +\%Y\%m\%d).db
```
