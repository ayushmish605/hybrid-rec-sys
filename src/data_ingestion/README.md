# Data Ingestion Module

## Purpose
Load movie data from external sources into the database.

## Components

### 1. `tmdb_loader.py` - TMDB CSV Loader
- **Purpose**: Parse and load TMDB movie data from CSV files
- **Input**: 
  - CSV file path (str)
  - Expected CSV columns:
    - `title`: Movie title
    - `release_date`: YYYY-MM-DD format
    - `vote_average`: Rating (0-10)
    - `vote_count`: Number of votes
    - `genres`: Genre names or IDs
    - `overview`: Movie description
    - `popularity`: Popularity score
    - `runtime`: Duration in minutes
    - `original_language`: Language code
- **Output**: 
  - Loads movies into `Movie` table
  - Returns count of movies loaded

### 2. `__init__.py` - Package Exports
Exposes the TMDBDataLoader class.

## Usage

```python
from data_ingestion.tmdb_loader import TMDBDataLoader
from database.db import SessionLocal

# Create loader
loader = TMDBDataLoader('data/tmdb_commercial_movies_2016_2024.csv')

# Load CSV into pandas
loader.load_csv()

# Parse and insert movies
db = SessionLocal()
for _, row in loader.df.iterrows():
    movie_data = loader.parse_movie(row)
    if movie_data:
        # Check if exists
        existing = db.query(Movie).filter(
            Movie.title == movie_data['title'],
            Movie.release_year == movie_data['release_year']
        ).first()
        
        if not existing:
            movie = Movie(**movie_data)
            db.add(movie)

db.commit()
db.close()
```

## Data Processing
1. **CSV Loading**: Reads CSV with pandas, handles encoding
2. **Genre Parsing**: Converts genre strings/IDs to pipe-delimited format
3. **Date Parsing**: Extracts year from release_date
4. **Type Conversion**: Ensures proper data types for database
5. **Validation**: Skips rows with missing required fields

## Error Handling
- Flexible CSV parsing (handles various column name formats)
- Skips malformed rows with logging
- Handles missing/null values gracefully
- Duplicate detection (title + year combination)

## Expected CSV Format
The loader is designed for TMDB commercial movie datasets with these characteristics:
- One movie per row
- Release years 2016-2024 (configurable)
- Minimum vote count for quality filtering
- English language movies (can be adjusted)
