#!/usr/bin/env python3
"""
Test how Google Trends data changes based on keyword comparison.
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


async def test_trends_comparison(keywords_list):
    """Test Google Trends with different keyword combinations."""
    
    auth = base64.b64encode(f"{Config.DATAFORSEO_LOGIN_DECODED}:{Config.DATAFORSEO_PASSWORD_DECODED}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    
    # Date range - last 30 days
    date_to = datetime.now()
    date_from = date_to - timedelta(days=30)
    
    payload = [{
        "keywords": keywords_list,
        "location_code": 2840,  # US
        "language_code": "en",
        "date_from": date_from.strftime("%Y-%m-%d"),
        "date_to": date_to.strftime("%Y-%m-%d")
    }]
    
    print(f"\nTesting with keywords: {', '.join(keywords_list)}")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        url = "https://api.dataforseo.com/v3/keywords_data/google_trends/explore/live"
        
        async with session.post(url, json=payload, headers=headers) as response:
            result = await response.json()
            
            if result.get("status_code") == 20000:
                tasks = result.get("tasks", [])
                if tasks and tasks[0].get("status_code") == 20000:
                    task_result = tasks[0].get("result", [])
                    if task_result:
                        data = task_result[0]
                        
                        if "items" in data and data["items"]:
                            item = data["items"][0]
                            
                            # Get averages for each keyword
                            if "averages" in item:
                                averages = item["averages"]
                                for i, keyword in enumerate(keywords_list):
                                    if i < len(averages):
                                        avg_value = averages[i] if isinstance(averages[i], (int, float)) else averages[i].get('value', 0)
                                        print(f"  {keyword}: {avg_value} (average over period)")
                            
                            # Show last few data points
                            if "data" in item:
                                time_data = item["data"]
                                print(f"\nLast 5 data points:")
                                
                                for point in time_data[-5:]:
                                    date = point.get('date_from', '')
                                    values = point.get('values', [])
                                    
                                    value_str = ""
                                    for i, keyword in enumerate(keywords_list):
                                        if i < len(values):
                                            value = values[i] if isinstance(values[i], (int, float)) else values[i].get('value', 0)
                                            value_str += f"{keyword}: {value}, "
                                    
                                    print(f"  {date}: {value_str.rstrip(', ')}")


async def main():
    """Run comparison tests."""
    
    print("Google Trends Relative Scale Demonstration")
    print("=" * 60)
    
    # Test 1: ChatGPT alone
    await test_trends_comparison(["chatgpt"])
    await asyncio.sleep(2)
    
    # Test 2: ChatGPT vs small keyword
    await test_trends_comparison(["chatgpt", "dataforseo"])
    await asyncio.sleep(2)
    
    # Test 3: ChatGPT vs similar-sized keyword
    await test_trends_comparison(["chatgpt", "google"])
    await asyncio.sleep(2)
    
    # Test 4: Multiple AI products
    await test_trends_comparison(["chatgpt", "claude", "gemini", "copilot", "perplexity"])
    
    print("\n" + "=" * 60)
    print("IMPORTANT: Notice how the same keyword (chatgpt) gets different")
    print("values depending on what it's compared against!")


if __name__ == "__main__":
    asyncio.run(main())