"""
Sentiment analysis pipeline for movie reviews.
Uses transformer models for accurate sentiment detection.
"""

from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import torch
from typing import Dict, List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SentimentAnalyzer:
    """Analyze sentiment of movie reviews using transformers and VADER"""
    
    def __init__(
        self, 
        model_name: str = "distilbert-base-uncased-finetuned-sst-2-english",
        use_gpu: bool = None
    ):
        """
        Initialize sentiment analyzer.
        
        Args:
            model_name: HuggingFace model name
            use_gpu: Whether to use GPU (auto-detects if None)
        """
        # Determine device
        if use_gpu is None:
            use_gpu = torch.cuda.is_available()
        
        device = 0 if use_gpu else -1
        
        try:
            # Load transformer model
            self.transformer = pipeline(
                "sentiment-analysis",
                model=model_name,
                device=device,
                max_length=512,
                truncation=True
            )
            logger.info(f"Loaded transformer model: {model_name}")
        except Exception as e:
            logger.error(f"Error loading transformer model: {e}")
            self.transformer = None
        
        # Load VADER as backup/supplement
        try:
            self.vader = SentimentIntensityAnalyzer()
            logger.info("Loaded VADER sentiment analyzer")
        except Exception as e:
            logger.error(f"Error loading VADER: {e}")
            self.vader = None
        
        logger.info(f"SentimentAnalyzer initialized (GPU: {use_gpu})")
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of a single text.
        
        Args:
            text: Review text
        
        Returns:
            Dictionary with sentiment scores:
            {
                'label': 'POSITIVE' or 'NEGATIVE',
                'score': confidence (0-1),
                'compound': compound score (-1 to 1),
                'vader_scores': {...}
            }
        """
        if not text or len(text) < 10:
            return {
                'label': 'NEUTRAL',
                'score': 0.5,
                'compound': 0.0,
                'vader_scores': None
            }
        
        results = {}
        
        # Transformer analysis
        if self.transformer:
            try:
                transformer_result = self.transformer(text[:512])[0]  # Limit length
                results['label'] = transformer_result['label']
                results['score'] = transformer_result['score']
            except Exception as e:
                logger.error(f"Transformer analysis error: {e}")
                results['label'] = 'NEUTRAL'
                results['score'] = 0.5
        
        # VADER analysis (as supplement)
        if self.vader:
            try:
                vader_scores = self.vader.polarity_scores(text)
                results['vader_scores'] = vader_scores
                results['compound'] = vader_scores['compound']
            except Exception as e:
                logger.error(f"VADER analysis error: {e}")
                results['compound'] = 0.0
                results['vader_scores'] = None
        
        # Convert to unified format
        return self._unify_sentiment(results)
    
    def _unify_sentiment(self, results: Dict) -> Dict:
        """
        Unify transformer and VADER results into consistent format.
        
        Args:
            results: Raw results from both analyzers
        
        Returns:
            Unified sentiment dictionary
        """
        # Map transformer label to sentiment
        label = results.get('label', 'NEUTRAL')
        score = results.get('score', 0.5)
        compound = results.get('compound', 0.0)
        
        # Normalize label
        if label == 'POSITIVE':
            sentiment_label = 'positive'
            sentiment_score = score
        elif label == 'NEGATIVE':
            sentiment_label = 'negative'
            sentiment_score = -score
        else:
            sentiment_label = 'neutral'
            sentiment_score = 0.0
        
        # Combine with VADER compound score if available
        if compound != 0.0:
            # Average transformer and VADER
            combined_score = (sentiment_score + compound) / 2
        else:
            combined_score = sentiment_score
        
        # Determine final label based on combined score
        if combined_score > 0.05:
            final_label = 'positive'
        elif combined_score < -0.05:
            final_label = 'negative'
        else:
            final_label = 'neutral'
        
        return {
            'sentiment_label': final_label,
            'sentiment_score': combined_score,  # -1 to 1
            'sentiment_confidence': abs(score) if score else 0.5,
            'vader_compound': compound,
            'raw_transformer_label': label,
            'raw_transformer_score': score
        }
    
    def batch_analyze(self, texts: List[str], batch_size: int = 32) -> List[Dict]:
        """
        Analyze sentiment for multiple texts in batches.
        
        Args:
            texts: List of review texts
            batch_size: Batch size for processing
        
        Returns:
            List of sentiment dictionaries
        """
        results = []
        
        # Process in batches for efficiency
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            try:
                if self.transformer:
                    # Transformer batch processing
                    truncated_batch = [t[:512] for t in batch]
                    transformer_results = self.transformer(truncated_batch)
                    
                    for j, text in enumerate(batch):
                        vader_scores = None
                        compound = 0.0
                        
                        # Add VADER for this text
                        if self.vader:
                            vader_scores = self.vader.polarity_scores(text)
                            compound = vader_scores['compound']
                        
                        # Combine results
                        combined = {
                            'label': transformer_results[j]['label'],
                            'score': transformer_results[j]['score'],
                            'compound': compound,
                            'vader_scores': vader_scores
                        }
                        
                        results.append(self._unify_sentiment(combined))
                else:
                    # VADER only
                    for text in batch:
                        sentiment = self.analyze_sentiment(text)
                        results.append(sentiment)
                        
            except Exception as e:
                logger.error(f"Batch analysis error: {e}")
                # Add neutral sentiments for failed batch
                for _ in batch:
                    results.append({
                        'sentiment_label': 'neutral',
                        'sentiment_score': 0.0,
                        'sentiment_confidence': 0.5,
                        'vader_compound': 0.0
                    })
        
        logger.info(f"Analyzed sentiment for {len(results)} texts")
        return results
    
    def analyze_reviews(self, reviews: List[Dict]) -> List[Dict]:
        """
        Analyze sentiment for a list of review dictionaries.
        Updates reviews in-place with sentiment fields.
        
        Args:
            reviews: List of review dictionaries with 'text' field
        
        Returns:
            Same list with sentiment fields added
        """
        texts = [r.get('text', '') for r in reviews]
        sentiments = self.batch_analyze(texts)
        
        # Update reviews with sentiment data
        for review, sentiment in zip(reviews, sentiments):
            review.update(sentiment)
        
        return reviews


# Example usage
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    
    # Test reviews
    test_reviews = [
        "This movie was absolutely amazing! Best film I've seen all year.",
        "Terrible waste of time. Poor acting and boring plot.",
        "It was okay, nothing special but not terrible either."
    ]
    
    for text in test_reviews:
        sentiment = analyzer.analyze_sentiment(text)
        print(f"\nText: {text}")
        print(f"Sentiment: {sentiment['sentiment_label']}")
        print(f"Score: {sentiment['sentiment_score']:.3f}")
        print(f"Confidence: {sentiment['sentiment_confidence']:.3f}")
