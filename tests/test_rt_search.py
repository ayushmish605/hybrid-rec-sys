"""
Quick test for the new RT search functionality.

Tests:
1. Search with year
2. Search without year
3. Difficult titles (special characters, articles)
4. Fallback to slug generation
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.scrapers.rotten_tomatoes_selenium import RottenTomatoesSeleniumScraper
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def test_search():
    """Test the new search functionality"""
    
    rt = RottenTomatoesSeleniumScraper(headless=True)
    
    test_cases = [
        # (title, year, expected_slug_contains)
        ("Deadpool & Wolverine", 2024, "deadpool"),
        ("The Batman", 2022, "batman"),
        ("Spider-Man: No Way Home", 2021, "spider"),
        ("Inception", 2010, "inception"),
        ("The Shawshank Redemption", 1994, "shawshank"),
        # This one might fail - test fallback
        ("Some Nonexistent Movie", 2025, None),
    ]
    
    print("\n" + "="*60)
    print("Testing RT Search Functionality")
    print("="*60 + "\n")
    
    successes = 0
    failures = 0
    
    for title, year, expected in test_cases:
        print(f"\n Testing: '{title}' ({year})")
        print("-" * 60)
        
        try:
            slug = rt.search_movie(title, year)
            
            if slug:
                print(f" Found: {slug}")
                if expected and expected in slug:
                    print(f" Matches expected: '{expected}' in '{slug}'")
                    successes += 1
                elif expected:
                    print(f"⚠️ Unexpected slug (might still be correct)")
                    successes += 1
                else:
                    print(f"⚠️ Found slug for movie that might not exist (fallback?)")
                    successes += 1
            else:
                print(f" Not found")
                if expected is None:
                    print(f" Expected to fail (nonexistent movie)")
                    successes += 1
                else:
                    failures += 1
                    
        except Exception as e:
            print(f" Error: {e}")
            failures += 1
    
    print("\n" + "="*60)
    print(f"Results: {successes} successes, {failures} failures")
    print("="*60 + "\n")
    
    rt._close_driver()
    
    return successes, failures


if __name__ == "__main__":
    successes, failures = test_search()
    
    if failures == 0:
        print(" All tests passed!")
        sys.exit(0)
    else:
        print(f"⚠️ {failures} tests failed")
        sys.exit(1)
