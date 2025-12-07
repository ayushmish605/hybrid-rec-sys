"""
Review quality scoring and weighting algorithm.
"""

import math
from datetime import datetime
from typing import Dict
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ReviewWeighter:
    """Calculate quality scores for reviews based on multiple factors"""
    
    # Default weights for each factor
    DEFAULT_WEIGHTS = {
        'length_weight': 0.25,
        'engagement_weight': 0.30,
        'recency_weight': 0.15,
        'source_weight': 0.20,
        'sentiment_confidence_weight': 0.10
    }
    
    # Source credibility scores (0-1)
    SOURCE_SCORES = {
        'imdb': 1.0,
        'rotten_tomatoes': 0.95,
        'reddit': 0.7,
        'twitter': 0.5
    }
    
    def __init__(self, weights: Dict = None):
        """
        Initialize review weighter.
        
        Args:
            weights: Custom weights dictionary (uses defaults if None)
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        logger.info("ReviewWeighter initialized")
    
    def calculate_quality_score(self, review: Dict) -> float:
        """
        Calculate overall quality score for a review.
        
        Args:
            review: Review dictionary with keys like:
                - text, review_length, word_count
                - source, upvotes, helpful_count, reply_count
                - review_date, sentiment_confidence
        
        Returns:
            Quality score (0-1)
        """
        try:
            # Calculate individual scores
            length_score = self._score_length(review)
            engagement_score = self._score_engagement(review)
            recency_score = self._score_recency(review)
            source_score = self._score_source(review)
            confidence_score = self._score_sentiment_confidence(review)
            
            # Weighted combination
            total_score = (
                self.weights['length_weight'] * length_score +
                self.weights['engagement_weight'] * engagement_score +
                self.weights['recency_weight'] * recency_score +
                self.weights['source_weight'] * source_score +
                self.weights['sentiment_confidence_weight'] * confidence_score
            )
            
            # Normalize to 0-1
            return min(max(total_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.5  # Default middle score
    
    def _score_length(self, review: Dict) -> float:
        """
        Score based on review length.
        Longer reviews are generally more informative, but extremely long ones
        may be less useful.
        
        Args:
            review: Review dictionary
        
        Returns:
            Length score (0-1)
        """
        length = review.get('review_length', 0)
        
        # Define bins with scores
        if length < 20:
            return 0.0  # Too short, invalid
        elif length < 100:
            return 0.5  # Short
        elif length < 300:
            return 0.75  # Medium
        elif length < 1000:
            return 1.0  # Long, ideal
        elif length < 5000:
            return 0.9  # Very long
        else:
            return 0.7  # Extremely long, might be spam
    
    def _score_engagement(self, review: Dict) -> float:
        """
        Score based on engagement metrics (upvotes, likes, helpful votes).
        
        Args:
            review: Review dictionary
        
        Returns:
            Engagement score (0-1)
        """
        source = review.get('source', '')
        
        # Get relevant engagement metric based on source
        if source == 'imdb':
            engagement = review.get('helpful_count', 0)
            # IMDb helpful counts can be high
            threshold = 100
        elif source == 'reddit':
            engagement = review.get('upvotes', 0)
            threshold = 50
        elif source == 'twitter':
            engagement = review.get('upvotes', 0)  # Likes
            threshold = 20
        elif source == 'rotten_tomatoes':
            # RT doesn't always have engagement metrics
            return 0.5  # Neutral score
        else:
            engagement = 0
            threshold = 10
        
        # Logarithmic scaling for engagement
        if engagement <= 0:
            return 0.3  # Default for no engagement
        elif engagement >= threshold:
            return 1.0
        else:
            # Logarithmic interpolation
            score = 0.3 + 0.7 * (math.log(engagement + 1) / math.log(threshold + 1))
            return min(score, 1.0)
    
    def _score_recency(self, review: Dict) -> float:
        """
        Score based on review recency.
        More recent reviews get higher scores, but older reviews
        still have value.
        
        Args:
            review: Review dictionary
        
        Returns:
            Recency score (0-1)
        """
        review_date = review.get('review_date')
        
        if not review_date:
            return 0.5  # Neutral if no date
        
        try:
            # Calculate days since review
            if isinstance(review_date, str):
                review_date = datetime.fromisoformat(review_date)
            
            days_old = (datetime.utcnow() - review_date).days
            
            # Decay function
            # Recent (< 30 days): 1.0
            # 1 year: 0.8
            # 3 years: 0.6
            # 10+ years: 0.4
            
            if days_old < 30:
                return 1.0
            elif days_old < 365:
                return 0.8 + 0.2 * (1 - days_old / 365)
            elif days_old < 1095:  # 3 years
                return 0.6 + 0.2 * (1 - (days_old - 365) / 730)
            else:
                return max(0.4, 0.6 - (days_old - 1095) / 3650 * 0.2)
                
        except Exception as e:
            logger.error(f"Error calculating recency score: {e}")
            return 0.5
    
    def _score_source(self, review: Dict) -> float:
        """
        Score based on source credibility.
        
        Args:
            review: Review dictionary
        
        Returns:
            Source score (0-1)
        """
        source = review.get('source', '').lower()
        return self.SOURCE_SCORES.get(source, 0.5)
    
    def _score_sentiment_confidence(self, review: Dict) -> float:
        """
        Score based on sentiment analysis confidence.
        
        Args:
            review: Review dictionary
        
        Returns:
            Confidence score (0-1)
        """
        confidence = review.get('sentiment_confidence')
        
        if confidence is None:
            return 0.5  # Neutral if not analyzed yet
        
        return float(confidence)
    
    def batch_score_reviews(self, reviews: list) -> list:
        """
        Calculate quality scores for multiple reviews.
        
        Args:
            reviews: List of review dictionaries
        
        Returns:
            Same list with 'quality_score' field added
        """
        for review in reviews:
            review['quality_score'] = self.calculate_quality_score(review)
        
        return reviews
    
    def filter_low_quality(self, reviews: list, threshold: float = 0.3) -> list:
        """
        Filter out low-quality reviews.
        
        Args:
            reviews: List of review dictionaries
            threshold: Minimum quality score (0-1)
        
        Returns:
            Filtered list of reviews
        """
        filtered = [
            r for r in reviews 
            if r.get('quality_score', 0) >= threshold
        ]
        
        logger.info(f"Filtered {len(reviews)} reviews -> {len(filtered)} (threshold={threshold})")
        return filtered


# Example usage
if __name__ == "__main__":
    weighter = ReviewWeighter()
    
    # Test review
    test_review = {
        'text': 'This is an amazing movie with great performances...' * 10,
        'review_length': 500,
        'word_count': 80,
        'source': 'imdb',
        'helpful_count': 150,
        'review_date': datetime(2023, 6, 1),
        'sentiment_confidence': 0.95
    }
    
    score = weighter.calculate_quality_score(test_review)
    print(f"Quality score: {score:.3f}")
