# Preprocessing Module

## ⚠️ ATTENTION: THIS MODULE NEEDS IMPLEMENTATION

**Status**: STUB IMPLEMENTATIONS ONLY  
**Owner**: NLP/Sentiment Analysis Team  
**Dependencies**: Scraping team provides raw review data

---

## Purpose
Process and analyze review text for sentiment and quality scoring.

## Current State

### ✅ What's Done (Stubs)
- Interface contracts defined
- Function signatures finalized
- Example usage provided

### ❌ What Needs Implementation
- Real sentiment analysis (VADER, DistilBERT, etc.)
- Review quality scoring algorithm
- Batch processing for efficiency
- Model training/loading
- Error handling

---

## Components

### 1. `sentiment_analysis.py` - **NEEDS IMPLEMENTATION**

#### Current Status: STUB
Returns neutral sentiment (0.0) for all reviews.

#### What You Need to Implement

**Function: `analyze_sentiment(text: str, method: str = 'vader') -> Dict`**

**Input:**
```python
text = "This movie was absolutely amazing!"
method = 'vader'  # or 'distilbert'
```

**Expected Output:**
```python
{
    'score': 0.87,      # -1.0 (very negative) to +1.0 (very positive)
    'label': 'positive', # 'positive', 'neutral', or 'negative'
    'confidence': 0.92   # 0.0 to 1.0 confidence score
}
```

**Implementation Suggestions:**
- Use NLTK's VADER for fast, lexicon-based analysis
- Use Hugging Face transformers (DistilBERT) for deep learning
- Support both methods via the `method` parameter
- Handle edge cases (empty text, non-English, etc.)

**Function: `batch_analyze_sentiment(texts: List[str], method: str) -> List[Dict]`**

Same as above but processes multiple texts efficiently.

---

### 2. `review_weighting.py` - **NEEDS IMPLEMENTATION**

#### Current Status: STUB
Returns 0.5 (neutral) weight for all reviews.

#### What You Need to Implement

**Function: `calculate_review_weight(review_data: Dict) -> float`**

**Input:**
```python
review_data = {
    'text': 'Detailed review with analysis...',  # REQUIRED
    'rating': 8.5,                               # OPTIONAL
    'helpful_count': 42,                         # OPTIONAL
    'review_date': datetime.now(),               # OPTIONAL
    'author': 'john_smith',                      # OPTIONAL
    'source': 'imdb',                            # OPTIONAL
    'word_count': 150,                           # OPTIONAL
    'review_length': 850                         # OPTIONAL
}
```

**Expected Output:**
```python
0.85  # float between 0.0 and 1.0
```

**Weighting Factors to Consider:**
1. **Length** (30% weight)
   - Very short (<20 words): 0.5
   - Short (20-50 words): 0.7
   - Medium (50-100 words): 0.9
   - Long (>100 words): 1.0

2. **Helpfulness** (30% weight)
   - No votes: 0.5
   - 1-10 votes: 0.6
   - 10-50 votes: 0.8
   - >50 votes: 1.0

3. **Recency** (20% weight)
   - <7 days: 1.0
   - 7-30 days: 0.9
   - 30-180 days: 0.8
   - >180 days: 0.7

4. **Rating Consistency** (10% weight)
   - Extreme (1/10 or 10/10): 0.7 (might be biased)
   - Moderate (4-7/10): 1.0 (more balanced)

5. **Source Credibility** (10% weight)
   - IMDb: 1.0 (verified users)
   - Reddit: 0.8 (community-based)
   - Twitter: 0.7 (casual/short)

**Implementation Suggestions:**
- Combine factors with weighted average
- Handle missing optional fields gracefully
- Consider outlier detection
- Add normalization

---

## Integration with Scraping System

### Data Flow

```
1. Scrapers collect raw reviews
      ↓
2. Reviews saved to database (by scraping team)
      ↓
3. YOUR CODE: Sentiment analysis processes review text
      ↓
4. YOUR CODE: Quality weighting calculates credibility scores
      ↓
5. Updated database with sentiment_score, sentiment_label, quality_weight
      ↓
6. Recommendation models use weighted, sentiment-scored reviews
```

### Where Your Code Runs

The scraping team will call your functions like this:

```python
from preprocessing.sentiment_analysis import analyze_sentiment
from preprocessing.review_weighting import calculate_review_weight
from database.db import SessionLocal
from database.models import Review

# Get unprocessed reviews
db = SessionLocal()
reviews = db.query(Review).filter(Review.sentiment_score.is_(None)).all()

for review in reviews:
    # YOUR FUNCTION 1: Sentiment analysis
    sentiment = analyze_sentiment(review.text, method='vader')
    review.sentiment_score = sentiment['score']
    review.sentiment_label = sentiment['label']
    
    # YOUR FUNCTION 2: Quality weighting
    weight = calculate_review_weight({
        'text': review.text,
        'rating': review.rating,
        'helpful_count': review.helpful_count,
        'review_date': review.review_date,
        'source': review.source,
        'word_count': review.word_count
    })
    review.quality_weight = weight

db.commit()
db.close()
```

---

## Testing Your Implementation

### Test Data Provided

The database will have real scraped reviews from:
- IMDb: Long, detailed reviews with ratings
- Reddit: Discussion-style, varied length
- Twitter: Short, casual sentiment

### Test Script

