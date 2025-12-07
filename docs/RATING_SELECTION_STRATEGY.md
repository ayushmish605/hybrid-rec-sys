# Rating Selection Strategy (Timestamp-Based)

## The Problem with "Newer = Better"

**Assumption I made**: "IMDb scraped live is newer than TMDB CSV"
**Reality**: We don't know when the CSV was created or when TMDB last updated

## Better Approach: Timestamp Comparison

### Strategy 1: Use Both with Metadata

```python
def get_best_rating(movie):
    """
    Select rating based on recency AND vote count
    """
    ratings = []
    
    # Option 1: TMDB (from CSV)
    if movie.tmdb_rating:
        ratings.append({
            'value': movie.tmdb_rating,
            'votes': movie.tmdb_vote_count,
            'source': 'tmdb_csv',
            'timestamp': movie.csv_import_date,  # When CSV was loaded
            'age_days': (now() - movie.csv_import_date).days
        })
    
    # Option 2: IMDb (scraped)
    if movie.imdb_rating:
        ratings.append({
            'value': movie.imdb_rating,
            'votes': movie.imdb_vote_count,
            'source': 'imdb_scraped',
            'timestamp': movie.scraped_at,
            'age_days': (now() - movie.scraped_at).days
        })
    
    # Selection logic:
    # 1. If one is significantly more recent (>30 days), prefer it
    # 2. If similar age, prefer higher vote count
    # 3. If similar votes, average them
    
    if len(ratings) == 2:
        age_diff = abs(ratings[0]['age_days'] - ratings[1]['age_days'])
        
        if age_diff > 30:
            # One is significantly newer
            return min(ratings, key=lambda x: x['age_days'])
        else:
            # Similar age, prefer more votes
            if ratings[0]['votes'] > ratings[1]['votes'] * 1.5:
                return ratings[0]
            elif ratings[1]['votes'] > ratings[0]['votes'] * 1.5:
                return ratings[1]
            else:
                # Similar votes, average them
                return {
                    'value': (ratings[0]['value'] + ratings[1]['value']) / 2,
                    'source': 'averaged',
                    'votes': max(ratings[0]['votes'], ratings[1]['votes'])
                }
    
    return ratings[0] if ratings else None
```

### Strategy 2: Use Both as Validation

```python
def validate_ratings(movie):
    """
    Use both ratings to detect anomalies
    """
    if movie.tmdb_rating and movie.imdb_rating:
        diff = abs(movie.tmdb_rating - movie.imdb_rating)
        
        # If difference > 1.0, investigate
        if diff > 1.0:
            logger.warning(
                f"{movie.title}: Large rating difference! "
                f"TMDB={movie.tmdb_rating}, IMDb={movie.imdb_rating}"
            )
            
            # Could indicate:
            # - Different rating scales
            # - Regional differences
            # - Controversy (rating changed dramatically)
            # - Data quality issue
```

### Strategy 3: Weighted Combination

```python
def get_weighted_rating(movie):
    """
    Combine both ratings with confidence weighting
    """
    if movie.tmdb_rating and movie.imdb_rating:
        # Weight by vote count
        tmdb_weight = movie.tmdb_vote_count
        imdb_weight = movie.imdb_vote_count
        
        total_weight = tmdb_weight + imdb_weight
        
        weighted_rating = (
            (movie.tmdb_rating * tmdb_weight + 
             movie.imdb_rating * imdb_weight) / 
            total_weight
        )
        
        return weighted_rating
    
    # Fallback to whichever exists
    return movie.imdb_rating or movie.tmdb_rating
```

## Recommended Configuration

### Add to Database Schema:

```python
class Movie(Base):
    # ... existing fields ...
    
    # TMDB data
    tmdb_rating = Column(Float)
    tmdb_vote_count = Column(Integer)
    tmdb_data_date = Column(DateTime)  # NEW: When CSV was exported
    
    # IMDb data
    imdb_rating = Column(Float)
    imdb_vote_count = Column(Integer)
    imdb_scraped_at = Column(DateTime)  # When we scraped
    
    # Combined
    @property
    def recommended_rating(self):
        """Smart rating selection"""
        # If we scraped IMDb recently (< 7 days), trust it
        if self.imdb_rating and self.imdb_scraped_at:
            if (datetime.now() - self.imdb_scraped_at).days < 7:
                return self.imdb_rating
        
        # If both exist and similar age, average weighted by votes
        if self.tmdb_rating and self.imdb_rating:
            return self._weighted_average()
        
        # Otherwise use whatever exists
        return self.imdb_rating or self.tmdb_rating
    
    def _weighted_average(self):
        """Average ratings weighted by vote count"""
        tmdb_w = self.tmdb_vote_count or 1
        imdb_w = self.imdb_vote_count or 1
        
        return (
            (self.tmdb_rating * tmdb_w + self.imdb_rating * imdb_w) / 
            (tmdb_w + imdb_w)
        )
```

## What We Actually Know

### TMDB CSV:
- ✅ **What**: Ratings from TMDB database
- ✅ **Accuracy**: Generally reliable (large user base)
- ❓ **When**: Unknown (depends on when YOU exported it)
- ✅ **Completeness**: All 2000 movies have data

### IMDb Scraping:
- ✅ **What**: Ratings from IMDb.com
- ✅ **Accuracy**: Generally reliable (large user base)
- ✅ **When**: Exactly when we scrape (we timestamp it)
- ❓ **Completeness**: Only if we successfully find the movie

## Real-World Scenarios

### Scenario 1: Fresh CSV
```
Your CSV exported: Dec 1, 2025
IMDb scraped: Dec 7, 2025
Age difference: 6 days
→ Both very current, use weighted average
```

### Scenario 2: Old CSV
```
Your CSV exported: Jan 1, 2024
IMDb scraped: Dec 7, 2025
Age difference: ~700 days
→ IMDb much fresher, prefer it
```

### Scenario 3: Can't determine CSV age
```
Your CSV date: Unknown
IMDb scraped: Dec 7, 2025
→ Use both, weight by vote count
```

## Bottom Line

**I was making an assumption** that your CSV is older. The **correct approach** is:

1. ✅ **Keep both ratings** (TMDB + IMDb)
2. ✅ **Track timestamps** (when each was collected)
3. ✅ **Weight by vote count** (more votes = more reliable)
4. ✅ **Prefer fresher data** (if age difference > 30 days)
5. ✅ **Average similar-age ratings** (use both as validation)

This is more robust than blindly preferring one source!
