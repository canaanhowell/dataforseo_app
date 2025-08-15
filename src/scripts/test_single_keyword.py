#!/usr/bin/env python3
"""
Test a single keyword to verify data accuracy.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.dataforseo_client import DataForSEOClient
from src.config.config import Config


async def test_keyword(keyword: str):
    """Test a single keyword and show detailed results."""
    
    print(f"Testing keyword: '{keyword}'")
    print("=" * 60)
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        return
    
    async with DataForSEOClient(
        login=Config.DATAFORSEO_LOGIN_DECODED,
        password=Config.DATAFORSEO_PASSWORD_DECODED,
        rate_limit=Config.DATAFORSEO_RATE_LIMIT
    ) as client:
        
        try:
            # Test with US location
            print("\n🇺🇸 United States results:")
            results = await client.get_search_volume(
                keywords=[keyword],
                location_code=2840,
                language_code="en"
            )
            
            if results:
                for result in results:
                    print(f"  Keyword: {result.keyword}")
                    print(f"  Search Volume: {result.search_volume:,}")
                    print(f"  Location Code: {result.location_code}")
                    print(f"  Language Code: {result.language_code}")
                    
                    if result.monthly_searches:
                        print(f"  Monthly data (last 6 months):")
                        for month_data in result.monthly_searches[:6]:
                            print(f"    {month_data['year']}-{month_data['month']:02d}: {month_data['search_volume']:,}")
            else:
                print("  No results returned")
                
            # Test with Global search
            print("\n🌍 Global search volume:")
            global_results = await client.get_search_volume(
                keywords=[keyword],
                location_name="United Kingdom",
                language_name="English"
            )
            
            if global_results:
                for result in global_results:
                    print(f"  UK Search Volume: {result.search_volume:,}")
            
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else "chatgpt"
    asyncio.run(test_keyword(keyword))