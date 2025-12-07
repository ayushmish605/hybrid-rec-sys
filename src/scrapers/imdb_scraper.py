"""
IMDb scraper - Highest priority source for quality reviews.
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)


class IMDbScraper:
    """Scrape reviews from IMDb"""
    
    BASE_URL = "https://www.imdb.com"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    def __init__(self, rate_limit: float = 2.0):
        """
        Initialize IMDb scraper.
        
        Args:
            rate_limit: Seconds between requests
        """
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def search_movie(self, title: str, year: Optional[int] = None) -> Optional[str]:
        """
        Search for a movie and return its IMDb ID using IMDb's search API.
        
        Args:
            title: Movie title
            year: Release year
        
        Returns:
            IMDb ID (e.g., 'tt1375666') or None
        """
        try:
            search_query = title
            if year:
                search_query += f" {year}"
            
            search_url = f"{self.BASE_URL}/find"
            params = {'q': search_query, 's': 'tt', 'ttype': 'ft'}
            
            time.sleep(self.rate_limit)
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for IMDb's dynamic structure
            # Method 1: Look for data-testid attribute (new IMDb)
            result = soup.find('a', {'data-testid': 'search-result-title'})
            if result and 'href' in result.attrs:
                href = result['href']
                match = re.search(r'/(tt\d+)/', href)
                if match:
                    imdb_id = match.group(1)
                    logger.info(f"Found IMDb ID for '{title}': {imdb_id}")
                    return imdb_id
            
            # Method 2: Look for ipc-metadata-list-summary-item (new IMDb structure)
            result = soup.find('a', class_=lambda x: x and 'ipc-metadata-list-summary-item__t' in x)
            if result and 'href' in result.attrs:
                href = result['href']
                match = re.search(r'/(tt\d+)/', href)
                if match:
                    imdb_id = match.group(1)
                    logger.info(f"Found IMDb ID for '{title}': {imdb_id}")
                    return imdb_id
            
            # Method 3: Find any link with /title/tt pattern
            all_links = soup.find_all('a', href=re.compile(r'/title/tt\d+/'))
            if all_links:
                href = all_links[0]['href']
                match = re.search(r'/(tt\d+)/', href)
                if match:
                    imdb_id = match.group(1)
                    logger.info(f"Found IMDb ID for '{title}': {imdb_id}")
                    return imdb_id
            
            logger.warning(f"Could not find IMDb ID for '{title}'")
            return None
            
        except Exception as e:
            logger.error(f"Error searching IMDb for '{title}': {e}")
            return None
    
    def scrape_reviews(
        self, 
        imdb_id: str, 
        max_reviews: int = 50
    ) -> List[Dict]:
        """
        Scrape reviews for a movie.
        
        Args:
            imdb_id: IMDb ID (e.g., 'tt1375666')
            max_reviews: Maximum number of reviews to scrape
        
        Returns:
            List of review dictionaries
        """
        reviews = []
        
        try:
            # IMDb reviews URL
            reviews_url = f"{self.BASE_URL}/title/{imdb_id}/reviews"
            
            # Pagination key for loading more reviews
            pagination_key = None
            
            while len(reviews) < max_reviews:
                # Build URL with pagination
                if pagination_key:
                    url = f"{reviews_url}/_ajax?paginationKey={pagination_key}"
                else:
                    url = reviews_url
                
                time.sleep(self.rate_limit)
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find review containers
                review_containers = soup.find_all('div', class_='review-container')
                
                if not review_containers:
                    logger.info(f"No more reviews found for {imdb_id}")
                    break
                
                for container in review_containers:
                    if len(reviews) >= max_reviews:
                        break
                    
                    try:
                        review = self._parse_review(container, imdb_id)
                        if review:
                            reviews.append(review)
                    except Exception as e:
                        logger.error(f"Error parsing review: {e}")
                        continue
                
                # Find pagination key for next page
                load_more = soup.find('div', class_='load-more-data')
                if load_more and 'data-key' in load_more.attrs:
                    pagination_key = load_more['data-key']
                else:
                    break  # No more pages
            
            logger.info(f"Scraped {len(reviews)} reviews from IMDb for {imdb_id}")
            return reviews
            
        except Exception as e:
            logger.error(f"Error scraping reviews for {imdb_id}: {e}")
            return reviews
    
    def _parse_review(self, container, imdb_id: str) -> Optional[Dict]:
        """
        Parse a single review container.
        
        Args:
            container: BeautifulSoup review container
            imdb_id: IMDb ID
        
        Returns:
            Review dictionary or None
        """
        try:
            # Review ID
            review_id = container.get('data-review-id')
            
            # Title
            title_elem = container.find('a', class_='title')
            title = title_elem.text.strip() if title_elem else None
            
            # Text content
            content_elem = container.find('div', class_='text show-more__control')
            if not content_elem:
                content_elem = container.find('div', class_='content')
            text = content_elem.text.strip() if content_elem else None
            
            if not text or len(text) < 20:
                return None  # Skip very short reviews
            
            # Rating
            rating = None
            rating_elem = container.find('span', class_='rating-other-user-rating')
            if rating_elem:
                rating_text = rating_elem.find('span')
                if rating_text:
                    try:
                        rating = float(rating_text.text.strip()) 
                    except:
                        pass
            
            # Author
            author = None
            author_elem = container.find('span', class_='display-name-link')
            if author_elem:
                author = author_elem.text.strip()
            
            # Date
            review_date = None
            date_elem = container.find('span', class_='review-date')
            if date_elem:
                date_str = date_elem.text.strip()
                try:
                    review_date = datetime.strptime(date_str, '%d %B %Y')
                except:
                    pass
            
            # Helpful votes
            helpful_count = 0
            helpful_elem = container.find('div', class_='actions text-muted')
            if helpful_elem:
                helpful_text = helpful_elem.text
                match = re.search(r'(\d+)\s+out of', helpful_text)
                if match:
                    helpful_count = int(match.group(1))
            
            return {
                'source': 'imdb',
                'source_id': f"imdb_{review_id}",
                'imdb_id': imdb_id,
                'title': title,
                'text': text,
                'rating': rating,
                'author': author,
                'review_date': review_date,
                'helpful_count': helpful_count,
                'review_length': len(text),
                'word_count': len(text.split()),
                'scraped_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error parsing review: {e}")
            return None
    
    def scrape_movie_rating(
        self,
        title: str,
        year: Optional[int] = None,
        imdb_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Scrape just the movie rating (not full reviews).
        
        Args:
            title: Movie title
            year: Release year
            imdb_id: IMDb ID (if known, skips search)
        
        Returns:
            Dictionary with rating info: {
                'rating': float,
                'vote_count': int,
                'imdb_id': str
            }
        """
        try:
            if not imdb_id:
                imdb_id = self.search_movie(title, year)
                if not imdb_id:
                    logger.warning(f"IMDb ID not found for '{title}' ({year})")
                    return None
            
            # Fetch movie page
            movie_url = f"{self.BASE_URL}/title/{imdb_id}/"
            time.sleep(self.rate_limit)
            
            response = self.session.get(movie_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find rating - IMDb uses structured JSON-LD data
            rating = None
            vote_count = None
            
            # Use JSON-LD structured data (most reliable)
            script_tags = soup.find_all('script', type='application/ld+json')
            for script in script_tags:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'aggregateRating' in data:
                        rating_data = data['aggregateRating']
                        rating = float(rating_data.get('ratingValue', 0))
                        vote_count = int(rating_data.get('ratingCount', 0))
                        break
                except:
                    continue
            
            if rating:
                logger.info(f"Scraped rating for {imdb_id}: {rating}/10 ({vote_count} votes)")
                return {
                    'rating': rating,
                    'vote_count': vote_count,
                    'imdb_id': imdb_id
                }
            else:
                logger.warning(f"Could not find rating for {imdb_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping rating for '{title}': {e}")
            return None
    
    def scrape_movie_reviews(
        self, 
        title: str, 
        year: Optional[int] = None,
        imdb_id: Optional[str] = None,
        max_reviews: int = 50
    ) -> List[Dict]:
        """
        Complete workflow: search + scrape reviews.
        
        Args:
            title: Movie title
            year: Release year
            imdb_id: IMDb ID (if known, skips search)
            max_reviews: Maximum reviews to scrape
        
        Returns:
            List of review dictionaries
        """
        if not imdb_id:
            imdb_id = self.search_movie(title, year)
            if not imdb_id:
                logger.warning(f"Cannot scrape reviews - IMDb ID not found for '{title}'")
                return []
        
        return self.scrape_reviews(imdb_id, max_reviews)


# Example usage
if __name__ == "__main__":
    scraper = IMDbScraper()
    
    # Test with a well-known movie
    reviews = scraper.scrape_movie_reviews(
        title="Inception",
        year=2010,
        max_reviews=10
    )
    
    print(f"Scraped {len(reviews)} reviews")
    if reviews:
        print("\nFirst review:")
        print(f"Title: {reviews[0]['title']}")
        print(f"Rating: {reviews[0]['rating']}")
        print(f"Text: {reviews[0]['text'][:200]}...")