```python
# Run this to test your implementation
python -c "
from preprocessing.sentiment_analysis import analyze_sentiment
from preprocessing.review_weighting import calculate_review_weight

# Test 1: Positive sentiment
text1 = 'This movie was absolutely amazing! Best film of the year!'
result1 = analyze_sentiment(text1, 'vader')
assert result1['label'] == 'positive', 'Should detect positive sentiment'
assert result1['score'] > 0.5, 'Score should be positive'

# Test 2: Negative sentiment
text2 = 'Terrible movie. Waste of time and money.'
result2 = analyze_sentiment(text2, 'vader')
assert result2['label'] == 'negative', 'Should detect negative sentiment'
assert result2['score'] < -0.5, 'Score should be negative'

# Test 3: Quality weight
review_high_quality = {
    'text': 'A detailed analysis of the cinematography...' * 20,
    'helpful_count': 100,
    'rating': 8.0
}
weight = calculate_review_weight(review_high_quality)
assert weight > 0.5, 'High quality review should have high weight'

print('✅ All tests passed!')
"
```

---

## Dependencies You'll Need

Add these to `requirements.txt`:

```txt
# For VADER sentiment
nltk==3.8.1
vaderSentiment==3.3.2

# For DistilBERT sentiment
transformers==4.35.0
torch==2.1.0

# For text processing
scikit-learn==1.3.2
```

---

## Performance Requirements

- **Sentiment Analysis**: Process at least 100 reviews/second (VADER)
- **Quality Weighting**: Process at least 1000 reviews/second
- **Batch Processing**: Support batches of 1000+ reviews
- **Memory**: Should handle 10,000 reviews without excessive RAM usage

---

## Questions for Your Team?

Contact the scraping team lead with:
1. Review data format questions
2. Database schema questions
3. Integration timeline
4. Testing coordination

---

## Current Stub Behavior

⚠️ **Until you implement this module:**
- All reviews get sentiment_score = 0.0 (neutral)
- All reviews get sentiment_label = 'neutral'
- All reviews get quality_weight = 0.5 (neutral)

This allows the scraping system to work independently while you develop the NLP components.

- **Purpose**: Analyze sentiment of review text
- **Input**: Review text (str)
- **Output**: Dictionary with:
  ```python
  {
      'score': float,      # -1.0 (negative) to +1.0 (positive)
      'label': str,        # 'positive', 'neutral', 'negative'
      'confidence': float  # 0.0 to 1.0
  }
  ```
- **Methods**:
  - VADER: Fast, lexicon-based (good for social media text)
  - DistilBERT: Deep learning model (more accurate, slower)
- **Usage**: Call `analyze_sentiment(text, method='vader')`

### 2. `review_weighting.py` - Review Quality Scoring
- **Purpose**: Calculate quality/credibility weight for reviews
- **Input**: Review dictionary with fields:
  - `text`: Review content
  - `rating`: Numerical rating (optional)
  - `helpful_count`: Helpful votes (optional)
  - `review_date`: Date posted (optional)
  - `author`: Username (optional)
- **Output**: Quality weight (float, 0.0 to 1.0)
- **Factors**:
  - **Length**: Longer reviews weighted higher (min 50 chars)
  - **Helpfulness**: More helpful votes → higher weight
  - **Recency**: Recent reviews weighted slightly higher
  - **Rating consistency**: Extreme ratings (1/10 or 10/10) get lower weight
  - **Source credibility**: IMDb > Reddit > Twitter

## Sentiment Analysis Details

### VADER (Valence Aware Dictionary and sEntiment Reasoner)
- **Best for**: Social media, informal text, emojis
- **Speed**: Very fast
- **Accuracy**: Good for general sentiment
- **Usage**:
  ```python
  from preprocessing.sentiment_analysis import analyze_sentiment
  result = analyze_sentiment("This movie was amazing!", method='vader')
  # {'score': 0.87, 'label': 'positive', 'confidence': 0.87}
  ```

### DistilBERT (Transformer Model)
- **Best for**: Complex, nuanced text
- **Speed**: Slower (requires GPU for efficiency)
- **Accuracy**: Higher for subtle sentiment
- **Usage**:
  ```python
  result = analyze_sentiment("Not bad, but could be better", method='distilbert')
  ```

## Quality Weight Formula

```
weight = (
    length_score * 0.3 +      # Review length (0.5-1.0)
    helpful_score * 0.3 +      # Helpful votes (0-1.0)
    recency_score * 0.2 +      # How recent (0.5-1.0)
    rating_score * 0.1 +       # Rating consistency (0.5-1.0)
    source_score * 0.1         # Source credibility (0.7-1.0)
)
```

## Usage Example

```python
from preprocessing.sentiment_analysis import analyze_sentiment
from preprocessing.review_weighting import calculate_review_weight
from database.db import SessionLocal
from database.models import Review

# Process reviews
db = SessionLocal()
reviews = db.query(Review).filter(Review.sentiment_score.is_(None)).all()

for review in reviews:
    # Analyze sentiment
    sentiment = analyze_sentiment(review.text, method='vader')
    review.sentiment_score = sentiment['score']
    review.sentiment_label = sentiment['label']
    
    # Calculate quality weight
    weight = calculate_review_weight({
        'text': review.text,
        'rating': review.rating,
        'helpful_count': review.helpful_count,
        'review_date': review.review_date,
        'source': review.source
    })
    review.quality_weight = weight

db.commit()
db.close()
```

## Output Fields
Both functions update the `Review` table:
- `sentiment_score`: -1.0 to +1.0
- `sentiment_label`: 'positive', 'neutral', 'negative'
- `quality_weight`: 0.0 to 1.0

## Performance Notes
- VADER: ~1000 reviews/second
- DistilBERT: ~10-50 reviews/second (CPU), ~200-500/second (GPU)
- Quality scoring: ~5000 reviews/second
