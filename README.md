# Hybrid Movie Recommendation System

A sophisticated recommendation engine combining content-based filtering, collaborative filtering, and NLP-based review analysis.

## Project Structure

```
hybrid-rec-sys/
├── config/                 # Configuration files
│   ├── config.yaml        # Main configuration
│   └── api_keys.yaml      # API keys (gitignored)
├── data/                  # Data storage
│   ├── raw/              # Raw scraped data
│   ├── processed/        # Cleaned data
│   └── database/         # SQLite database
├── src/                  # Source code
│   ├── scrapers/         # Web scraping modules
│   ├── database/         # Database operations
│   ├── preprocessing/    # Data cleaning & NLP
│   ├── models/          # Recommendation models
│   ├── evaluation/      # Metrics and testing
│   └── utils/           # Helper functions
├── notebooks/           # Jupyter notebooks for analysis
├── tests/              # Unit tests
└── requirements.txt    # Python dependencies
```

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API keys:**
   - Copy `config/api_keys.example.yaml` to `config/api_keys.yaml`
   - Add your API keys (Gemini, Reddit, Twitter)

3. **Initialize database:**
   ```bash
   python src/database/init_db.py
   ```

4. **Run scraping pipeline:**
   ```bash
   python src/main.py --mode scrape --limit 2000
   ```

## Features

### Data Collection
- **Multi-source scraping**: Reddit, Twitter, IMDb, Rotten Tomatoes
- **Intelligent search**: Gemini API generates optimal hashtags/search terms
- **Rate limiting**: Respects API limits and implements delays
- **Review weighting**: Quality scoring based on length, engagement, source

### Analysis
- **Sentiment analysis**: Transformer-based models for review sentiment
- **NLP embeddings**: Sentence transformers for semantic similarity
- **SQL storage**: Efficient querying and joins

### Recommendation Models
- **Content-based filtering**: TF-IDF and embeddings
- **Collaborative filtering**: Matrix factorization (SVD)
- **Hybrid approach**: Weighted and meta-learning combinations

## Usage

See `notebooks/demo.ipynb` for examples.

## Evaluation Metrics
- RMSE (rating prediction)
- Precision@k, Recall@k
- MAP@k (Mean Average Precision)
