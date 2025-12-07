"""
Hybrid Recommendation System combining CBF and CF.
"""

import numpy as np
from typing import List, Tuple, Dict
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from models.content_based import ContentBasedFilter
from models.collaborative import CollaborativeFilter
from utils.logger import setup_logger

logger = setup_logger(__name__)


class HybridRecommender:
    """Hybrid recommendation system combining multiple approaches"""
    
    def __init__(
        self, 
        cbf_model: ContentBasedFilter = None,
        cf_model: CollaborativeFilter = None,
        alpha: float = 0.6,
        beta: float = 0.4
    ):
        """
        Initialize hybrid recommender.
        
        Args:
            cbf_model: Content-based filtering model
            cf_model: Collaborative filtering model
            alpha: Weight for CBF (0-1)
            beta: Weight for CF (0-1)
        """
        self.cbf_model = cbf_model or ContentBasedFilter()
        self.cf_model = cf_model or CollaborativeFilter()
        
        # Normalize weights
        total = alpha + beta
        self.alpha = alpha / total
        self.beta = beta / total
        
        logger.info(f"HybridRecommender initialized (α={self.alpha:.2f}, β={self.beta:.2f})")
    
    def recommend(
        self, 
        user_id: int = None,
        liked_movies: List[int] = None,
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """
        Generate hybrid recommendations.
        
        Args:
            user_id: User ID for CF
            liked_movies: List of liked movie IDs for CBF
            top_k: Number of recommendations
        
        Returns:
            List of (movie_id, score) tuples
        """
        cbf_scores = {}
        cf_scores = {}
        
        # Get CBF recommendations
        if liked_movies and self.cbf_model:
            try:
                cbf_recs = self.cbf_model.recommend_for_user(liked_movies, top_k=50)
                cbf_scores = {movie_id: score for movie_id, score in cbf_recs}
            except Exception as e:
                logger.error(f"CBF error: {e}")
        
        # Get CF recommendations
        if user_id and self.cf_model:
            try:
                cf_recs = self.cf_model.recommend_for_user(user_id, top_k=50)
                cf_scores = {movie_id: score for movie_id, score in cf_recs}
            except Exception as e:
                logger.error(f"CF error: {e}")
        
        # Combine scores
        all_movies = set(cbf_scores.keys()) | set(cf_scores.keys())
        hybrid_scores = {}
        
        for movie_id in all_movies:
            cbf_score = cbf_scores.get(movie_id, 0)
            cf_score = cf_scores.get(movie_id, 0)
            
            # Weighted combination
            hybrid_scores[movie_id] = (
                self.alpha * self._normalize_score(cbf_score, max_score=1.0) +
                self.beta * self._normalize_score(cf_score, max_score=5.0)
            )
        
        # Sort and return top-k
        recommendations = sorted(
            hybrid_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        return recommendations
    
    def _normalize_score(self, score: float, max_score: float = 1.0) -> float:
        """Normalize score to 0-1 range"""
        return min(max(score / max_score, 0.0), 1.0)
    
    def explain_recommendation(
        self, 
        movie_id: int,
        user_id: int = None,
        liked_movies: List[int] = None
    ) -> Dict:
        """
        Explain why a movie was recommended.
        
        Args:
            movie_id: Recommended movie ID
            user_id: User ID
            liked_movies: Liked movie IDs
        
        Returns:
            Dictionary with explanation details
        """
        explanation = {
            'movie_id': movie_id,
            'cbf_contribution': 0.0,
            'cf_contribution': 0.0,
            'similar_movies': [],
            'user_similarity': None
        }
        
        # CBF explanation
        if liked_movies and self.cbf_model:
            # Find which liked movie is most similar
            max_sim = 0.0
            most_similar = None
            
            for liked_id in liked_movies:
                similar = self.cbf_model.get_similar_movies(liked_id, top_k=20)
                for sim_id, score in similar:
                    if sim_id == movie_id and score > max_sim:
                        max_sim = score
                        most_similar = liked_id
            
            explanation['cbf_contribution'] = max_sim * self.alpha
            explanation['similar_movies'] = [most_similar] if most_similar else []
        
        # CF explanation
        if user_id and self.cf_model:
            predicted_rating = self.cf_model.predict_rating(user_id, movie_id)
            explanation['cf_contribution'] = (predicted_rating / 5.0) * self.beta
        
        explanation['total_score'] = (
            explanation['cbf_contribution'] + explanation['cf_contribution']
        )
        
        return explanation
    
    def save(self, cbf_path: str, cf_path: str):
        """Save both models"""
        if self.cbf_model:
            self.cbf_model.save(cbf_path)
        if self.cf_model:
            self.cf_model.save(cf_path)
        logger.info("Saved hybrid model components")
    
    def load(self, cbf_path: str, cf_path: str):
        """Load both models"""
        if self.cbf_model:
            self.cbf_model.load(cbf_path)
        if self.cf_model:
            self.cf_model.load(cf_path)
        logger.info("Loaded hybrid model components")


# Stub/placeholder code
if __name__ == "__main__":
    print("Hybrid Recommender - Placeholder")
    print("TODO: Implement meta-learning approach")
    print("TODO: Add context-aware weighting")
    print("TODO: Implement ensemble methods")
    print("TODO: Add review sentiment as feature")
