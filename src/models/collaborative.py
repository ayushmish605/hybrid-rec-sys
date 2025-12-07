"""
Collaborative Filtering (CF) recommendation model.
Uses matrix factorization (SVD) for user-item ratings.
"""

from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix
import numpy as np
import pickle
from typing import List, Tuple, Dict
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from database.models import get_session, UserRating
from utils.logger import setup_logger

logger = setup_logger(__name__)


class CollaborativeFilter:
    """Collaborative filtering using matrix factorization"""
    
    def __init__(self, n_factors: int = 100):
        """
        Initialize CF model.
        
        Args:
            n_factors: Number of latent factors for SVD
        """
        self.n_factors = n_factors
        self.svd = TruncatedSVD(n_components=n_factors, random_state=42)
        
        self.user_factors = None
        self.item_factors = None
        self.user_ids = None
        self.movie_ids = None
        self.rating_matrix = None
    
    def fit(self, ratings: List[UserRating]):
        """
        Fit CF model on user ratings.
        
        Args:
            ratings: List of UserRating objects
        
        Returns:
            Self for chaining
        """
        logger.info(f"Fitting CF model on {len(ratings)} ratings")
        
        # Build user-item rating matrix
        user_set = set(r.user_id for r in ratings)
        movie_set = set(r.movie_id for r in ratings)
        
        self.user_ids = sorted(list(user_set))
        self.movie_ids = sorted(list(movie_set))
        
        user_idx_map = {uid: idx for idx, uid in enumerate(self.user_ids)}
        movie_idx_map = {mid: idx for idx, mid in enumerate(self.movie_ids)}
        
        # Create sparse matrix
        rows = []
        cols = []
        data = []
        
        for rating in ratings:
            user_idx = user_idx_map[rating.user_id]
            movie_idx = movie_idx_map[rating.movie_id]
            rows.append(user_idx)
            cols.append(movie_idx)
            data.append(rating.rating)
        
        self.rating_matrix = csr_matrix(
            (data, (rows, cols)),
            shape=(len(self.user_ids), len(self.movie_ids))
        )
        
        logger.info(f"Rating matrix shape: {self.rating_matrix.shape}")
        
        # Apply SVD
        self.user_factors = self.svd.fit_transform(self.rating_matrix)
        self.item_factors = self.svd.components_.T
        
        logger.info(f"User factors shape: {self.user_factors.shape}")
        logger.info(f"Item factors shape: {self.item_factors.shape}")
        
        return self
    
    def predict_rating(self, user_id: int, movie_id: int) -> float:
        """
        Predict rating for user-movie pair.
        
        Args:
            user_id: User ID
            movie_id: Movie ID
        
        Returns:
            Predicted rating (1-5 scale typically)
        """
        if user_id not in self.user_ids or movie_id not in self.movie_ids:
            return 3.0  # Default neutral rating
        
        user_idx = self.user_ids.index(user_id)
        movie_idx = self.movie_ids.index(movie_id)
        
        prediction = np.dot(self.user_factors[user_idx], self.item_factors[movie_idx])
        
        # Clip to valid rating range
        return np.clip(prediction, 1.0, 5.0)
    
    def recommend_for_user(
        self, 
        user_id: int, 
        top_k: int = 10,
        exclude_rated: bool = True
    ) -> List[Tuple[int, float]]:
        """
        Recommend movies for a user.
        
        Args:
            user_id: Target user ID
            top_k: Number of recommendations
            exclude_rated: Whether to exclude already-rated movies
        
        Returns:
            List of (movie_id, predicted_rating) tuples
        """
        if user_id not in self.user_ids:
            logger.warning(f"User {user_id} not in training data")
            return []
        
        user_idx = self.user_ids.index(user_id)
        
        # Predict ratings for all movies
        predictions = np.dot(self.user_factors[user_idx], self.item_factors.T)
        
        # Get rated movies for this user
        if exclude_rated:
            user_ratings = self.rating_matrix[user_idx].toarray().flatten()
            rated_mask = user_ratings > 0
            predictions[rated_mask] = -np.inf  # Exclude rated movies
        
        # Get top-k
        top_indices = predictions.argsort()[::-1][:top_k]
        
        recommendations = [
            (self.movie_ids[idx], float(predictions[idx]))
            for idx in top_indices
        ]
        
        return recommendations
    
    def get_similar_movies(
        self, 
        movie_id: int, 
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """
        Get similar movies based on item factors.
        
        Args:
            movie_id: Target movie ID
            top_k: Number of similar movies
        
        Returns:
            List of (movie_id, similarity_score) tuples
        """
        if movie_id not in self.movie_ids:
            logger.warning(f"Movie {movie_id} not in training data")
            return []
        
        movie_idx = self.movie_ids.index(movie_id)
        
        # Compute cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(
            [self.item_factors[movie_idx]],
            self.item_factors
        )[0]
        
        # Get top-k (excluding itself)
        similar_indices = similarities.argsort()[::-1][1:top_k+1]
        
        results = [
            (self.movie_ids[idx], float(similarities[idx]))
            for idx in similar_indices
        ]
        
        return results
    
    def save(self, filepath: str):
        """Save model to disk"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'svd': self.svd,
                'user_factors': self.user_factors,
                'item_factors': self.item_factors,
                'user_ids': self.user_ids,
                'movie_ids': self.movie_ids,
                'rating_matrix': self.rating_matrix
            }, f)
        logger.info(f"Saved CF model to {filepath}")
    
    def load(self, filepath: str):
        """Load model from disk"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.svd = data['svd']
            self.user_factors = data['user_factors']
            self.item_factors = data['item_factors']
            self.user_ids = data['user_ids']
            self.movie_ids = data['movie_ids']
            self.rating_matrix = data['rating_matrix']
        logger.info(f"Loaded CF model from {filepath}")


# Stub/placeholder code
if __name__ == "__main__":
    print("Collaborative Filtering - Placeholder")
    print("TODO: Implement user-user CF variant")
    print("TODO: Implement item-item CF variant")
    print("TODO: Add bias terms")
    print("TODO: Experiment with ALS, NMF")
