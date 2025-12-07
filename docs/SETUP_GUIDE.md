# Quick Setup Guide

## 📁 Step 1: Place Your TMDB CSV

Move your dataset to the data folder:

```bash
cp ~/Downloads/tmdb_commercial_movies_2016_2024.csv /Users/rachitasaini/Desktop/Rutgers/Fall\ 2026/Intro\ to\ Data\ Science\ 01-198-439/project/hybrid-rec-sys/data/
```

Or just drag and drop the file into:
```
hybrid-rec-sys/data/tmdb_commercial_movies_2016_2024.csv
```

## 📦 Step 2: Install Dependencies

```bash
cd /Users/rachitasaini/Desktop/Rutgers/Fall\ 2026/Intro\ to\ Data\ Science\ 01-198-439/project/hybrid-rec-sys
source venv/bin/activate
pip install -r requirements.txt
```

## 🗄️ Step 3: Load TMDB Data into Database

```bash
# Initialize database and load CSV
python -m src.data_ingestion.tmdb_loader data/tmdb_commercial_movies_2016_2024.csv
```

This will:
- ✅ Create SQLite database (`data/movies.db`)
- ✅ Parse CSV and extract: titles, years, genres, ratings, etc.
- ✅ Populate `movies` table with 2000 movies
- ✅ Set `tmdb_rating` and `tmdb_vote_count` from CSV

Expected output:
```
Loaded 2000 movies from CSV
Progress: 100/2000 movies processed
Progress: 500/2000 movies processed
...
Progress: 2000/2000 movies processed
✅ TMDB Data Load Complete: {loaded: 2000, skipped: 0, errors: 0}
```

## 🔑 Step 4: Configure API Credentials

### Reddit API (Required for Reddit scraping)

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in:
   - **Name**: `MovieScraperBot`
   - **Type**: Select "script"
   - **Description**: `Movie review scraper for academic project`
   - **About URL**: (leave blank)
   - **Redirect URI**: `http://localhost:8080`
4. Click "Create app"
5. Copy the credentials and add to `.env`:

```bash
# .env file already has Gemini key, add these:
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=MovieScraperBot/1.0 by YourRedditUsername
```

### API Keys Summary

| Service | Required? | Purpose | Setup |
|---------|-----------|---------|-------|
| **Gemini** | ✅ Done | Generate smart search terms | Already configured |
| **Reddit** | ⚠️ Needed | Scrape Reddit discussions | Follow Step 4 above |
| **Twitter** | ❌ Optional | Uses snscrape (no key needed) | None |
| **IMDb** | ❌ None | Web scraping (public) | None |
| **Rotten Tomatoes** | ❌ None | Web scraping (public) | None |

## 🧪 Step 5: Test Scraping (10 movies)

```bash
# Test on small sample first
python src/main.py scrape --limit 10 --parallel --workers 2
```

Expected output:
```
Scraping 10 movies in parallel (2 workers)
✅ The Batman (2022): 245 reviews (IMDb: 8.2/10 vs TMDB: 7.8/10)
✅ Dune (2021): 189 reviews (IMDb: 8.0/10 vs TMDB: 7.9/10)
...
Scraping complete! 10 movies, 1,834 total reviews
```

**Rating Comparison**: System will automatically log when IMDb ratings differ from TMDB CSV:
- `IMDb: 8.2` = Live scraped (Dec 2025)
- `TMDB: 7.8` = From CSV (older snapshot)
- System uses **IMDb 8.2** (more current)

## 🚀 Step 6: Full Scraping Run (2000 movies)

```bash
# Full scrape with 4 parallel workers
python src/main.py scrape --parallel --workers 4
```

**Estimated time**: ~6-8 hours for 2000 movies
- IMDb: ~3 sec/movie
- Reddit: ~2 sec/movie
- Twitter: ~1 sec/movie
- Rotten Tomatoes: ~2 sec/movie
- Rate limiting: ~8 sec/movie average

**Progress saving**: Reviews saved to database continuously, so you can stop/resume anytime

## 📊 Step 7: Verify Data

```bash
# Check database statistics
python -c "
from src.database.db import SessionLocal
from src.database.models import Movie, Review

db = SessionLocal()

movies = db.query(Movie).count()
with_imdb = db.query(Movie).filter(Movie.imdb_rating.isnot(None)).count()
reviews = db.query(Review).count()

print(f'Movies: {movies}')
print(f'With IMDb ratings: {with_imdb}')
print(f'Total reviews: {reviews}')

# Rating comparison
different_ratings = db.query(Movie).filter(
    Movie.imdb_rating.isnot(None),
    Movie.tmdb_rating.isnot(None),
    Movie.imdb_rating != Movie.tmdb_rating
).count()

print(f'Movies with different IMDb vs TMDB ratings: {different_ratings}')
"
```

## 🎯 Usage in Recommendations

The recommendation system automatically uses the most current rating:

```python
from src.models.recommender import HybridRecommender

recommender = HybridRecommender()

# System automatically:
# 1. Prefers IMDb rating if < 7 days old
# 2. Falls back to TMDB rating if IMDb unavailable
# 3. Uses review-based rating if both missing

recommendations = recommender.recommend(user_id=1, n=10)
```

## 📁 File Structure After Setup

```
hybrid-rec-sys/
├── data/
│   ├── tmdb_commercial_movies_2016_2024.csv  ← Your CSV here
│   └── movies.db                              ← Created after Step 3
├── .env                                       ← API keys
├── venv/                                      ← Virtual environment
└── src/
    ├── data_ingestion/
    │   └── tmdb_loader.py                     ← CSV loader
    ├── scrapers/
    │   ├── orchestrator.py                    ← Main scraper
    │   ├── imdb_scraper.py                    ← IMDb scraper
    │   └── ...
    └── database/
        └── models.py                          ← Dual rating schema
```

## 🔍 Troubleshooting

### CSV file not found
```bash
# Check if file exists
ls -la data/tmdb_commercial_movies_2016_2024.csv
```

### Database permission error
```bash
# Ensure data directory is writable
chmod -R 755 data/
```

### Missing dependencies
```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

### Reddit API errors
- Double-check credentials in `.env`
- Ensure no extra spaces in API keys
- Verify Reddit app is "script" type (not "web app")

## ✅ Success Checklist

- [ ] CSV placed in `data/` folder
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database initialized (2000 movies loaded)
- [ ] Gemini API tested (✅ already done)
- [ ] Reddit API configured (add to `.env`)
- [ ] Test scraping works (10 movies)
- [ ] Full scraping completed
- [ ] Ratings comparison verified

## 📚 Next Steps After Setup

1. **Exploratory Data Analysis**: Check `notebooks/01_data_exploration.ipynb`
2. **Train Models**: Run collaborative filtering and content-based models
3. **Evaluate**: Test recommendation quality with metrics
4. **Visualize**: Generate rating distribution charts, sentiment analysis graphs
