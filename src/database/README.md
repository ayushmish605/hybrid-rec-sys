# Database Module

## Purpose
SQLite database schema and connection management for the movie recommendation system.

## Components

### 1. `models.py` - Database Schema
Defines SQLAlchemy ORM models for all database tables.

#### Tables:

**Movie** - Core movie information
- **Inputs**: TMDB CSV data, scraped IMDb ratings
- **Fields**:
  - `id`: Primary key
  - `title`, `release_year`: Movie identification
  - `genres`, `overview`, `runtime`, `language`: Metadata
  - `tmdb_rating`, `tmdb_vote_count`: From CSV
  - `imdb_rating`, `imdb_vote_count`, `imdb_id`: From scraping
  - `popularity`, `scraped_at`: Additional info
- **Methods**:
  - `get_best_rating()`: Returns smartest rating choice (weighted by votes, recency)
  - `get_rating_metadata()`: Returns rating sources and reasoning

**Review** - User reviews from all sources
- **Inputs**: Scraped from IMDb, Reddit, Twitter, Rotten Tomatoes
- **Fields**:
  - `id`: Primary key
  - `movie_id`: Foreign key to Movie
  - `source`: 'imdb', 'reddit', 'twitter', 'rotten_tomatoes'
  - `source_id`: Unique ID from source platform (UNIQUE constraint)
  - `text`: Review content
  - `rating`: Numerical rating (if available)
  - `title`: Review title (IMDb only)
  - `sentiment_score`, `sentiment_label`: From sentiment analysis
  - `quality_score`: Review quality score (0-1)
  - `author`, `review_date`: Review metadata
  - `helpful_count`: Helpful votes (IMDb only)
  - `not_helpful_count`: Not helpful votes (IMDb only)
  - `upvotes`, `downvotes`: Social media engagement
  - `reply_count`: Number of replies
  - `review_length`: Character count
  - `word_count`: Word count
  - `scraped_at`: When review was scraped

**MovieSearchTerm** - AI-generated search terms
- **Inputs**: Gemini AI generator
- **Fields**:
  - `id`: Primary key
  - `movie_id`: Foreign key to Movie
  - `search_term`: Generated search query
  - `source`: Always 'gemini'
  - `created_at`: Timestamp

**User** - User profiles (for collaborative filtering)
- **Fields**: `id`, `username`, `created_at`

**Rating** - User ratings (for collaborative filtering)
- **Fields**: `user_id`, `movie_id`, `rating`, `timestamp`

### 2. `db.py` - Connection Management
- **Purpose**: Provide database session and initialization utilities
- **Functions**:
  - `SessionLocal()`: Create a new database session
  - `init_db()`: Initialize database schema (creates tables, directories)
- **Output**: SQLAlchemy Session objects

### 3. `__init__.py` - Package Exports
Exposes commonly used models and functions for easy imports.

## Database Location
`data/database/movie_recommender.db` (SQLite file)

## Usage Pattern

```python
from database.db import SessionLocal, init_db
from database.models import Movie, Review

# Initialize database (first time only)
init_db()

# Create session for queries
db = SessionLocal()

# Query movies
movies = db.query(Movie).limit(10).all()

# Add new review
review = Review(
    movie_id=1,
    source='imdb',
    text='Great movie!',
    rating=9.0
)
db.add(review)
db.commit()

# Close session
db.close()
```

## Rating Selection Logic
The `Movie.get_best_rating()` method intelligently chooses between TMDB and IMDb ratings:
1. **Recency**: Prefer IMDb if scraped within 7 days
2. **Vote count**: Weight by number of votes
3. **Weighted average**: Combines both sources based on vote counts
4. **Fallback**: Returns TMDB if IMDb unavailable

## Data Integrity
- Foreign key constraints enforce relationships
- Unique constraints prevent duplicate reviews
- Nullable fields allow partial data
- Timestamps track data freshness
