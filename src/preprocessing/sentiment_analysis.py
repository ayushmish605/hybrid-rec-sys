"""
MINIMAL STUB FOR SENTIMENT ANALYSIS
=====================================

This is a PLACEHOLDER implementation for your partners to replace.
The scrapers are independent and don't need this - it's for downstream processing.

YOUR PARTNERS SHOULD IMPLEMENT:
- Real sentiment analysis (VADER, DistilBERT, etc.)
- Replace the stub functions below with actual NLP code

INPUT/OUTPUT CONTRACT - DO NOT CHANGE THESE SIGNATURES
"""

from typing import Dict, List


def analyze_sentiment(text: str, method: str = 'vader') -> Dict[str, any]:
    """
    Analyze sentiment of review text.
    
    Args:
        text: Review text to analyze
        method: 'vader' or 'distilbert' (ignored in stub)
    
    Returns:
        Dictionary with:
        {
            'score': float,      # -1.0 (very negative) to +1.0 (very positive)
            'label': str,        # 'positive', 'neutral', 'negative'
            'confidence': float  # 0.0 to 1.0
        }
    
    STUB BEHAVIOR:
    - Returns neutral sentiment (0.0) for all text
    - Your partners should replace this with real sentiment analysis
    """
    # STUB: Return neutral sentiment
    return {
        'score': 0.0,
        'label': 'neutral',
        'confidence': 0.5
    }


def batch_analyze_sentiment(texts: List[str], method: str = 'vader') -> List[Dict]:
    """
    Analyze sentiment for multiple texts (more efficient for large batches).
    
    Args:
        texts: List of review texts
        method: 'vader' or 'distilbert'
    
    Returns:
        List of sentiment dictionaries (same format as analyze_sentiment)
    
    STUB BEHAVIOR:
    - Returns neutral for all texts
    - Your partners should implement batch processing for efficiency
    """
    # STUB: Return neutral for all
    return [analyze_sentiment(text, method) for text in texts]


# Example usage for partners to test against
if __name__ == "__main__":
    # Test single sentiment
    result = analyze_sentiment("This movie was amazing!")
    print(f"Single: {result}")
    
    # Test batch
    texts = ["Great movie!", "Terrible film", "It was okay"]
    results = batch_analyze_sentiment(texts)
    print(f"Batch: {results}")
