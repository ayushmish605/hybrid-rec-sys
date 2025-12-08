"""
Test RT search for the specific movies in the database to identify issues.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.scrapers.rotten_tomatoes_selenium import RottenTomatoesSeleniumScraper
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def test_specific_movies():
    """Test search for the actual movies in the database"""
    
    rt = RottenTomatoesSeleniumScraper(headless=True)
    
    # Movies from the database
    test_movies = [
        ("Annabelle Comes Home", 2019),
        ("Once Upon a Time... in Hollywood", 2019),
        ("Murder Mystery 2", 2023),
        ("Monster Hunter", 2020),
        ("The Ritual", 2017),
        ("Black Adam", 2022),
        ("Don't Worry Darling", 2022),
        ("Space Sweepers", 2021),
        ("Poor Things", 2023),
        ("Devotion", 2022),
    ]
    
    print("\n" + "="*70)
    print("Testing RT Search for Database Movies")
    print("="*70 + "\n")
    
    results = []
    
    for title, year in test_movies:
        print(f" Testing: '{title}' ({year})")
        print("-" * 70)
        
        try:
            # Test the search
            slug = rt.search_movie(title, year)
            
            if slug:
                print(f"    Found slug: {slug}")
                
                # Quick check if URL exists (try to load the page)
                rt._init_driver()
                test_url = f"{rt.BASE_URL}/m/{slug}"
                rt.driver.get(test_url)
                
                # Check for 404 or redirect
                current_url = rt.driver.current_url
                page_title = rt.driver.title
                
                if "page not found" in page_title.lower() or "404" in page_title.lower():
                    print(f"    URL returns 404: {test_url}")
                    print(f"      Page title: {page_title}")
                    results.append((title, year, slug, "404"))
                elif current_url != test_url:
                    print(f"   ⚠️ Redirected to: {current_url}")
                    results.append((title, year, slug, "redirect"))
                else:
                    print(f"    URL works: {test_url}")
                    results.append((title, year, slug, "success"))
            else:
                print(f"    No slug found")
                results.append((title, year, None, "not_found"))
                
        except Exception as e:
            print(f"    Error: {e}")
            results.append((title, year, None, f"error: {str(e)[:50]}"))
        
        print()
    
    rt._close_driver()
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    success = len([r for r in results if r[3] == "success"])
    redirect = len([r for r in results if r[3] == "redirect"])
    not_found = len([r for r in results if r[3] == "not_found"])
    four_oh_four = len([r for r in results if r[3] == "404"])
    errors = len([r for r in results if r[3].startswith("error")])
    
    print(f" Success: {success}/{len(test_movies)}")
    print(f"⚠️ Redirect: {redirect}/{len(test_movies)}")
    print(f" 404: {four_oh_four}/{len(test_movies)}")
    print(f" Not Found: {not_found}/{len(test_movies)}")
    print(f" Errors: {errors}/{len(test_movies)}")
    
    if four_oh_four + not_found > 0:
        print(f"\n FAILED MOVIES:")
        for title, year, slug, status in results:
            if status in ["404", "not_found"]:
                print(f"   • {title} ({year}) - {status}")
                if slug:
                    print(f"     Guessed slug: {slug}")
    
    print("\n" + "="*70)
    
    return results


if __name__ == "__main__":
    test_specific_movies()
