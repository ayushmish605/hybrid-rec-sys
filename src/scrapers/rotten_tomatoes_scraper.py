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
        Scrape reviews for a movie from all available RT endpoints.
        
        NOTE: RT only loads most recent reviews via static HTML (no pagination without JavaScript).
        This scraper gets what's available from:
        - /reviews/all-critics
        - /reviews/top-critics  
        - /reviews/all-audience
        - /reviews/verified-audience
        
        Deduplication happens based on review text hash.
        Top critic reviews take priority over all-critic reviews.
        Verified audience reviews take priority over all-audience reviews.
        
        Args:
            movie_slug: RT movie slug (e.g., 'zootopia_2')
            max_reviews: Maximum number of reviews per endpoint (total may be higher)
            review_type: Type of reviews to scrape
        
        Returns:
            List of deduplicated review dictionaries with appropriate priorities
        """
        all_reviews = []
        seen_hashes = set()  # Track review text hashes for deduplication
        
        # Scrape all 4 endpoints in priority order
        # Priority: top-critics > all-critics, verified-audience > all-audience
        
        if review_type in ['critic', 'both']:
            # 1. Top Critics first (highest priority)
            top_critic_reviews = self._scrape_endpoint(
                movie_slug, 
                'top-critics', 
                max_reviews,
                is_critic=True,
                is_top=True
            )
            for review in top_critic_reviews:
                text_hash = hash(review['text'])
                if text_hash not in seen_hashes:
                    seen_hashes.add(text_hash)
                    all_reviews.append(review)
            
            # 2. All Critics (may contain duplicates with top-critics)
            all_critic_reviews = self._scrape_endpoint(
                movie_slug,
                'all-critics',
                max_reviews,
                is_critic=True,
                is_top=False
            )
            for review in all_critic_reviews:
                text_hash = hash(review['text'])
                if text_hash not in seen_hashes:
                    seen_hashes.add(text_hash)
                    all_reviews.append(review)
        
        if review_type in ['audience', 'both']:
            # 3. Verified Audience first (highest priority)
            verified_reviews = self._scrape_endpoint(
                movie_slug,
                'verified-audience',
                max_reviews,
                is_critic=False,
                is_verified=True
            )
            for review in verified_reviews:
                text_hash = hash(review['text'])
                if text_hash not in seen_hashes:
                    seen_hashes.add(text_hash)
                    all_reviews.append(review)
            
            # 4. All Audience (may contain duplicates with verified)
            all_audience_reviews = self._scrape_endpoint(
                movie_slug,
                'all-audience',
                max_reviews,
                is_critic=False,
                is_verified=False
            )
            for review in all_audience_reviews:
                text_hash = hash(review['text'])
                if text_hash not in seen_hashes:
                    seen_hashes.add(text_hash)
                    all_reviews.append(review)
        
        logger.info(f"Scraped {len(all_reviews)} deduplicated reviews from RT for {movie_slug}")
        return all_reviews
    
    def _scrape_endpoint(
        self,
        movie_slug: str,
        endpoint: str,
        max_reviews: int,
        is_critic: bool,
        is_top: bool = False,
        is_verified: bool = False
    ) -> List[Dict]:
        """
        Scrape a specific RT review endpoint.
        
        Args:
            movie_slug: RT movie slug
            endpoint: One of 'all-critics', 'top-critics', 'all-audience', 'verified-audience'
            max_reviews: Max reviews to scrape
            is_critic: True for critic reviews, False for audience
            is_top: True if this is top-critics endpoint
            is_verified: True if this is verified-audience endpoint
        
        Returns:
            List of review dictionaries
        """
        reviews = []
        
        try:
            url = f"{self.BASE_URL}/m/{movie_slug}/reviews/{endpoint}"
            logger.info(f"Scraping RT endpoint: {url}")
            
            time.sleep(self.rate_limit)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find <review-card> elements (new RT structure)
            review_cards = soup.find_all('review-card')
            
            if not review_cards:
                logger.warning(f"No <review-card> elements found for {endpoint}")
                return reviews
            
            logger.info(f"Found {len(review_cards)} review cards on {endpoint}")
            
            for card in review_cards[:max_reviews]:
                try:
                    review = self._parse_review_card(
                        card,
                        movie_slug,
                        is_critic=is_critic,
                        is_top=is_top,
                        is_verified=is_verified
                    )
                    if review:
                        reviews.append(review)
                except Exception as e:
                    logger.error(f"Error parsing review card: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(reviews)} reviews from {endpoint}")
            return reviews
            
        except Exception as e:
            logger.error(f"Error scraping {endpoint} for {movie_slug}: {e}")
            return reviews
    
    def _parse_review_card(
        self,
        card,
        movie_slug: str,
        is_critic: bool,
        is_top: bool = False,
        is_verified: bool = False
    ) -> Optional[Dict]:
        """
        Parse a <review-card> element (new RT structure).
        
        Example structure:
        <review-card approved-critic="false" approved-publication="true" 
                     top-critic="false" top-publication="false" verified-review="false">
            ...review content in slots...
        </review-card>
        
        Args:
            card: BeautifulSoup review-card element
            movie_slug: RT movie slug
            is_critic: True for critic review
            is_top: True if from top-critics endpoint
            is_verified: True if from verified-audience endpoint
        
        Returns:
            Review dictionary or None
        """
        try:
            # Check card attributes for additional priority metadata
            card_attrs = card.attrs if hasattr(card, 'attrs') else {}
            top_critic_attr = card_attrs.get('top-critic') == 'true'
            verified_attr = card_attrs.get('verified-review') == 'true'
            
            # Review text (in drawer-more slot or review slot)
            text_elem = card.find('drawer-more', attrs={'slot': 'review'})
            if text_elem:
                content_span = text_elem.find('span', attrs={'slot': 'content'})
                text = content_span.get_text(strip=True) if content_span else text_elem.get_text(strip=True)
            else:
                # Fallback: look for any text content
                text_elem = card.find(attrs={'slot': 'review'})
                text = text_elem.get_text(strip=True) if text_elem else None
            
            if not text or len(text) < 20:
                return None
            
            # Author (in name slot)
            author_elem = card.find('rt-link', attrs={'slot': 'name'})
            author = author_elem.get_text(strip=True) if author_elem else None
            
            # Publication (in publication slot) - for critic reviews
            publication = None
            if is_critic:
                pub_elem = card.find('rt-link', attrs={'slot': 'publication'})
                publication = pub_elem.get_text(strip=True) if pub_elem else None
            
            # Timestamp (in timestamp slot)
            time_elem = card.find('span', attrs={'slot': 'timestamp'})
            timestamp_str = time_elem.get_text(strip=True) if time_elem else None
            
            # Parse timestamp (e.g., "1d", "2w", "3mo")
            review_date = self._parse_relative_timestamp(timestamp_str)
            
            # Sentiment (in rating slot - look for score-icon-critics or score-icon-audience)
            sentiment = None
            rating_slot = card.find(attrs={'slot': 'rating'})
            if rating_slot:
                score_icon = rating_slot.find(['score-icon-critics', 'score-icon-audience'])
                if score_icon:
                    sentiment = score_icon.get('sentiment')  # 'positive' or 'negative'
            
            # Convert sentiment to numeric rating
            # For critics: positive=1.0 (fresh), negative=0.0 (rotten)
            # For audience: we could use star ratings if available, but typically just fresh/rotten
            rating = None
            if sentiment == 'positive':
                rating = 1.0
            elif sentiment == 'negative':
                rating = 0.0
            
            # Determine review priority for weighting during sentiment analysis
            # Priority levels: top_critic > verified_audience > regular_critic > regular_audience
            priority_level = 'regular'
            if is_critic:
                if is_top or top_critic_attr:
                    priority_level = 'top_critic'
                else:
                    priority_level = 'critic'
            else:
                if is_verified or verified_attr:
                    priority_level = 'verified_audience'
                else:
                    priority_level = 'audience'
            
            # Create unique source_id
            source_id = f"rt_{priority_level}_{movie_slug}_{hash(text)}"
            
            review_data = {
                'source_id': source_id,
                'text': text,
                'rating': rating,
                'title': None,  # RT review cards don't have separate titles
                'author': author,
                'review_date': review_date,
                'review_length': len(text),
                'word_count': len(text.split()),
                # Additional metadata for prioritization during sentiment analysis
                'review_type': priority_level,  # Store priority level
                'publication': publication,  # For critic reviews
                'sentiment': sentiment  # 'positive' or 'negative'
            }
            
            return review_data
            
        except Exception as e:
            logger.error(f"Error parsing review card: {e}")
            return None
    
    def _parse_relative_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """
        Parse relative timestamps like '1d', '2w', '3mo' into datetime.
        
        Args:
            timestamp_str: Relative timestamp string
        
        Returns:
            Estimated datetime or None
        """
        if not timestamp_str:
            return None
        
        try:
            import re
            from datetime import timedelta
            
            # Match pattern like "1d", "2w", "3mo", "1y"
            match = re.match(r'(\d+)([dwmoy])', timestamp_str.lower())
            if not match:
                return None
            
            amount = int(match.group(1))
            unit = match.group(2)
            
            now = datetime.now()
            
            if unit == 'd':  # days
                return now - timedelta(days=amount)
            elif unit == 'w':  # weeks
                return now - timedelta(weeks=amount)
            elif unit == 'm':  # months (approximate as 30 days)
                return now - timedelta(days=amount * 30)
            elif unit == 'o':  # "mo" = months
                return now - timedelta(days=amount * 30)
            elif unit == 'y':  # years (approximate as 365 days)
                return now - timedelta(days=amount * 365)
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing timestamp '{timestamp_str}': {e}")
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
            max_reviews: Maximum reviews per endpoint
        
        Returns:
            List of deduplicated review dictionaries with priority metadata
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
    
    # Test with Zootopia 2
    reviews = scraper.scrape_movie_reviews(
        title="Zootopia 2",
        year=2025,
        max_reviews=20
    )
    
    print(f"\n{'='*80}")
    print(f"Scraped {len(reviews)} total reviews from RT")
    print(f"{'='*80}\n")
    
    if reviews:
        # Count by priority
        priority_counts = {}
        for review in reviews:
            priority = review.get('review_type', 'unknown')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        print("Reviews by priority level:")
        for priority, count in priority_counts.items():
            print(f"   {priority}: {count}")
        
        print("\n" + "="*80)
        print("Sample reviews:")
        print("="*80)
        
        # Show one of each type
        for priority in ['top_critic', 'critic', 'verified_audience', 'audience']:
            sample = next((r for r in reviews if r.get('review_type') == priority), None)
            if sample:
                print(f"\n[{priority.upper()}]")
                print(f"Author: {sample['author']}")
                if sample.get('publication'):
                    print(f"Publication: {sample['publication']}")
                print(f"Sentiment: {sample.get('sentiment', 'N/A')}")
                print(f"Text: {sample['text'][:150]}...")
                print()
