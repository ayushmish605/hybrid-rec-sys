# Quick Start: Sentiment Analysis & RT Scores

## ✅ What Was Done

### 1. Database Schema (Already Updated)
- ✅ Added 7 new columns to `movies` table
- ✅ Added 1 new column to `reviews` table  
- ✅ Added `review_category` field to track RT review types

### 2. RT Scraper (Already Enhanced)
- ✅ Added `get_tomatometer_score()` method
- ✅ Scrapes official RT percentage from page

### 3. Notebook (3 New Cells Added)
- ✅ **Cell 32**: Scrape RT Tomatometer scores
- ✅ **Cell 35**: Run VADER sentiment analysis
- ✅ **Cell 37**: Calculate average sentiment per movie

## 🚀 How to Use

### Step 1: Re-initialize Database (IMPORTANT!)

Because we added new columns, you need to recreate the database:

```bash
cd /Users/rachitasaini/Desktop/Rutgers/Fall\ 2026/Intro\ to\ Data\ Science\ 01-198-439/project/hybrid-rec-sys

# Option 1: Delete and recreate
rm data/database/movie_recommender.db
python src/database/init_db.py

# Option 2: Add columns manually (SQLite)
sqlite3 data/database/movie_recommender.db < add_columns.sql
```

Where `add_columns.sql` contains:
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

### Step 2: Run Notebook Cells in Order

Open `notebooks/01_quick_test.ipynb`:

1. **Run Cells 1-30**: Load data, scrape IMDb (as before)

2. **NEW - Cell 32**: Scrape RT Tomatometer Scores
   - Scrapes official RT percentage for each movie
   - Stores in `rt_tomatometer` (0-100)
   - Stores in `rt_tomatometer_out_of_10` (0-10)

3. **Cell 33**: Scrape RT Reviews (as before)
   - Now properly stores `review_category` field

4. **NEW - Cell 35**: VADER Sentiment Analysis
   - Auto-installs `vaderSentiment` if needed
   - Analyzes all reviews
   - Updates `sentiment_score`, `sentiment_label`, `sentiment_confidence`

5. **NEW - Cell 37**: Calculate Average Sentiment
   - Groups by movie and category
   - Updates 5 sentiment average columns in `movies` table

### Step 3: Verify Results

```python
# Check a single movie
from database.db import get_session
from database.models import Movie

db = get_session()
movie = db.query(Movie).first()

print(f"Title: {movie.title}")
print(f"RT Score: {movie.rt_tomatometer}%")
print(f"RT Score /10: {movie.rt_tomatometer_out_of_10}")
print(f"IMDb Sentiment: {movie.sentiment_imdb_avg}")
print(f"RT Top Critics Sentiment: {movie.sentiment_rt_top_critics_avg}")
print(f"RT All Critics Sentiment: {movie.sentiment_rt_all_critics_avg}")
print(f"RT Verified Audience Sentiment: {movie.sentiment_rt_verified_audience_avg}")
print(f"RT All Audience Sentiment: {movie.sentiment_rt_all_audience_avg}")
```

## 📊 Expected Output

### Cell 32 (RT Scores)
```
🍅 SCRAPING ROTTEN TOMATOES TOMATOMETER SCORES
📽️  [1/10] Getting RT score: The Batman (2022)
   ✅ RT Score: 85% (out of 10: 8.5)
...
✅ Scores found: 9/10
```

### Cell 35 (Sentiment Analysis)
```
🎭 VADER SENTIMENT ANALYSIS
📊 Found 350 reviews to analyze
   Progress: 100/350
   Progress: 200/350
   Progress: 300/350
✅ Sentiment analysis complete!
   Analyzed: 350 reviews

📊 Sentiment Distribution:
   Positive: 180
   Negative: 120
   Neutral: 50
```

### Cell 37 (Averages)
```
📊 CALCULATING AVERAGE SENTIMENT PER MOVIE

The Batman (2022):
   IMDb avg sentiment: 0.4523 (n=50)
   RT Top Critics avg sentiment: 0.6234 (n=20)
   RT All Critics avg sentiment: 0.5891 (n=40)
   RT Verified Audience avg sentiment: 0.3456 (n=15)
   RT All Audience avg sentiment: 0.2987 (n=25)

✅ Sentiment averages calculated for 10 movies

📈 SENTIMENT SUMMARY ACROSS ALL MOVIES
IMDb Average Sentiment: 0.3245
RT Top Critics Average Sentiment: 0.4567
RT All Critics Average Sentiment: 0.4123
RT Verified Audience Average Sentiment: 0.2890
RT All Audience Average Sentiment: 0.2654
✅ ALL SENTIMENT PROCESSING COMPLETE!
```

## 🎯 New Columns Summary

### Movies Table (7 new columns)
1. `rt_tomatometer` - RT critics score (0-100)
2. `rt_tomatometer_out_of_10` - RT score converted to 10-point scale
3. `sentiment_imdb_avg` - Average IMDb review sentiment (-1 to 1)
4. `sentiment_rt_top_critics_avg` - Average RT top critics sentiment (-1 to 1)
5. `sentiment_rt_all_critics_avg` - Average RT all critics sentiment (-1 to 1)
6. `sentiment_rt_verified_audience_avg` - Average RT verified audience sentiment (-1 to 1)
7. `sentiment_rt_all_audience_avg` - Average RT all audience sentiment (-1 to 1)

### Reviews Table (1 new column)
1. `review_category` - For RT: 'top_critic', 'critic', 'verified_audience', 'audience'

## ⚠️ Important Notes

### Disk Space
- **Fixed**: File logging is now disabled to avoid disk space errors
- Make sure you have free disk space before running

### RT Category Mapping
- `'top_critic'` → RT Top Critics
- `'critic'` → RT All Critics (non-top)
- `'verified_audience'` → RT Verified Audience
- `'audience'` → RT All Audience (non-verified)

### Sentiment Scores
- Range: **-1.0 to +1.0**
- Precision: **6 decimal places**
- Positive: >= 0.05
- Negative: <= -0.05
- Neutral: between -0.05 and 0.05

## 🔧 Troubleshooting

### "Column doesn't exist" error
➡️ **Solution**: Recreate database (Step 1 above)

### RT scores all None
➡️ **Solution**: Run Cell 32 (RT score scraping)

### Sentiment scores all None on reviews
➡️ **Solution**: Run Cell 35 (VADER analysis)

### Sentiment averages None on movies
➡️ **Solution**: Run Cell 37 (calculate averages)

### "No module named vaderSentiment"
➡️ **Solution**: Cell 35 auto-installs it, or run:
```bash
pip install vaderSentiment
```

## 📚 Documentation

- Full details: `docs/SENTIMENT_ANALYSIS_INTEGRATION.md`
- RT scraper: `src/scrapers/rotten_tomatoes_selenium.py`
- Database models: `src/database/models.py`

## ✨ What's Working

1. ✅ RT score scraping with Beautiful Soup parsing
2. ✅ VADER sentiment analysis on all reviews
3. ✅ Proper categorization of RT reviews by source
4. ✅ Average sentiment calculation by source
5. ✅ 6 decimal place precision on all scores
6. ✅ Automatic VADER installation
7. ✅ Comprehensive error handling
