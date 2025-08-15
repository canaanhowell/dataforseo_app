#!/usr/bin/env python3
"""
Test script to verify DataForSEO Clickstream API connection.

This script demonstrates:
1. Connecting to DataForSEO API
2. Getting locations and languages
3. Fetching search volume data
4. Getting global search volume with country distribution
"""

import asyncio
import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.dataforseo_client import DataForSEOClient, DataForSEOError
from src.config.config import Config


async def test_locations_and_languages(client: DataForSEOClient):
    """Test getting locations and languages."""
    print("\n=== Testing Locations and Languages Endpoint ===")
    try:
        result = await client.get_locations_and_languages()
        print(f"✓ Successfully retrieved locations and languages")
        print(f"  Status: {result.get('status_code')}")
        print(f"  Tasks count: {result.get('tasks_count')}")
        
        # Display sample locations
        if result.get('tasks'):
            locations = result['tasks'][0].get('result', [])
            if locations:
                print(f"\n  Sample locations (first 5):")
                for loc in locations[:5]:
                    print(f"    - {loc.get('location_name')} (code: {loc.get('location_code')})")
                    
    except DataForSEOError as e:
        print(f"✗ Error: {e}")
        return False
    return True


async def test_search_volume(client: DataForSEOClient):
    """Test search volume endpoint with location."""
    print("\n=== Testing Search Volume Endpoint ===")
    
    test_keywords = ["python programming", "data science", "machine learning"]
    
    try:
        results = await client.get_search_volume(
            keywords=test_keywords,
            location_name="United States",
            language_name="English",
            use_clickstream=True
        )
        
        print(f"✓ Successfully retrieved search volume for {len(results)} keywords")
        
        for result in results:
            print(f"\n  Keyword: {result.keyword}")
            print(f"    Search Volume: {result.search_volume:,}")
            print(f"    Clickstream: {result.use_clickstream}")
            
            if result.monthly_searches:
                print("    Recent monthly data:")
                for month_data in result.monthly_searches[-3:]:  # Last 3 months
                    print(f"      {month_data['year']}-{month_data['month']:02d}: {month_data['search_volume']:,}")
                    
    except DataForSEOError as e:
        print(f"✗ Error: {e}")
        return False
    except ValueError as e:
        print(f"✗ Validation Error: {e}")
        return False
    return True


async def test_global_search_volume(client: DataForSEOClient):
    """Test global search volume endpoint."""
    print("\n=== Testing Global Search Volume Endpoint ===")
    
    test_keywords = ["youtube", "facebook", "google"]
    
    try:
        results = await client.get_global_search_volume(keywords=test_keywords)
        
        print(f"✓ Successfully retrieved global search volume for {len(results)} keywords")
        
        for result in results:
            print(f"\n  Keyword: {result.keyword}")
            print(f"    Global Search Volume: {result.search_volume:,}")
            
            if result.country_distribution:
                print("    Top 5 countries:")
                for country in result.country_distribution[:5]:
                    print(f"      {country['country_iso_code']}: {country['search_volume']:,} ({country['percentage']:.1f}%)")
                    
    except DataForSEOError as e:
        print(f"✗ Error: {e}")
        return False
    except ValueError as e:
        print(f"✗ Validation Error: {e}")
        return False
    return True


async def test_search_volume_by_location(client: DataForSEOClient):
    """Test search volume by specific location."""
    print("\n=== Testing Search Volume by Location Endpoint ===")
    
    test_keywords = ["coffee shops", "restaurants near me"]
    
    try:
        results = await client.get_search_volume_by_location(
            keywords=test_keywords,
            location_name="United Kingdom"
        )
        
        print(f"✓ Successfully retrieved location-specific search volume for {len(results)} keywords")
        
        for result in results:
            print(f"\n  Keyword: {result.keyword}")
            print(f"    UK Search Volume: {result.search_volume:,}")
            
            if result.monthly_searches:
                # Calculate trend
                if len(result.monthly_searches) >= 2:
                    recent = result.monthly_searches[-1]['search_volume']
                    previous = result.monthly_searches[-2]['search_volume']
                    if previous > 0:
                        trend = ((recent - previous) / previous) * 100
                        trend_icon = "↑" if trend > 0 else "↓"
                        print(f"    Trend: {trend_icon} {abs(trend):.1f}%")
                        
    except DataForSEOError as e:
        print(f"✗ Error: {e}")
        return False
    except ValueError as e:
        print(f"✗ Validation Error: {e}")
        return False
    return True


async def main():
    """Run all tests."""
    print("DataForSEO Clickstream API Connection Test")
    print("=" * 50)
    
    # Validate configuration
    try:
        Config.validate()
        print("✓ Configuration validated")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("\nPlease ensure your .env file contains:")
        print("  - dataforseo_login_password (base64 encoded)")
        print("  - GOOGLE_PROJECT_ID")
        return
    
    # Display configuration (non-sensitive)
    print("\nConfiguration:")
    for key, value in Config.to_dict().items():
        print(f"  {key}: {value}")
    
    # Create client and run tests
    async with DataForSEOClient(
        login=Config.DATAFORSEO_LOGIN_DECODED,
        password=Config.DATAFORSEO_PASSWORD_DECODED,
        rate_limit=Config.DATAFORSEO_RATE_LIMIT
    ) as client:
        
        # Run all tests
        tests_passed = 0
        total_tests = 4
        
        if await test_locations_and_languages(client):
            tests_passed += 1
            
        if await test_search_volume(client):
            tests_passed += 1
            
        if await test_global_search_volume(client):
            tests_passed += 1
            
        if await test_search_volume_by_location(client):
            tests_passed += 1
        
        # Summary
        print(f"\n{'=' * 50}")
        print(f"Tests Summary: {tests_passed}/{total_tests} passed")
        
        if tests_passed == total_tests:
            print("✓ All tests passed! DataForSEO Clickstream API is working correctly.")
        else:
            print("✗ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())