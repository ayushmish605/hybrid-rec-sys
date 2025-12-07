# Quick Start Guide

## Installation

1. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys:**
   - Copy `config/api_keys.example.yaml` to `config/api_keys.yaml`
   - Fill in your API keys:
     - **Gemini API**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
     - **Reddit API**: Create app at [Reddit Apps](https://www.reddit.com/prefs/apps)
     - **Twitter API** (optional): Get from [Twitter Developer Portal](https://developer.twitter.com/)

4. **Copy your movie dataset:**
   ```bash
   # Place your tmdb_commercial_movies_2016_2024.csv in the data/raw/ directory
   mkdir -p data/raw
   cp /path/to/tmdb_commercial_movies_2016_2024.csv data/raw/
   ```

## Usage

### 1. Initialize Database

```bash
python src/main.py init-db
```

When prompted, enter the path to your CSV file:
```
/full/path/to/data/raw/tmdb_commercial_movies_2016_2024.csv
```

### 2. Scrape Movie Reviews

Scrape reviews for all movies (or a limited number):

```bash
# Scrape 10 movies (for testing)
python src/main.py scrape --limit 10

# Scrape all movies (may take hours!)
python src/main.py scrape

# Use parallel scraping for speed
python src/main.py scrape --parallel --workers 4
```

### 3. Train Recommendation Models

```bash
python src/main.py train
```

### 4. Get Recommendations

```bash
python src/main.py recommend "Inception" --top-k 10
```

## Project Workflow

```
1. init-db    → Load movies from CSV into database
2. scrape     → Scrape reviews from IMDb, Reddit, Twitter, RT
3. train      → Train CBF, CF, and hybrid models
4. recommend  → Get personalized recommendations
```

## Configuration

Edit `config/config.yaml` to customize:
- Number of reviews per source
- Rate limits
- Model parameters
- Weighting factors

## Troubleshooting

**ImportError: No module named 'X'**
- Run: `pip install -r requirements.txt`

**API rate limiting errors:**
- Increase `rate_limits` in `config/config.yaml`
- Use `--limit` to test with fewer movies first

**Database locked errors:**
- Close other connections to the database
- Use PostgreSQL for concurrent access (edit config)

**Out of memory errors:**
- Reduce batch sizes in config
- Process movies in smaller batches
- Use `--limit` parameter

## Next Steps

1. Implement evaluation metrics (RMSE, Precision@k, etc.)
2. Fine-tune model hyperparameters
3. Add more NLP features (topic modeling, entity extraction)
4. Implement the meta-learning hybrid approach
5. Build a web interface for the recommendation system

## Questions?

Check the full README.md for detailed documentation.
