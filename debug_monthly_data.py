#!/usr/bin/env python3
"""
Debug script to examine the ordering of monthly_searches data from DataForSEO API
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils.dataforseo_client import DataForSEOClient
from src.config.config import Config

async def debug_monthly_ordering():
    """Debug the ordering of monthly_searches data"""
    
    try:
        Config.validate()
        
        # Test with a single keyword to examine the monthly data structure
        test_keyword = "airtable"
        
        async with DataForSEOClient(
            login=Config.DATAFORSEO_LOGIN_DECODED,
            password=Config.DATAFORSEO_PASSWORD_DECODED,
            rate_limit=Config.DATAFORSEO_RATE_LIMIT
        ) as client:
            
            print(f"Testing monthly data ordering for keyword: {test_keyword}")
            print("=" * 60)
            
            results = await client.get_search_volume(
                keywords=[test_keyword],
                location_name="United States",
                language_name="English",
                use_clickstream=True
            )
            
            if results:
                result = results[0]
                print(f"Keyword: {result.keyword}")
                print(f"Total Search Volume: {result.search_volume:,}")
                print(f"Monthly searches count: {len(result.monthly_searches)}")
                print("\nRaw monthly_searches data from API:")
                print(json.dumps(result.monthly_searches, indent=2))
                
                print("\nProcessed monthly data (as currently done in script):")
                monthly_data = {}
                month_names = {
                    1: "January", 2: "February", 3: "March", 4: "April",
                    5: "May", 6: "June", 7: "July", 8: "August",
                    9: "September", 10: "October", 11: "November", 12: "December"
                }
                
                for month_data in result.monthly_searches:
                    year = month_data.get('year')
                    month_num = month_data.get('month')
                    volume = month_data.get('search_volume', 0)
                    
                    if year and month_num and month_num in month_names:
                        month_key = f"{month_names[month_num]} {year}"
                        monthly_data[month_key] = volume
                        
                print(json.dumps(monthly_data, indent=2))
                
                print("\nMonthly data sorted by date (as shown in display):")
                from datetime import datetime
                monthly_items = []
                for month_year, volume in monthly_data.items():
                    try:
                        date_obj = datetime.strptime(month_year, "%B %Y")
                        monthly_items.append((date_obj, month_year, volume))
                    except:
                        continue
                
                monthly_items.sort(key=lambda x: x[0])
                
                print("All months in chronological order:")
                for date_obj, month_year, volume in monthly_items:
                    print(f"  {month_year}: {volume:,}")
                    
                print("\nLast 3 months (as displayed by script):")
                for date_obj, month_year, volume in monthly_items[-3:]:
                    print(f"  {month_year}: {volume:,}")
                    
            else:
                print("No results returned from API")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_monthly_ordering())