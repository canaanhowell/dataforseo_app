#!/usr/bin/env python3
"""
Flexible Google Trends search with customizable time periods.
"""

import asyncio
import aiohttp
import base64
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.config.config import Config


async def search_trends(
    keywords,
    days_back=30,
    custom_date_from=None,
    custom_date_to=None,
    location_code=2840  # US default
):
    """
    Search Google Trends with flexible time period options.
    
    Args:
        keywords: List of keywords (max 5)
        days_back: Number of days to look back (ignored if custom dates provided)
        custom_date_from: Custom start date (YYYY-MM-DD string)
        custom_date_to: Custom end date (YYYY-MM-DD string)
        location_code: Location code (default US)
    """
    
    auth = base64.b64encode(f"{Config.DATAFORSEO_LOGIN_DECODED}:{Config.DATAFORSEO_PASSWORD_DECODED}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    
    # Set date range
    if custom_date_from and custom_date_to:
        date_from = custom_date_from
        date_to = custom_date_to
    else:
        date_to = datetime.now().strftime("%Y-%m-%d")
        date_from = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    payload = [{
        "keywords": keywords if isinstance(keywords, list) else [keywords],
        "location_code": location_code,
        "language_code": "en",
        "date_from": date_from,
        "date_to": date_to
    }]
    
    print(f"\nSearching trends for: {', '.join(keywords if isinstance(keywords, list) else [keywords])}")
    print(f"Date range: {date_from} to {date_to}")
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
                        
                        # Show averages
                        if "averages" in item and item["averages"]:
                            print("\nAverage values over period:")
                            for i, kw in enumerate(keywords if isinstance(keywords, list) else [keywords]):
                                if i < len(item["averages"]):
                                    avg = item["averages"][i]
                                    print(f"  {kw}: {avg}")
                        
                        # Show recent data points
                        if "data" in item:
                            data_points = item["data"]
                            print(f"\nTotal data points: {len(data_points)}")
                            print("\nLast 5 data points:")
                            
                            for point in data_points[-5:]:
                                date = point.get("date_from", "")
                                values = point.get("values", [])
                                print(f"  {date}:", end="")
                                
                                for i, kw in enumerate(keywords if isinstance(keywords, list) else [keywords]):
                                    if i < len(values):
                                        val = values[i] if isinstance(values[i], (int, float)) else 0
                                        print(f" {kw}={val}", end="")
                                print()
                                
            print(f"\nAPI Cost: ${result.get('cost', 0)}")


async def main():
    """Demonstrate different time period options."""
    
    print("Google Trends API - Time Period Examples")
    print("=" * 60)
    
    # Example 1: Last 7 days
    print("\n1. LAST 7 DAYS")
    await search_trends("chatgpt", days_back=7)
    await asyncio.sleep(2)
    
    # Example 2: Last 30 days
    print("\n\n2. LAST 30 DAYS")
    await search_trends("chatgpt", days_back=30)
    await asyncio.sleep(2)
    
    # Example 3: Last year
    print("\n\n3. LAST 365 DAYS")
    await search_trends("chatgpt", days_back=365)
    await asyncio.sleep(2)
    
    # Example 4: Custom date range
    print("\n\n4. CUSTOM DATE RANGE (Jan 1 - Mar 31, 2025)")
    await search_trends(
        "chatgpt",
        custom_date_from="2025-01-01",
        custom_date_to="2025-03-31"
    )
    await asyncio.sleep(2)
    
    # Example 5: Multiple keywords over 90 days
    print("\n\n5. MULTIPLE KEYWORDS - LAST 90 DAYS")
    await search_trends(
        ["chatgpt", "claude", "gemini"],
        days_back=90
    )
    
    print("\n" + "=" * 60)
    print("AVAILABLE TIME PERIOD OPTIONS:")
    print("- days_back: Simple way to look back X days from today")
    print("- custom_date_from/to: Specific date range (YYYY-MM-DD)")
    print("- Maximum range depends on data availability")
    print("- Shorter periods = more granular daily data")
    print("- Longer periods = might aggregate to weekly/monthly")


if __name__ == "__main__":
    asyncio.run(main())