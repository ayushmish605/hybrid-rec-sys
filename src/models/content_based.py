"""
Content-Based Filtering (CBF) recommendation model.
Uses TF-IDF and embeddings for movie similarity.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np
import pickle
from typing import List, Dict, Tuple
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from database.models import get_session, get_engine, Movie, Review
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ContentBasedFilter:
    """Content-based filtering using movie metadata and reviews"""
    
    def __init__(self, embedding_model: str = 'all-MiniLM-L6-v2'):
        """
        Initialize CBF model.
        
        Args:
            embedding_model: SentenceTransformer model name
        """
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        # Will be loaded when trained
        self.tfidf_matrix = None
        self.movie_ids = None
        self.movie_metadata = None
        
        # Sentence embeddings
        try:
            self.embedding_model = SentenceTransformer(embedding_model)
            logger.info(f"Loaded embedding model: {embedding_model}")
        except:
            logger.warning("Could not load SentenceTransformer")
            self.embedding_model = None
        
        self.embeddings = None
    
    def fit(self, movies: List[Movie], db_session):
        """
        Fit the CBF model on movie data.
        
        Args:
            movies: List of Movie objects
            db_session: Database session to fetch reviews
        
        Returns:
            Self for chaining
        """
        logger.info(f"Fitting CBF model on {len(movies)} movies")
        
        self.movie_ids = [m.id for m in movies]
        self.movie_metadata = {}
        
        # Build text corpus for each movie
        corpus = []
        for movie in movies:
            # Combine metadata and reviews
            text = self._build_movie_text(movie, db_session)
            corpus.append(text)
            self.movie_metadata[movie.id] = {
                'title': movie.title,
                'year': movie.year,
                'genres': movie.genres
            }
        
        # Fit TF-IDF
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)
        logger.info(f"TF-IDF matrix shape: {self.tfidf_matrix.shape}")
        
        # Generate embeddings if model available
        if self.embedding_model:
            self.embeddings = self.embedding_model.encode(
                corpus, 
                show_progress_bar=True,
                convert_to_numpy=True
            )
            logger.info(f"Embeddings shape: {self.embeddings.shape}")
        
        return self
    
    def _build_movie_text(self, movie: Movie, db_session) -> str:
        """
        Build text representation of a movie.
        
        Args:
            movie: Movie object
            db_session: Database session
        
        Returns:
            Combined text string
        """
        parts = []
        
        # Title and overview
        if movie.title:
            parts.append(movie.title)
        if movie.overview:
            parts.append(movie.overview)
        
        # Genres
        if movie.genres:
            parts.append(' '.join(movie.genres))
        
        # Top reviews (by quality score)
        reviews = db_session.query(Review).filter_by(
            movie_id=movie.id
        ).order_by(Review.quality_score.desc()).limit(10).all()
        
        review_texts = [r.text for r in reviews if r.text]
        if review_texts:
            parts.append(' '.join(review_texts))
        
        return ' '.join(parts)
    
    def get_similar_movies(
        self, 
        movie_id: int, 
        top_k: int = 10,
        use_embeddings: bool = True
    ) -> List[Tuple[int, float]]:
        """
        Get similar movies to a given movie.
        
        Args:
            movie_id: Target movie ID
            top_k: Number of recommendations
            use_embeddings: Use embeddings vs TF-IDF
        
        Returns:
            List of (movie_id, similarity_score) tuples
        """
        if movie_id not in self.movie_ids:
            logger.warning(f"Movie {movie_id} not in training data")
            return []
        
        movie_idx = self.movie_ids.index(movie_id)
        
        if use_embeddings and self.embeddings is not None:
            # Use embeddings
            similarities = cosine_similarity(
                [self.embeddings[movie_idx]], 
                self.embeddings
            )[0]
        else:
            # Use TF-IDF
            similarities = cosine_similarity(
                self.tfidf_matrix[movie_idx], 
                self.tfidf_matrix
            ).flatten()
        
        # Get top-k similar (excluding itself)
        similar_indices = similarities.argsort()[::-1][1:top_k+1]
        
        results = [
            (self.movie_ids[idx], float(similarities[idx]))
            for idx in similar_indices
        ]
        
        return results
    
    def recommend_for_user(
        self, 
        liked_movie_ids: List[int], 
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """
        Recommend movies based on user's liked movies.
        
        Args:
            liked_movie_ids: List of movie IDs user liked
            top_k: Number of recommendations
        
        Returns:
            List of (movie_id, score) tuples
        """
        # Aggregate similarities from all liked movies
        all_scores = {}
        
        for movie_id in liked_movie_ids:
            similar = self.get_similar_movies(movie_id, top_k=50)
            for sim_id, score in similar:
                if sim_id not in liked_movie_ids:
                    all_scores[sim_id] = all_scores.get(sim_id, 0) + score
        
        # Sort and return top-k
        sorted_movies = sorted(
            all_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:top_k]
        
        return sorted_movies
    
    def save(self, filepath: str):
        """Save model to disk"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'tfidf_vectorizer': self.tfidf_vectorizer,
                'tfidf_matrix': self.tfidf_matrix,
                'movie_ids': self.movie_ids,
                'movie_metadata': self.movie_metadata,
                'embeddings': self.embeddings
            }, f)
        logger.info(f"Saved CBF model to {filepath}")
    
    def load(self, filepath: str):
        """Load model from disk"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.tfidf_vectorizer = data['tfidf_vectorizer']
            self.tfidf_matrix = data['tfidf_matrix']
            self.movie_ids = data['movie_ids']
            self.movie_metadata = data['movie_metadata']
            self.embeddings = data['embeddings']
        logger.info(f"Loaded CBF model from {filepath}")


# Stub/placeholder code
if __name__ == "__main__":
    print("Content-Based Filtering - Placeholder")
    print("TODO: Train model on full dataset")
    print("TODO: Implement advanced feature engineering")
    print("TODO: Add genre weighting")
