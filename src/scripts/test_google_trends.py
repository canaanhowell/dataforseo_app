#!/usr/bin/env python3
"""
Test Google Trends API to get more recent data.
"""

import asyncio
import aiohttp
import base64
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config.config import Config


async def test_google_trends(keyword: str):
    """Test Google Trends API for recent data."""
    
    # Prepare auth
    auth = base64.b64encode(f"{Config.DATAFORSEO_LOGIN_DECODED}:{Config.DATAFORSEO_PASSWORD_DECODED}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    
    # Set date range - last 90 days
    date_to = datetime.now()
    date_from = date_to - timedelta(days=90)
    
    payload = [{
        "keywords": [keyword],
        "location_code": 2840,  # United States
        "language_code": "en",
        "date_from": date_from.strftime("%Y-%m-%d"),
        "date_to": date_to.strftime("%Y-%m-%d"),
        # "type": "web_search"  # Remove this - not a valid field
    }]
    
    print(f"Testing Google Trends for: '{keyword}'")
    print(f"Date range: {date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')}")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        url = "https://api.dataforseo.com/v3/keywords_data/google_trends/explore/live"
        
        try:
            async with session.post(url, json=payload, headers=headers) as response:
                result = await response.json()
                
                print(f"Status Code: {response.status}")
                
                if result.get("status_code") == 20000:
                    tasks = result.get("tasks", [])
                    if tasks and tasks[0].get("status_code") == 20000:
                        task_result = tasks[0].get("result", [])
                        if task_result:
                            data = task_result[0]
                            
                            # Debug - print available keys
                            print(f"\nAvailable data keys: {list(data.keys())}")
                            
                            # Check items
                            if "items" in data:
                                items = data["items"]
                                print(f"\nFound {len(items)} items")
                                
                                if items:
                                    # Check first item structure
                                    first_item = items[0]
                                    print(f"First item keys: {list(first_item.keys())}")
                                    
                                    # Process first item (should be interest_over_time)
                                    item = items[0]
                                    print(f"\nProcessing item type: {item.get('type')}")
                                    
                                    if "data" in item:
                                        time_data = item["data"]
                                        print(f"\nTime series data points: {len(time_data)}")
                                        
                                        # Show last 15 data points
                                        print("\nRecent trend data:")
                                        for point in time_data[-15:]:
                                            date_from = point.get('date_from', '')
                                            date_to = point.get('date_to', '')
                                            values = point.get('values', [])
                                            if values and isinstance(values, list) and len(values) > 0:
                                                # Values might be just numbers, not dicts
                                                value = values[0] if isinstance(values[0], (int, float)) else values[0].get('value', 0)
                                                print(f"  {date_from} to {date_to}: {value}")
                                        
                                        # Show averages if available
                                        if "averages" in item:
                                            averages = item["averages"]
                                            if averages:
                                                avg_value = averages[0].get('value', 0)
                                                print(f"\nAverage value over period: {avg_value}")
                                    
                            # Show current metrics
                            if "metrics" in data:
                                print(f"\nMetrics:")
                                metrics = data["metrics"]
                                for key, value in metrics.items():
                                    print(f"  {key}: {value}")
                        else:
                            print("No result data")
                    else:
                        print(f"Task error: {tasks[0].get('status_message') if tasks else 'Unknown'}")
                else:
                    print(f"API error: {result.get('status_message')}")
                    
                # Show cost
                if "cost" in result:
                    print(f"\nAPI Cost: ${result['cost']}")
                    
        except Exception as e:
            print(f"Error: {e}")


async def compare_data_sources():
    """Compare search volume vs trends data."""
    
    keywords = ["chatgpt", "claude", "gemini"]
    
    for keyword in keywords:
        print(f"\n{'='*60}")
        await test_google_trends(keyword)
        await asyncio.sleep(2)  # Rate limiting


if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else "chatgpt"
    asyncio.run(test_google_trends(keyword))