"""
Reddit scraper using PRAW (Python Reddit API Wrapper).
"""

import praw
import yaml
from datetime import datetime
from typing import List, Dict, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RedditScraper:
    """Scrape movie discussions and reviews from Reddit"""
    
    # Relevant movie subreddits
    MOVIE_SUBREDDITS = [
        'movies',
        'TrueFilm',
        'flicks',
        'MovieSuggestions',
        'moviecritic',
        'NetflixBestOf',
        'criterion',
        'horror',  # For horror movies
        'scifi',   # For sci-fi movies
        'boxoffice'
    ]
    
    def __init__(self, client_id: str = None, client_secret: str = None, user_agent: str = None):
        """
        Initialize Reddit scraper with PRAW.
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret  
            user_agent: User agent string
        """
        if not all([client_id, client_secret, user_agent]):
            client_id, client_secret, user_agent = self._load_credentials()
        
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            logger.info("Reddit API initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit API: {e}")
            raise
    
    def _load_credentials(self):
        """Load Reddit credentials from config"""
        config_path = Path(__file__).parent.parent.parent / 'config' / 'api_keys.yaml'
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                reddit_config = config['reddit']
                return (
                    reddit_config['client_id'],
                    reddit_config['client_secret'],
                    reddit_config['user_agent']
                )
        except Exception as e:
            logger.error(f"Error loading Reddit credentials: {e}")
            raise
    
    def search_movie_discussions(
        self,
        search_terms: List[str],
        subreddits: List[str] = None,
        limit: int = 30,
        time_filter: str = 'all'
    ) -> List[Dict]:
        """
        Search for movie discussions across subreddits.
        
        Args:
            search_terms: List of search queries
            subreddits: List of subreddits to search (default: MOVIE_SUBREDDITS)
            limit: Maximum results per search term per subreddit
            time_filter: Time filter ('all', 'year', 'month', 'week', 'day')
        
        Returns:
            List of discussion/review dictionaries
        """
        if subreddits is None:
            subreddits = self.MOVIE_SUBREDDITS
        
        all_posts = []
        seen_ids = set()
        
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                for term in search_terms:
                    try:
                        # Search subreddit
                        for submission in subreddit.search(
                            term, 
                            limit=limit, 
                            time_filter=time_filter,
                            sort='relevance'
                        ):
                            # Avoid duplicates
                            if submission.id in seen_ids:
                                continue
                            seen_ids.add(submission.id)
                            
                            # Parse submission
                            post_data = self._parse_submission(submission)
                            if post_data:
                                all_posts.append(post_data)
                                
                    except Exception as e:
                        logger.error(f"Error searching '{term}' in r/{subreddit_name}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error accessing r/{subreddit_name}: {e}")
                continue
        
        logger.info(f"Found {len(all_posts)} unique posts from Reddit")
        return all_posts
    
    def _parse_submission(self, submission) -> Optional[Dict]:
        """
        Parse a Reddit submission.
        
        Args:
            submission: PRAW Submission object
        
        Returns:
            Dictionary with submission data
        """
        try:
            # Combine title and selftext for full content
            text = submission.title
            if submission.selftext:
                text += "\n\n" + submission.selftext
            
            # Skip if too short
            if len(text) < 50:
                return None
            
            return {
                'source': 'reddit',
                'source_id': f"reddit_{submission.id}",
                'text': text,
                'title': submission.title,
                'author': str(submission.author) if submission.author else '[deleted]',
                'upvotes': submission.score,
                'downvotes': 0,  # Reddit doesn't provide exact downvotes
                'reply_count': submission.num_comments,
                'review_date': datetime.fromtimestamp(submission.created_utc),
                'subreddit': submission.subreddit.display_name,
                'url': f"https://reddit.com{submission.permalink}",
                'review_length': len(text),
                'word_count': len(text.split()),
                'scraped_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error parsing submission: {e}")
            return None
    
    def get_top_comments(
        self, 
        submission_id: str, 
        limit: int = 10
    ) -> List[Dict]:
        """
        Get top comments from a submission.
        
        Args:
            submission_id: Reddit submission ID
            limit: Number of top comments to retrieve
        
        Returns:
            List of comment dictionaries
        """
        try:
            submission = self.reddit.submission(id=submission_id)
            submission.comments.replace_more(limit=0)  # Remove "more comments" objects
            
            comments = []
            for comment in submission.comments.list()[:limit]:
                try:
                    if len(comment.body) < 30:  # Skip very short comments
                        continue
                    
                    comments.append({
                        'source': 'reddit',
                        'source_id': f"reddit_comment_{comment.id}",
                        'text': comment.body,
                        'author': str(comment.author) if comment.author else '[deleted]',
                        'upvotes': comment.score,
                        'review_date': datetime.fromtimestamp(comment.created_utc),
                        'parent_id': submission_id,
                        'review_length': len(comment.body),
                        'word_count': len(comment.body.split()),
                        'scraped_at': datetime.utcnow()
                    })
                except Exception as e:
                    logger.error(f"Error parsing comment: {e}")
                    continue
            
            return comments
            
        except Exception as e:
            logger.error(f"Error getting comments for {submission_id}: {e}")
            return []
    
    def scrape_movie_content(
        self,
        title: str,
        search_terms: List[str] = None,
        max_posts: int = 30,
        include_comments: bool = False
    ) -> List[Dict]:
        """
        Complete workflow to scrape content for a movie.
        
        Args:
            title: Movie title
            search_terms: Custom search terms (if None, uses basic terms)
            max_posts: Maximum posts to scrape
            include_comments: Whether to also scrape top comments
        
        Returns:
            List of posts and optionally comments
        """
        if search_terms is None:
            search_terms = [
                title,
                f"{title} review",
                f"{title} discussion",
                f"{title} movie"
            ]
        
        # Get posts
        posts = self.search_movie_discussions(
            search_terms=search_terms,
            limit=max(10, max_posts // len(search_terms))
        )
        
        # Optionally get comments from top posts
        if include_comments and posts:
            all_content = posts.copy()
            for post in posts[:5]:  # Get comments from top 5 posts
                submission_id = post['source_id'].replace('reddit_', '')
                comments = self.get_top_comments(submission_id, limit=5)
                all_content.extend(comments)
            return all_content
        
        return posts[:max_posts]


# Example usage
if __name__ == "__main__":
    scraper = RedditScraper()
    
    # Test search
    posts = scraper.scrape_movie_content(
        title="Inception",
        max_posts=10
    )
    
    print(f"Found {len(posts)} posts")
    if posts:
        print("\nFirst post:")
        print(f"Title: {posts[0].get('title', 'N/A')}")
        print(f"Upvotes: {posts[0]['upvotes']}")
        print(f"Text: {posts[0]['text'][:200]}...")
