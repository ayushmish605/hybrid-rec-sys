# Sentiment Analysis Integration

## Overview

This document describes the complete integration of VADER sentiment analysis and Rotten Tomatoes Tomatometer scoring into the hybrid recommendation system.

## Changes Made

### 1. Database Schema Updates (`src/database/models.py`)

#### Movie Table - New Columns:
```python
# Rotten Tomatoes ratings
rt_tomatometer = Column(Float, nullable=True)  # RT critics score (0-100)
rt_tomatometer_out_of_10 = Column(Float, nullable=True)  # Converted to 0-10 scale

# Sentiment analysis averages (computed from reviews)
sentiment_imdb_avg = Column(Float, nullable=True)  # Average sentiment from IMDb reviews (-1 to 1)
sentiment_rt_top_critics_avg = Column(Float, nullable=True)  # RT top critics sentiment
sentiment_rt_all_critics_avg = Column(Float, nullable=True)  # RT all critics sentiment
sentiment_rt_verified_audience_avg = Column(Float, nullable=True)  # RT verified audience sentiment
sentiment_rt_all_audience_avg = Column(Float, nullable=True)  # RT all audience sentiment
```

**Total new columns**: 7

#### Review Table - New Column:
```python
review_category = Column(String(50), nullable=True)  # For RT: 'top_critic', 'critic', 'verified_audience', 'audience'
```

This allows proper categorization of RT reviews by their source endpoint.

### 2. Rotten Tomatoes Scraper Enhancement (`src/scrapers/rotten_tomatoes_selenium.py`)

#### New Method: `get_tomatometer_score()`
```python
def get_tomatometer_score(self, movie_slug: str) -> Optional[float]:
    """
    Get the Tomatometer (critics) score for a movie.
    
    Scrapes from: <rt-text slot="criticsScore" ...>46%</rt-text>
    
    Returns:
        Score as percentage (0-100), or None if not found
    """
```

**Implementation Details:**
- Uses CSS selector: `rt-text[slot="criticsScore"]`
- Extracts percentage value and converts to float
- 10-second timeout for page load
- Handles missing scores gracefully

### 3. Notebook Updates (`notebooks/01_quick_test.ipynb`)

