"""
Diagnose RT search issues by manually checking what search results look like.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def diagnose_search(title, year):
    """Diagnose what's happening with RT search for a specific movie"""
    
    print(f"\n{'='*70}")
    print(f"Diagnosing: '{title}' ({year})")
    print(f"{'='*70}\n")
    
    # Set up headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to search
        search_url = f"https://www.rottentomatoes.com/search?search={title}"
        print(f"1. Navigating to: {search_url}")
        driver.get(search_url)
        
        # Wait a bit for page to load
        time.sleep(3)
        
        # Check page title
        print(f"2. Page title: {driver.title}")
        print(f"3. Current URL: {driver.current_url}")
        
        # Try to find search results
        print(f"\n4. Looking for search results...")
        
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "search-page-media-row")))
            
            results = driver.find_elements(By.TAG_NAME, "search-page-media-row")
            print(f"   Found {len(results)} search-page-media-row elements")
            
            if results:
                print(f"\n5. Analyzing first {min(5, len(results))} results:")
                for i, result in enumerate(results[:5], 1):
                    try:
                        # Get title
                        link = result.find_element(By.CSS_SELECTOR, 'a[data-qa="info-name"]')
                        result_title = link.text.strip()
                        result_url = link.get_attribute('href')
                        
                        # Get year
                        result_year = result.get_attribute('startyear')
                        
                        print(f"\n   Result {i}:")
                        print(f"      Title: {result_title}")
                        print(f"      Year: {result_year}")
                        print(f"      URL: {result_url}")
                        print(f"      Type: {'TV' if '/tv/' in result_url else 'Movie'}")
                        
                        # Check if it would match
                        if '/tv/' not in result_url:
                            if result_title.lower() == title.lower():
                                print(f"       EXACT MATCH!")
                            elif title.lower() in result_title.lower() or result_title.lower() in title.lower():
                                print(f"      ⚠️ Partial match")
                            else:
                                print(f"       No match")
                            
                            if result_year and str(year):
                                if abs(int(result_year) - year) <= 1:
                                    print(f"       Year matches (within ±1)")
                                else:
                                    print(f"       Year mismatch ({result_year} vs {year})")
                        
                    except Exception as e:
                        print(f"   Result {i}: Error - {e}")
            
        except Exception as e:
            print(f"    Could not find search results: {e}")
            
            # Try to get page source to see what's there
            print(f"\n   Checking page source...")
            page_source = driver.page_source
            
            if "search-page-media-row" in page_source:
                print(f"   ⚠️ search-page-media-row IS in page source but not loaded yet")
            else:
                print(f"    search-page-media-row NOT in page source at all")
            
            if "no results" in page_source.lower() or "couldn't find" in page_source.lower():
                print(f"    Page says 'no results'")
        
    finally:
        driver.quit()


if __name__ == "__main__":
    # Test a few problematic movies
    test_cases = [
        ("Once Upon a Time... in Hollywood", 2019),
        ("Space Sweepers", 2021),
        ("The Ritual", 2017),
    ]
    
    for title, year in test_cases:
        diagnose_search(title, year)
        print("\n" + "="*70 + "\n")
