"""
Test script to verify Gemini API key works.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from scrapers.gemini_search import GeminiSearchTermGenerator
import json


def test_gemini_api():
    """Test Gemini API with a sample movie"""
    
    print("=" * 60)
    print("Testing Gemini API Connection")
    print("=" * 60)
    
    try:
        # Initialize generator
        print("\n1. Initializing Gemini API...")
        generator = GeminiSearchTermGenerator()
        print("   ✅ Gemini API initialized successfully!")
        
        # Test with a well-known movie
        print("\n2. Testing with sample movie: Inception (2010)")
        test_movie = {
            'title': 'Inception',
            'year': 2010,
            'genres': ['Action', 'Sci-Fi', 'Thriller'],
            'overview': 'A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea.'
        }
        
        print("   Generating search terms...")
        search_terms = generator.generate_search_terms(
            title=test_movie['title'],
            year=test_movie['year'],
            genres=test_movie['genres'],
            overview=test_movie['overview']
        )
        
        print("\n   ✅ Search terms generated successfully!")
        
        # Display results
        print("\n3. Generated Search Terms:")
        print("-" * 60)
        
        for platform, terms in search_terms.items():
            print(f"\n   {platform.upper()}:")
            for term in terms:
                print(f"      • {term}")
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Gemini API is working correctly!")
        print("=" * 60)
        
        # Save results to file for reference
        output_file = Path(__file__).parent.parent / 'test_gemini_output.json'
        with open(output_file, 'w') as f:
            json.dump(search_terms, f, indent=2)
        
        print(f"\n📄 Results saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ ERROR: Gemini API test failed!")
        print("=" * 60)
        print(f"\nError details: {e}")
        print("\nPossible issues:")
        print("  1. API key is invalid")
        print("  2. Internet connection problem")
        print("  3. Gemini API quota exceeded")
        print("  4. Missing dependencies (run: pip install google-generativeai)")
        return False


if __name__ == "__main__":
    success = test_gemini_api()
    sys.exit(0 if success else 1)
