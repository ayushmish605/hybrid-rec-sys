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
                    # Verify year if provided
                    if year and not self._verify_movie_year(soup, result, year):
                        logger.info(f"Year mismatch for '{title}', trying next result...")
                    else:
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
            
            # Method 3: Find any link with /title/tt pattern and verify with year
            # Walk up DOM tree to find container with text to distinguish released vs in-development movies
            all_links = soup.find_all('a', href=re.compile(r'/title/tt\d+/'))
            
            for link in all_links[:10]:  # Check first 10 results
                href = link['href']
                match = re.search(r'/(tt\d+)/', href)
                if match:
                    imdb_id = match.group(1)
                    
                    # Walk up the DOM tree to find the container with text content
                    # Released movies have runtime/rating metadata; in-development movies don't
                    current = link
                    found_released_movie = False
                    
                    for level in range(10):
                        current = current.parent
                        if not current:
                            break
                        
                        text = current.get_text(strip=True)
                        if len(text) < 15:  # Skip empty levels
                            continue
                        
                        # Check for indicators of a released movie:
                        # - Runtime: "1h 31m" or "90m"
                        # - Rating: "5.3(27K)" or "Metascore"
                        has_runtime = re.search(r'\d+h\s*\d+m', text) or re.search(r'^\d+m', text)
                        has_rating = re.search(r'\d+\.\d+\(\d+K?\)', text) or 'Metascore' in text
                        
                        if has_runtime or has_rating:
                            # This is a released movie with actual content
                            found_released_movie = True
                            
                            # Verify year if provided
                            if year:
                                if any(str(y) in text for y in [year - 1, year, year + 1]):
                                    logger.info(f"Found released movie IMDb ID for '{title}' ({year}): {imdb_id}")
                                    return imdb_id
                                else:
                                    # Year mismatch, try next result
                                    break
                            else:
                                logger.info(f"Found released movie IMDb ID for '{title}': {imdb_id}")
                                return imdb_id
                        
                        elif len(text) < 50 and str(year) in text if year else len(text) < 30:
                            # Short text with no runtime/rating = in-development movie
                            # Skip this result and try the next one
                            logger.debug(f"Skipping in-development movie: {imdb_id}")
                            break
                    
                    # If we didn't find runtime/rating but also didn't identify as in-development,
                    # fall back to simple year check for backwards compatibility
                    if not found_released_movie and not year:
                        logger.info(f"Found IMDb ID for '{title}': {imdb_id}")
                        return imdb_id
            
            logger.warning(f"Could not find IMDb ID for '{title}' ({year})")
            logger.info(f"💡 Tip: If you know the IMDb ID, you can scrape directly using imdb_id parameter")
            return None
            
        except Exception as e:
            logger.error(f"Error searching IMDb for '{title}': {e}")
            return None
    
    def _verify_movie_year(self, soup, result_element, expected_year: int) -> bool:
        """Helper to verify if a search result matches the expected year"""
        try:
            # Look for year in the result's parent or siblings
            parent = result_element.parent
            if parent:
                text = parent.get_text()
                # Check if year appears in text (allow ±1 year for release date variations)
                if any(str(y) in text for y in [expected_year - 1, expected_year, expected_year + 1]):
                    return True
            return False
        except:
            return False
    
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
                
                # Try NEW IMDb structure first (2024+ layout)
                review_containers = soup.find_all('article', class_=lambda x: x and 'user-review' in str(x))
                
                # Fallback to OLD structure if new one doesn't exist
                if not review_containers:
                    review_containers = soup.find_all('div', class_='review-container')
                
                # Try alternative new structure (div with data-testid)
                if not review_containers:
                    review_containers = soup.find_all('div', attrs={'data-testid': lambda x: x and 'review' in str(x).lower()})
                
                if not review_containers:
                    logger.warning(f"No review containers found for {imdb_id}. IMDb may have changed structure.")
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
            # Review ID - try multiple attributes
            review_id = container.get('data-review-id') or container.get('data-testid', '').replace('review-', '')
            
            # Title - try multiple selectors (new and old)
            title_elem = container.find('a', class_='title')
            if not title_elem:
                title_elem = container.find('h3', class_=lambda x: x and 'ipc-title__text' in str(x))
            if not title_elem:
                # Look for h3 inside ipc-title wrapper
                title_wrapper = container.find('div', {'data-testid': 'review-summary'})
                if title_wrapper:
                    title_elem = title_wrapper.find('h3')
            if not title_elem:
                title_elem = container.find('span', class_=lambda x: x and 'title' in str(x).lower())
            
            # Extract title text and remove rating if present
            title = None
            if title_elem:
                title_text = title_elem.get_text(separator=' ', strip=True)
                # Remove rating pattern (e.g., "5/10" or "10/10") from title
                title_text = re.sub(r'^\d+/\d+\s*', '', title_text)
                title = title_text.strip() if title_text else None
            
            # Text content - try multiple selectors
            content_elem = container.find('div', class_='text show-more__control')
            if not content_elem:
                content_elem = container.find('div', class_='content')
            if not content_elem:
                # New structure - look for the spoiler button's parent
                spoiler_btn = container.find('button', class_=lambda x: x and 'review-spoiler-button' in str(x))
                if spoiler_btn:
                    # The review text is in the parent's previous sibling or nearby content
                    parent = spoiler_btn.parent
                    if parent:
                        # Try to find the content div
                        content_elem = parent.find('div', class_=lambda x: x and 'content' in str(x).lower())
            if not content_elem:
                # New structure - try finding by tag and content
                content_elem = container.find('div', class_=lambda x: x and ('text' in str(x).lower() or 'content' in str(x).lower()))
            if not content_elem:
                # Last resort - find any div with substantial text (but exclude buttons, titles, etc.)
                for div in container.find_all('div'):
                    # Skip if it contains buttons or is very short
                    if div.find('button') or div.find('a', class_='ipc-title-link-wrapper'):
                        continue
                    div_text = div.get_text(strip=True)
                    if div_text and len(div_text) > 50:
                        content_elem = div
                        break
            
            # Extract text with proper spacing
            text = None
            if content_elem:
                # Get text with spaces between elements
                text = content_elem.get_text(separator=' ', strip=True)
                # Remove "Spoiler" button text if present
                text = re.sub(r'\bSpoiler\b', '', text, flags=re.IGNORECASE)
                # Remove excessive whitespace
                text = re.sub(r'\s+', ' ', text).strip()
            
            if not text or len(text) < 20:
                return None  # Skip very short reviews
            
            # Remove rating from text if it appears at the beginning
            text = re.sub(r'^\d+/\d+\s*', '', text)
            
            # Rating - try multiple selectors
            rating = None
            rating_elem = container.find('span', class_='rating-other-user-rating')
            if not rating_elem:
                # New structure - look for aria-label with rating
                rating_elem = container.find('span', attrs={'aria-label': re.compile(r"rating:\s*\d+")})
            if not rating_elem:
                # Look for ipc-rating-star with rating class
                rating_elem = container.find('span', class_=lambda x: x and 'ipc-rating-star--rating' in str(x))
            
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                try:
                    # Extract just the number (e.g., "5" from "5/10")
                    rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                except:
                    pass
            
            # If still no rating, try finding in title or aria-label
            if not rating and title_elem:
                aria_label = title_elem.get('aria-label', '')
                rating_match = re.search(r'rating:\s*(\d+)', aria_label)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # Author - try multiple selectors
            author = None
            author_elem = container.find('span', class_='display-name-link')
            if not author_elem:
                author_elem = container.find('a', {'data-testid': 'author-link'})
            if not author_elem:
                author_elem = container.find('a', class_=lambda x: x and 'author' in str(x).lower())
            if not author_elem:
                # Look for username or author in href
                author_elem = container.find('a', href=lambda x: x and '/user/' in str(x))
            if author_elem:
                author = author_elem.get_text(strip=True)
            
            # Date
            review_date = None
            date_elem = container.find('span', class_='review-date')
            if not date_elem:
                # Try finding by class pattern
                date_elem = container.find('li', class_=lambda x: x and 'review-date' in str(x))
            if date_elem:
                date_str = date_elem.get_text(strip=True)
                try:
                    # Try multiple date formats
                    for date_format in ['%d %B %Y', '%B %d, %Y', '%b %d, %Y']:
                        try:
                            review_date = datetime.strptime(date_str, date_format)
                            break
                        except:
                            continue
                except:
                    pass
            
            # Helpful and Not Helpful votes (new IMDb structure)
            helpful_count = 0
            not_helpful_count = 0
            
            # Look for voting buttons with counts
            voting_section = container.find('div', class_=lambda x: x and 'ipc-voting' in str(x))
            if voting_section:
                # Find helpful count (thumbs up)
                helpful_label = voting_section.find('span', class_=lambda x: x and 'ipc-voting__label__count--up' in str(x))
                if helpful_label:
                    try:
                        helpful_count = int(helpful_label.get_text(strip=True))
                    except:
                        pass
                
                # Find not helpful count (thumbs down)
                not_helpful_label = voting_section.find('span', class_=lambda x: x and 'ipc-voting__label__count--down' in str(x))
                if not_helpful_label:
                    try:
                        not_helpful_count = int(not_helpful_label.get_text(strip=True))
                    except:
                        pass
            
            # Fallback: old structure
            if helpful_count == 0:
                helpful_elem = container.find('div', class_='actions text-muted')
                if helpful_elem:
                    helpful_text = helpful_elem.get_text()
                    match = re.search(r'(\d+)\s+out of\s+(\d+)', helpful_text)
                    if match:
                        helpful_count = int(match.group(1))
                        total = int(match.group(2))
                        not_helpful_count = total - helpful_count
            
            return {
                'source_id': f"imdb_{review_id}" if review_id else None,
                'text': text,
                'rating': rating,
                'title': title,
                'author': author,
                'review_date': review_date,
                'helpful_count': helpful_count,
                'not_helpful_count': not_helpful_count,
                'review_length': len(text),
                'word_count': len(text.split())
            }
            
        except Exception as e:
            logger.error(f"Error parsing review: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
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
