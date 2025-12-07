"""
Rotten Tomatoes scraper for critic and audience reviews.
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
import sys
from pathlib import Path
import urllib.parse

sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RottenTomatoesScraper:
    """Scrape reviews from Rotten Tomatoes"""
    
    BASE_URL = "https://www.rottentomatoes.com"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    def __init__(self, rate_limit: float = 2.0):
        """
        Initialize Rotten Tomatoes scraper.
        
        Args:
            rate_limit: Seconds between requests
        """
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def search_movie(self, title: str, year: Optional[int] = None) -> Optional[str]:
        """
        Search for a movie and return its RT URL slug.
        
        Args:
            title: Movie title
            year: Release year
        
        Returns:
            RT movie slug (e.g., 'inception_2010') or None
        """
        try:
            search_query = title
            if year:
                search_query += f" {year}"
            
            search_url = f"{self.BASE_URL}/search"
            params = {'search': search_query}
            
            time.sleep(self.rate_limit)
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find movie results
            # RT search results have evolved, try multiple selectors
            results = soup.find_all('search-page-media-row')
            
            if not results:
                # Try alternative structure
                results = soup.find_all('a', attrs={'data-qa': 'info-name'})
            
            for result in results:
                try:
                    link = result.get('href') or result.find('a').get('href')
                    if link and '/m/' in link:
                        # Extract slug from URL
                        slug = link.split('/m/')[-1].split('/')[0]
                        logger.info(f"Found RT slug for '{title}': {slug}")
                        return slug
                except:
                    continue
            
            # Fallback: try constructing slug from title
            slug = self._construct_slug(title, year)
            logger.info(f"Using constructed slug for '{title}': {slug}")
            return slug
            
        except Exception as e:
            logger.error(f"Error searching RT for '{title}': {e}")
            # Return constructed slug as fallback
            return self._construct_slug(title, year)
    
    def _construct_slug(self, title: str, year: Optional[int] = None) -> str:
        """
        Construct a RT URL slug from title and year.
        
        Args:
            title: Movie title
            year: Release year
        
        Returns:
            Constructed slug
        """
        # Clean and format title
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars
        slug = re.sub(r'[\s_]+', '_', slug)   # Replace spaces with underscores
        slug = slug.strip('_')
        
        if year:
            slug += f"_{year}"
        
        return slug
    
    def scrape_reviews(
        self,
        movie_slug: str,
        max_reviews: int = 40,
        review_type: str = 'both'  # 'audience', 'critic', or 'both'
    ) -> List[Dict]:
        """
        Scrape reviews for a movie.
        
        Args:
            movie_slug: RT movie slug
            max_reviews: Maximum number of reviews
            review_type: Type of reviews to scrape
        
        Returns:
            List of review dictionaries
        """
        all_reviews = []
        
        if review_type in ['audience', 'both']:
            audience_reviews = self._scrape_audience_reviews(movie_slug, max_reviews // 2 if review_type == 'both' else max_reviews)
            all_reviews.extend(audience_reviews)
        
        if review_type in ['critic', 'both']:
            critic_reviews = self._scrape_critic_reviews(movie_slug, max_reviews // 2 if review_type == 'both' else max_reviews)
            all_reviews.extend(critic_reviews)
        
        logger.info(f"Scraped {len(all_reviews)} reviews from RT for {movie_slug}")
        return all_reviews
    
    def _scrape_audience_reviews(self, movie_slug: str, max_reviews: int) -> List[Dict]:
        """Scrape audience reviews"""
        reviews = []
        
        try:
            url = f"{self.BASE_URL}/m/{movie_slug}/reviews?type=user"
            
            time.sleep(self.rate_limit)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find review containers
            review_elements = soup.find_all('div', class_='review-row')
            
            for elem in review_elements[:max_reviews]:
                try:
                    review = self._parse_audience_review(elem, movie_slug)
                    if review:
                        reviews.append(review)
                except Exception as e:
                    logger.error(f"Error parsing audience review: {e}")
                    continue
            
            return reviews
            
        except Exception as e:
            logger.error(f"Error scraping audience reviews for {movie_slug}: {e}")
            return reviews
    
    def _scrape_critic_reviews(self, movie_slug: str, max_reviews: int) -> List[Dict]:
        """Scrape critic reviews"""
        reviews = []
        
        try:
            url = f"{self.BASE_URL}/m/{movie_slug}/reviews?type=top_critics"
            
            time.sleep(self.rate_limit)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find review containers
            review_elements = soup.find_all('div', class_='review-row')
            
            for elem in review_elements[:max_reviews]:
                try:
                    review = self._parse_critic_review(elem, movie_slug)
                    if review:
                        reviews.append(review)
                except Exception as e:
                    logger.error(f"Error parsing critic review: {e}")
                    continue
            
            return reviews
            
        except Exception as e:
            logger.error(f"Error scraping critic reviews for {movie_slug}: {e}")
            return reviews
    
    def _parse_audience_review(self, elem, movie_slug: str) -> Optional[Dict]:
        """Parse audience review element"""
        try:
            # Review text
            text_elem = elem.find('p', class_='review-text')
            if not text_elem:
                return None
            text = text_elem.text.strip()
            
            if len(text) < 20:
                return None
            
            # Rating (fresh/rotten)
            rating_elem = elem.find('span', class_='star-display')
            rating = None
            if rating_elem:
                # Extract rating from class or text
                classes = rating_elem.get('class', [])
                if 'star-display--rated' in ' '.join(classes):
                    # Try to extract numeric rating
                    match = re.search(r'(\d+\.?\d*)', str(rating_elem))
                    if match:
                        rating = float(match.group(1))
            
            # Author
            author_elem = elem.find('a', class_='display-name')
            author = author_elem.text.strip() if author_elem else None
            
            # Date
            date_elem = elem.find('span', class_='review-date')
            review_date = None
            if date_elem:
                date_str = date_elem.text.strip()
                try:
                    review_date = datetime.strptime(date_str, '%b %d, %Y')
                except:
                    pass
            
            return {
                'source': 'rotten_tomatoes',
                'source_id': f"rt_audience_{movie_slug}_{hash(text)}",
                'movie_slug': movie_slug,
                'text': text,
                'rating': rating,
                'author': author,
                'review_type': 'audience',
                'review_date': review_date,
                'review_length': len(text),
                'word_count': len(text.split()),
                'scraped_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error parsing audience review: {e}")
            return None
    
    def _parse_critic_review(self, elem, movie_slug: str) -> Optional[Dict]:
        """Parse critic review element"""
        try:
            # Review text
            text_elem = elem.find('p', class_='review-text')
            if not text_elem:
                return None
            text = text_elem.text.strip()
            
            if len(text) < 20:
                return None
            
            # Fresh/Rotten score
            score_elem = elem.find('span', class_='icon')
            fresh = 'fresh' in str(score_elem) if score_elem else None
            rating = 1.0 if fresh else 0.0 if fresh is not None else None
            
            # Author and publication
            author_elem = elem.find('a', class_='display-name')
            author = author_elem.text.strip() if author_elem else None
            
            # Date
            date_elem = elem.find('span', class_='review-date')
            review_date = None
            if date_elem:
                date_str = date_elem.text.strip()
                try:
                    review_date = datetime.strptime(date_str, '%b %d, %Y')
                except:
                    pass
            
            return {
                'source': 'rotten_tomatoes',
                'source_id': f"rt_critic_{movie_slug}_{hash(text)}",
                'movie_slug': movie_slug,
                'text': text,
                'rating': rating,
                'author': author,
                'review_type': 'critic',
                'review_date': review_date,
                'review_length': len(text),
                'word_count': len(text.split()),
                'scraped_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error parsing critic review: {e}")
            return None
    
    def scrape_movie_reviews(
        self,
        title: str,
        year: Optional[int] = None,
        movie_slug: Optional[str] = None,
        max_reviews: int = 40
    ) -> List[Dict]:
        """
        Complete workflow: search + scrape reviews.
        
        Args:
            title: Movie title
            year: Release year
            movie_slug: RT slug (if known)
            max_reviews: Maximum reviews
        
        Returns:
            List of review dictionaries
        """
        if not movie_slug:
            movie_slug = self.search_movie(title, year)
            if not movie_slug:
                logger.warning(f"Cannot scrape reviews - RT slug not found for '{title}'")
                return []
        
        return self.scrape_reviews(movie_slug, max_reviews)


# Example usage
if __name__ == "__main__":
    scraper = RottenTomatoesScraper()
    
    reviews = scraper.scrape_movie_reviews(
        title="Inception",
        year=2010,
        max_reviews=10
    )
    
    print(f"Scraped {len(reviews)} reviews")
    if reviews:
        print("\nFirst review:")
        print(f"Type: {reviews[0]['review_type']}")
        print(f"Author: {reviews[0]['author']}")
        print(f"Text: {reviews[0]['text'][:200]}...")
