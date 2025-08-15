#!/usr/bin/env python3
"""
Demonstrate how time period affects Google Trends scaling.
"""

import asyncio
import aiohttp
import base64
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.config.config import Config


async def test_trends_timeperiod(keyword: str, days: int):
    """Test Google Trends with different time periods."""
    
    auth = base64.b64encode(f"{Config.DATAFORSEO_LOGIN_DECODED}:{Config.DATAFORSEO_PASSWORD_DECODED}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    
    date_to = datetime.now()
    date_from = date_to - timedelta(days=days)
    
    payload = [{
        "keywords": [keyword],
        "location_code": 2840,
        "language_code": "en",
        "date_from": date_from.strftime("%Y-%m-%d"),
        "date_to": date_to.strftime("%Y-%m-%d")
    }]
    
    print(f"\nTime period: Last {days} days ({date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')})")
    print("-" * 60)
    
    async with aiohttp.ClientSession() as session:
        url = "https://api.dataforseo.com/v3/keywords_data/google_trends/explore/live"
        
        async with session.post(url, json=payload, headers=headers) as response:
            result = await response.json()
            
            if result.get("status_code") == 20000:
                tasks = result.get("tasks", [])
                if tasks and tasks[0].get("status_code") == 20000:
                    task_result = tasks[0].get("result", [])
                    if task_result and "items" in task_result[0]:
                        item = task_result[0]["items"][0]
                        
                        # Get average
                        if "averages" in item:
                            avg = item["averages"][0] if isinstance(item["averages"][0], (int, float)) else 0
                            print(f"Average value: {avg}")
                        
                        # Get min/max from data
                        if "data" in item:
                            values = []
                            for point in item["data"]:
                                vals = point.get("values", [])
                                if vals:
                                    val = vals[0] if isinstance(vals[0], (int, float)) else 0
                                    values.append(val)
                            
                            if values:
                                print(f"Peak value: {max(values)} (this will always be scaled to ~100)")
                                print(f"Lowest value: {min(values)}")
                                print(f"Today's value: {values[-1] if values else 'N/A'}")
                                
                                # Show sample of values
                                print(f"\nSample values (last 5 days):")
                                for i, point in enumerate(item["data"][-5:]):
                                    date = point.get("date_from", "")
                                    val = point.get("values", [0])[0]
                                    print(f"  {date}: {val}")


async def main():
    """Compare different time periods for the same keyword."""
    
    print("Google Trends Time Period Effect on Scaling")
    print("=" * 60)
    print("\nTesting keyword: 'chatgpt'")
    print("\nNOTE: The peak in each time period will be scaled to 100,")
    print("so the same date can have different values in different periods!")
    
    # Test different time periods
    for days in [7, 30, 90, 365]:
        await test_trends_timeperiod("chatgpt", days)
        await asyncio.sleep(2)
    
    print("\n" + "=" * 60)
    print("KEY INSIGHTS:")
    print("- Shorter periods: More granular, recent peaks dominate")
    print("- Longer periods: Smooths out spikes, shows bigger picture")
    print("- Same date can have different values in different time ranges")
    print("- Example: If ChatGPT peaked in December 2022:")
    print("  * Last 7 days: Recent days might show 80-100")
    print("  * Last 365 days: Recent days might show 30-50 (vs Dec 2022 peak)")


if __name__ == "__main__":
    asyncio.run(main())