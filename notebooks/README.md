# Notebooks Directory

## 🎯 Purpose
**The notebooks are the PRIMARY DRIVER for the entire system.** All scraping, data processing, and testing should be run through notebooks, not standalone scripts.

## 📓 Available Notebooks

### 1. `01_quick_test.ipynb` - Quick Setup Test + Basic Scraping (5 minutes)
**Purpose:** Verify setup works and test basic scraping functionality  

**What it does:**
- Part 1: CSV Loading & Database Operations
  - ✅ Loads 10 movies from TMDB CSV
  - ✅ Shows movie metadata (title, genres, ratings)
  - ✅ Demonstrates smart rating selection
  - ✅ Creates visualizations
  
- Part 2: Scraping Pipeline Test
  - ✅ Tests Gemini AI search term generation (3 movies)
  - ✅ Tests IMDb rating scraping (3 movies)
  - ✅ Compares TMDB vs IMDb ratings with visualization

**When to use:** First time setup, quick testing, verify scraping works

**Run this if:** You want to verify the system can load data AND scrape live ratings

**Runtime:** ~5 minutes

---

### 2. `02_full_pipeline_demo.ipynb` - Complete System Test (10-240 minutes)
**Purpose:** **Comprehensive end-to-end testing of entire hybrid recommendation system**  

**What it tests:**

#### 🗄️ Data Layer
- TMDB CSV loading and parsing
- Database schema validation
- Dual rating system (TMDB + IMDb)
- Data integrity checks

#### 🤖 AI & NLP Pipeline
- Gemini AI search term generation
- Sentiment analysis with transformers
- Review quality scoring
- Text preprocessing and cleaning

#### 🌐 Multi-Source Scraping
- IMDb: Ratings, reviews, vote counts
- Reddit: User discussions (optional)
- Twitter: Social media sentiment (optional)
- Rate limiting and error handling

#### 🧠 Intelligence Layer
- TMDB vs IMDb rating comparison
- Weighted average calculation
- Freshness-aware rating selection
- Quality-based review filtering

#### 📊 Analytics & Validation
- System health checks
- Performance benchmarking
- Data visualizations
- Comprehensive summary reports

**When to use:** Full system testing, production scraping, performance validation

**Run this if:** You want to test the complete system or scrape the full dataset

**Configuration:**
```python
SCRAPE_LIMIT = 10      # Set to 2000 for full dataset
USE_PARALLEL = False   # Set to True for faster scraping
```

---

## 🚀 Quick Start

### Option 1: Quick Test (Recommended First)
```bash
# 1. Copy your CSV
cp ~/Downloads/tmdb_commercial_movies_2016_2024.csv ../data/

# 2. Open Jupyter
jupyter notebook 01_quick_test.ipynb

# 3. Run all cells (Cell → Run All)
```

### Option 2: Full Pipeline
```bash
# 1. Copy your CSV
cp ~/Downloads/tmdb_commercial_movies_2016_2024.csv ../data/

# 2. Make sure dependencies are installed
pip install -r ../requirements.txt

# 3. Open Jupyter
jupyter notebook 02_full_pipeline_demo.ipynb

# 4. Run all cells or step through
```

---

## 📋 Notebook as Source of Truth

**Important:** The notebooks contain the **actual working code** for the system. The `src/` modules provide supporting functions, but:
- ✅ All scraping workflows are run from notebooks
- ✅ All data processing is executed in notebooks
- ✅ All testing and validation happens in notebooks
- ❌ No standalone `main.py` or orchestrator scripts
- ❌ No command-line drivers (removed)

**Why notebooks?**
- Interactive development and debugging
- Visual feedback at each step
- Easy to modify and experiment
- Clear documentation inline
- Step-by-step execution control

---

## 📊 What You'll See

### From `01_quick_test.ipynb`:
- Movie list with ratings
- Rating distribution chart
- Top movies bar chart
- Vote count vs rating scatter plot
- Genre breakdown

### From `02_full_pipeline_demo.ipynb`:
- All of the above PLUS:
- Gemini-generated search terms
- IMDb review samples
- Sentiment analysis results (positive/negative/neutral)
- Quality score rankings
- TMDB vs IMDb comparison chart
- Complete database statistics

---

## 🎯 Workflow Recommendation

**First time?**
1. Run `01_quick_test.ipynb` to verify setup (2 min)
2. If successful, run `02_full_pipeline_demo.ipynb` (10-15 min)
3. Adjust `SCRAPE_LIMIT` in notebook for more movies

**Production scraping?**
1. Use `02_full_pipeline_demo.ipynb`
2. Set `SCRAPE_LIMIT = 2000` (or desired number)
3. Set `USE_PARALLEL = True` for faster processing
4. Let it run (6-8 hours for 2000 movies)

---

## 🔧 Configuration

### In `01_quick_test.ipynb`:
- `DEMO_LIMIT = 10` - Number of movies to load

### In `02_full_pipeline_demo.ipynb`:
- `DEMO_LIMIT = 10` - Movies to load from CSV
- `SCRAPE_LIMIT = 5` - Movies to scrape
- `USE_PARALLEL = False` - Enable parallel scraping

---

## 📁 Output Files

After running notebooks, you'll have:
- `../data/movies.db` - SQLite database with movies & reviews
- `../data/demo_results.csv` - Exported results
- Inline visualizations in notebooks

---

## ❓ Troubleshooting

### "CSV not found"
```bash
cp ~/Downloads/tmdb_commercial_movies_2016_2024.csv ../data/
```

### "Module not found"
```bash
pip install -r ../requirements.txt
```

### "Gemini API error"
Check `.env` file has your API key:
```
GEMINI_API_KEY=your_api_key_here
```

### "IMDb blocking requests"
- Increase `rate_limit` parameter
- Add delays between requests
- Use VPN if needed

---

## 🎓 Learning Path

1. **Week 1:** Run `01_quick_test.ipynb` to understand data structure
2. **Week 2:** Run `02_full_pipeline_demo.ipynb` with 10 movies
3. **Week 3:** Scale up to 100 movies, analyze results
4. **Week 4:** Full 2000 movie scraping
5. **Week 5:** Train recommendation models on collected data

---

## 📚 Next Steps

After running demos:
- Explore `03_data_exploration.ipynb` (if exists) for deeper analysis
- Train models in `04_model_training.ipynb`
- Evaluate in `05_evaluation.ipynb`
- Build UI in `06_streamlit_app.ipynb`