#### New Cell: Step 11a - Scrape RT Tomatometer Scores
**Location**: Before RT review scraping (Cell #32)

**Purpose**: Scrape the official Rotten Tomatoes Tomatometer score for each movie

**Functionality:**
- Searches for movie using existing search logic
- Gets Tomatometer percentage (0-100)
- Converts to 0-10 scale for consistency
- Updates `Movie` table with both values
- Shows success rate summary

**Output Example:**
```
📽️  [1/10] Getting RT score: The Batman (2022)
   ✅ RT Score: 85% (out of 10: 8.5)
```

#### New Cell: Step 12 - VADER Sentiment Analysis
**Location**: After RT review scraping (Cell #35)

**Purpose**: Apply VADER sentiment analysis to all reviews

**Functionality:**
- Auto-installs `vaderSentiment` if needed
- Analyzes all reviews without sentiment scores
- Calculates compound score (-1 to +1)
- Assigns sentiment label (positive/negative/neutral)
- Stores confidence score
- Updates `Review` table with 6 decimal places precision
- Shows distribution of sentiment labels

**VADER Scoring:**
- **Compound >= 0.05**: Positive
- **Compound <= -0.05**: Negative
- **Between -0.05 and 0.05**: Neutral

**Output Example:**
```
📊 Found 350 reviews to analyze
✅ Sentiment analysis complete!
   Analyzed: 350 reviews

📊 Sentiment Distribution:
   Positive: 180
   Negative: 120
   Neutral: 50
```

#### New Cell: Step 13 - Calculate Average Sentiment Per Movie
**Location**: After sentiment analysis (Cell #37)

**Purpose**: Calculate average sentiment for each movie by source

**Functionality:**
- Queries reviews grouped by `movie_id` and `review_category`
- Calculates separate averages for:
  - IMDb reviews
  - RT Top Critics (`review_category = 'top_critic'`)
  - RT All Critics (`review_category = 'critic'`)
  - RT Verified Audience (`review_category = 'verified_audience'`)
  - RT All Audience (`review_category = 'audience'`)
- Updates `Movie` table with 6 decimal places
- Shows overall averages across all movies

**Output Example:**
```
The Batman (2022):
   IMDb avg sentiment: 0.4523 (n=50)
   RT Top Critics avg sentiment: 0.6234 (n=20)
   RT All Critics avg sentiment: 0.5891 (n=40)
   RT Verified Audience avg sentiment: 0.3456 (n=15)
   RT All Audience avg sentiment: 0.2987 (n=25)

📈 SENTIMENT SUMMARY ACROSS ALL MOVIES
IMDb Average Sentiment: 0.3245
RT Top Critics Average Sentiment: 0.4567
RT All Critics Average Sentiment: 0.4123
RT Verified Audience Average Sentiment: 0.2890
RT All Audience Average Sentiment: 0.2654
```

### 4. RT Review Scraping Update

The existing RT scraping cell now properly stores `review_category`:

```python
review = Review(
    movie_id=movie_obj.id,
    source='rotten_tomatoes',
    source_id=source_id,
    review_category=priority,  # 'top_critic', 'critic', 'verified_audience', 'audience'
    # ... rest of fields
)
```

This ensures sentiment can be averaged correctly by category.

## Data Flow

1. **Scrape RT Scores** (Step 11a)
   - Get Tomatometer percentage
   - Store in `Movie.rt_tomatometer` (0-100)
   - Store converted in `Movie.rt_tomatometer_out_of_10` (0-10)

2. **Scrape Reviews** (Step 11b)
   - IMDb reviews → `Review.source = 'imdb'`
   - RT reviews → `Review.source = 'rotten_tomatoes'`
     - Each review tagged with `review_category`

3. **Analyze Sentiment** (Step 12)
   - Run VADER on all reviews
   - Store `sentiment_score` (-1 to 1, 6 decimals)
   - Store `sentiment_label` (positive/negative/neutral)
   - Store `sentiment_confidence`

4. **Calculate Averages** (Step 13)
   - Group by movie and category
   - Update 5 columns in `Movie` table:
     - `sentiment_imdb_avg`
     - `sentiment_rt_top_critics_avg`
     - `sentiment_rt_all_critics_avg`
     - `sentiment_rt_verified_audience_avg`
     - `sentiment_rt_all_audience_avg`

## Database Columns Summary

### Movies Table - 7 New Columns

| Column Name | Type | Range | Description |
|------------|------|-------|-------------|
| `rt_tomatometer` | Float | 0-100 | Official RT critics score (percentage) |
| `rt_tomatometer_out_of_10` | Float | 0-10 | RT score converted to 10-point scale |
| `sentiment_imdb_avg` | Float | -1 to 1 | Average sentiment of IMDb reviews |
| `sentiment_rt_top_critics_avg` | Float | -1 to 1 | Average sentiment of RT top critics |
| `sentiment_rt_all_critics_avg` | Float | -1 to 1 | Average sentiment of RT all critics |
| `sentiment_rt_verified_audience_avg` | Float | -1 to 1 | Average sentiment of RT verified audience |
| `sentiment_rt_all_audience_avg` | Float | -1 to 1 | Average sentiment of RT all audience |

### Reviews Table - 1 New Column

| Column Name | Type | Values | Description |
|------------|------|--------|-------------|
| `review_category` | String | 'top_critic', 'critic', 'verified_audience', 'audience' | RT review source category |

**Note**: `sentiment_score`, `sentiment_label`, and `sentiment_confidence` already existed in the Review model.

## Usage

### Running the Pipeline

1. **Initialize database** (if new columns don't exist):
   ```bash
   python src/database/init_db.py
   ```

2. **Run notebook cells in order**:
   - Step 11a: Scrape RT scores
   - Step 11b: Scrape RT reviews (already done)
   - Step 12: Analyze sentiment
   - Step 13: Calculate averages

### Querying Sentiment Data

```python
from database.db import get_session
from database.models import Movie, Review

db = get_session()

# Get movie with all sentiment data
movie = db.query(Movie).filter(Movie.title == "The Batman").first()

print(f"RT Score: {movie.rt_tomatometer}%")
print(f"RT Score (out of 10): {movie.rt_tomatometer_out_of_10}")
print(f"IMDb Sentiment: {movie.sentiment_imdb_avg}")
print(f"RT Critics Sentiment: {movie.sentiment_rt_all_critics_avg}")

# Get individual review sentiments
reviews = db.query(Review).filter(
    Review.movie_id == movie.id,
    Review.source == 'rotten_tomatoes',
    Review.review_category == 'top_critic'
).all()

for review in reviews:
    print(f"{review.sentiment_label}: {review.sentiment_score:.4f} - {review.text[:100]}")
```

## Dependencies

### New Dependency
- `vaderSentiment`: For sentiment analysis (auto-installed in notebook)

### Installation
```bash
pip install vaderSentiment
```

Or add to `requirements.txt`:
```
vaderSentiment==3.3.2
```

## Notes

### Sentiment Score Precision
- All sentiment scores stored with **6 decimal places** for high precision
- Example: `0.456789` instead of `0.46`

### RT Category Mapping
- The scraper returns `review_type` which maps to `review_category`:
  - `'top_critic'` → Top Critics reviews
  - `'critic'` → All Critics reviews (non-top)
  - `'verified_audience'` → Verified Audience reviews
  - `'audience'` → All Audience reviews (non-verified)

### Handling Missing Data
- If RT score not found: columns remain `None`
- If no reviews for a category: sentiment average remains `None`
- Sentiment analysis skips reviews with no text

### Performance
- Sentiment analysis: ~100-200 reviews/second
- RT score scraping: ~1 movie every 10-15 seconds (includes WebDriver overhead)

## Future Enhancements

1. **Weighted Sentiment**: Use review quality scores to weight sentiment averages
2. **Temporal Analysis**: Track sentiment changes over time
3. **Aspect-Based Sentiment**: Analyze sentiment by specific aspects (acting, plot, visuals)
4. **Emoji Support**: VADER handles emojis but could be enhanced for movie reviews
5. **Multi-language**: Extend sentiment analysis to non-English reviews

## Troubleshooting

### Issue: Sentiment scores are None
**Solution**: Run Step 12 (sentiment analysis cell) first

### Issue: RT scores not scraped
**Solution**: 
- Check disk space (previous issue)
- Verify WebDriver is working
- Check RT website structure hasn't changed

### Issue: Averages not calculating
**Solution**: 
- Ensure `review_category` is set correctly
- Check that sentiment_score exists on reviews
- Verify movie has reviews in database

### Issue: Database errors on new columns
**Solution**: Drop and recreate database or add columns manually:
```sql
ALTER TABLE movies ADD COLUMN rt_tomatometer REAL;
ALTER TABLE movies ADD COLUMN rt_tomatometer_out_of_10 REAL;
ALTER TABLE movies ADD COLUMN sentiment_imdb_avg REAL;
ALTER TABLE movies ADD COLUMN sentiment_rt_top_critics_avg REAL;
ALTER TABLE movies ADD COLUMN sentiment_rt_all_critics_avg REAL;
ALTER TABLE movies ADD COLUMN sentiment_rt_verified_audience_avg REAL;
ALTER TABLE movies ADD COLUMN sentiment_rt_all_audience_avg REAL;
ALTER TABLE reviews ADD COLUMN review_category TEXT;
```

## Contact

For questions or issues, refer to:
- VADER documentation: https://github.com/cjhutto/vaderSentiment
- RT scraper docs: `src/scrapers/README.md`
- Database schema: `src/database/models.py`
