# Models Module

## Purpose
Recommendation algorithms: content-based, collaborative filtering, and hybrid.

## Components

### 1. `content_based.py` - Content-Based Filtering
- **Purpose**: Recommend movies based on movie metadata similarity
- **Input**:
  - Movie ID (int) or title (str)
  - Number of recommendations (int)
- **Features Used**:
  - Genres (TF-IDF vectorization)
  - Overview text (TF-IDF vectorization)
  - Director, cast (if available)
  - Sentiment of reviews
- **Output**: List of (movie_id, similarity_score) tuples
- **Algorithm**: Cosine similarity on TF-IDF vectors

### 2. `collaborative.py` - Collaborative Filtering
- **Purpose**: Recommend based on user rating patterns
- **Input**:
  - User ID (int)
  - Number of recommendations (int)
- **Methods**:
  - **User-based**: Find similar users, recommend their liked movies
  - **Item-based**: Find similar movies based on co-rating patterns
  - **Matrix Factorization**: SVD/ALS for latent factors
- **Output**: List of (movie_id, predicted_rating) tuples
- **Requirements**: Sufficient user-item ratings in database

### 3. `hybrid.py` - Hybrid Recommendation
- **Purpose**: Combine content-based and collaborative filtering
- **Input**:
  - User ID (int, optional)
  - Movie ID (int, optional for similarity-based)
  - Number of recommendations (int)
  - Weights for each method (dict)
- **Output**: Ranked list of movie recommendations
- **Strategies**:
  - **Weighted**: Combine scores with configurable weights
  - **Switching**: Use collaborative if enough data, else content-based
  - **Cascade**: Filter with one method, rank with another
  - **Feature augmentation**: Use collaborative features in content model

## Usage Examples

### Content-Based Recommendations
```python
from models.content_based import ContentBasedRecommender
from database.db import SessionLocal

db = SessionLocal()
recommender = ContentBasedRecommender(db)

# Get movies similar to "Inception"
recommendations = recommender.recommend(
    movie_title="Inception",
    n_recommendations=10
)

for movie_id, score in recommendations:
    movie = db.query(Movie).get(movie_id)
    print(f"{movie.title}: {score:.3f}")
```

### Collaborative Filtering
```python
from models.collaborative import CollaborativeRecommender

recommender = CollaborativeRecommender(db)

# Get recommendations for user 123
recommendations = recommender.recommend_for_user(
    user_id=123,
    n_recommendations=10
)
```

### Hybrid Recommendations
```python
from models.hybrid import HybridRecommender

recommender = HybridRecommender(db)

# Balanced hybrid for user with some history
recommendations = recommender.recommend(
    user_id=123,
    n_recommendations=10,
    weights={
        'content': 0.4,
        'collaborative': 0.6
    }
)
```

## Model Training

### Content-Based
- **Training**: Fits TF-IDF vectorizers on movie corpus
- **Input**: All movies in database
- **Output**: Saved vectorizers and similarity matrix
- **Retraining**: When new movies added or metadata updated

### Collaborative
- **Training**: Fits matrix factorization on user-item ratings
- **Input**: User-Movie-Rating triples
- **Output**: User and movie latent factor matrices
- **Retraining**: When new ratings added (batch or online)

### Hybrid
- **Training**: Trains both sub-models
- **Input**: Movies + ratings
- **Output**: Combined recommendation engine
- **Tuning**: Cross-validation to optimize weights

## Evaluation Metrics
- **Precision@K**: Fraction of top-K recommendations that are relevant
- **Recall@K**: Fraction of relevant items in top-K
- **NDCG**: Normalized Discounted Cumulative Gain
- **MAE/RMSE**: Mean Absolute/Root Mean Squared Error (for ratings)
- **Coverage**: % of items that can be recommended
- **Diversity**: How different recommended items are

## Cold Start Handling
- **New users**: Use content-based or popularity-based
- **New movies**: Use content-based similarity
- **New users + new movies**: Use metadata and popularity

## Status
⚠️ **Currently**: Skeleton implementations in place
 **Next Steps**: Train models after scraping sufficient review data
 **Goal**: Full hybrid system with sentiment-weighted recommendations
