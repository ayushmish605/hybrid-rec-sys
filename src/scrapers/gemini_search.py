"""
OpenAI API integration for generating search terms and hashtags for movies.
"""

from openai import OpenAI
import yaml
import json
from pathlib import Path
from typing import List, Dict, Optional
import sys
import os
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)


class GeminiSearchTermGenerator:
    """Generate optimized search terms for scraping using OpenAI API"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (if None, loads from .env or config)
        """
        if api_key is None:
            api_key = self._load_api_key()
        
        self.client = OpenAI(api_key=api_key)
        # Use GPT-4o-mini for cost-effective search term generation
        self.model = "gpt-4o-mini"
        logger.info("OpenAI API initialized successfully")
    
    def _load_api_key(self) -> str:
        """Load API key from .env file or config file"""
        # First try loading from .env file
        env_path = Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                logger.info("Loaded OpenAI API key from .env file")
                return api_key
        
        # Fall back to config file
        config_path = Path(__file__).parent.parent.parent / 'config' / 'api_keys.yaml'
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                api_key = config.get('openai', {}).get('api_key')
                if api_key:
                    logger.info("Loaded OpenAI API key from config file")
                    return api_key
        except Exception as e:
            logger.warning(f"Could not load from config: {e}")
        
        raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env file or config/api_keys.yaml")
    
    def generate_search_terms(
        self, 
        title: str, 
        year: int = None, 
        genres: List[str] = None,
        overview: str = None
    ) -> Optional[Dict[str, List[str]]]:
        """
        Generate search terms for a movie using OpenAI.
        
        Args:
            title: Movie title
            year: Release year
            genres: List of genres
            overview: Movie plot/overview
        
        Returns:
            Dictionary with search terms categorized by platform, or None if generation fails:
            {
                'reddit': [...],
                'twitter': [...],
                'imdb': [...],
                'general': [...]
            }
        """
        try:
            # Build context for OpenAI
            context = f"Movie: {title}"
            if year:
                context += f" ({year})"
            if genres:
                context += f"\nGenres: {', '.join(genres)}"
            if overview:
                context += f"\nPlot: {overview[:200]}"  # Limit length
            
            # Create prompt with strict JSON format requirement
            prompt = f"""You are a search optimization expert. Generate optimal search terms for finding movie discussions and reviews.

Movie Information:
{context}

Generate search terms in these EXACT categories. Return ONLY valid JSON, no markdown, no explanations.

Return a JSON object with this EXACT structure:
{{
  "reddit": ["term1", "term2", "term3", "term4", "term5"],
  "twitter": ["#Term1", "#Term2", "#Term3", "#Term4", "#Term5"],
  "imdb": ["term with year", "term variation", "term"],
  "general": ["term1", "term2", "term3", "term4", "term5"]
}}

Guidelines:
- REDDIT: Discussion-style phrases, include title variations
- TWITTER: Hashtags with # symbol, no spaces in hashtags
- IMDB: Official title with year, title variations
- GENERAL: Universal search terms, abbreviations, genre+title

Return pure JSON only. No markdown code blocks. No explanations. Just the JSON object."""
            
            # Call OpenAI API with JSON mode
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates search terms for movies. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=500
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            try:
                search_terms = json.loads(response_text)
                
                # Validate structure
                required_keys = ['reddit', 'twitter', 'imdb', 'general']
                if not all(key in search_terms for key in required_keys):
                    logger.error(f"Missing required keys in response for '{title}'")
                    return None
                
                # Ensure all values are lists
                for key in required_keys:
                    if not isinstance(search_terms[key], list):
                        logger.error(f"Invalid value type for key '{key}' in response for '{title}'")
                        return None
                
                logger.info(f"Generated search terms for '{title}'")
                return search_terms
                
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parse error for '{title}': {json_err}")
                return None
            
        except Exception as e:
            logger.error(f"Error generating search terms for '{title}': {e}")
            return None
    
    def batch_generate_search_terms(
        self, 
        movies: List[Dict]
    ) -> Dict[int, Dict[str, List[str]]]:
        """
        Generate search terms for multiple movies.
        
        Args:
            movies: List of movie dictionaries with keys: id, title, year, genres, overview
        
        Returns:
            Dictionary mapping movie_id to search terms
        """
        results = {}
        
        for movie in movies:
            movie_id = movie.get('id')
            title = movie.get('title')
            year = movie.get('year')
            genres = movie.get('genres', [])
            overview = movie.get('overview')
            
            try:
                search_terms = self.generate_search_terms(title, year, genres, overview)
                results[movie_id] = search_terms
            except Exception as e:
                logger.error(f"Failed to generate search terms for movie {movie_id}: {e}")
                continue
        
        return results


# Example usage
if __name__ == "__main__":
    # Test the generator
    generator = GeminiSearchTermGenerator()
    
    test_movie = {
        'title': 'The Dark Knight',
        'year': 2008,
        'genres': ['Action', 'Crime', 'Drama'],
        'overview': 'Batman raises the stakes in his war on crime...'
    }
    
    terms = generator.generate_search_terms(
        test_movie['title'],
        test_movie['year'],
        test_movie['genres'],
        test_movie['overview']
    )
    
    print(json.dumps(terms, indent=2))
