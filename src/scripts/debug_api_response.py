#!/usr/bin/env python3
"""
Debug script to see raw DataForSEO API responses.
"""

import asyncio
import sys
import json
import aiohttp
import base64
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config.config import Config


async def debug_api_call():
    """Make a direct API call and print the full response."""
    
    # Prepare auth
    auth = base64.b64encode(f"{Config.DATAFORSEO_LOGIN_DECODED}:{Config.DATAFORSEO_PASSWORD_DECODED}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    
    # Test payload
    payload = [{
        "keywords": ["python", "javascript", "react"],
        "location_code": 2840,  # United States
        "language_code": "en"
    }]
    
    print("Making API call with payload:")
    print(json.dumps(payload, indent=2))
    print("\n" + "="*60 + "\n")
    
    async with aiohttp.ClientSession() as session:
        url = "https://api.dataforseo.com/v3/keywords_data/google/search_volume/live"
        
        async with session.post(url, json=payload, headers=headers) as response:
            response_text = await response.text()
            
            print(f"Status Code: {response.status}")
            print(f"Headers: {dict(response.headers)}")
            print("\nRaw Response:")
            print(response_text)
            
            try:
                response_json = json.loads(response_text)
                print("\nParsed Response (formatted):")
                print(json.dumps(response_json, indent=2))
                
                # Check for tasks
                if "tasks" in response_json and response_json["tasks"]:
                    task = response_json["tasks"][0]
                    print(f"\nTask Status: {task.get('status_code')} - {task.get('status_message')}")
                    print(f"Task Cost: ${task.get('cost', 0)}")
                    
                    if "result" in task and task["result"]:
                        result = task["result"][0]
                        print(f"\nResult items count: {result.get('items_count', 0)}")
                        
                        if "items" in result and result["items"]:
                            print("\nFirst few items:")
                            for i, item in enumerate(result["items"][:3]):
                                print(f"\n  Item {i+1}:")
                                print(f"    Keyword: {item.get('keyword')}")
                                print(f"    Search Volume: {item.get('search_volume')}")
                                print(f"    Competition: {item.get('competition')}")
                                print(f"    CPC: ${item.get('cpc', 0)}")
                        else:
                            print("\nNo items in result!")
                            print(f"Full result object: {json.dumps(result, indent=2)}")
                            
            except json.JSONDecodeError as e:
                print(f"\nError parsing JSON: {e}")


async def test_google_ads_endpoint():
    """Test the Google Ads search volume endpoint instead."""
    
    print("\n" + "="*60)
    print("Testing Google Ads Search Volume endpoint...")
    print("="*60 + "\n")
    
    auth = base64.b64encode(f"{Config.DATAFORSEO_LOGIN_DECODED}:{Config.DATAFORSEO_PASSWORD_DECODED}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    
    payload = [{
        "keywords": ["seo tools", "keyword research", "backlink checker"],
        "location_code": 2840,
        "language_code": "en"
    }]
    
    async with aiohttp.ClientSession() as session:
        url = "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live"
        
        async with session.post(url, json=payload, headers=headers) as response:
            response_json = await response.json()
            
            print(f"Status Code: {response.status}")
            print(f"Status Message: {response_json.get('status_message')}")
            
            if response_json.get("tasks"):
                task = response_json["tasks"][0]
                print(f"\nTask Status: {task.get('status_code')} - {task.get('status_message')}")
                
                if task.get("result"):
                    result = task["result"][0]
                    print(f"Items count: {result.get('items_count', 0)}")
                    
                    if result.get("items"):
                        print("\nKeyword data:")
                        for item in result["items"]:
                            print(f"  - {item['keyword']}: {item.get('search_volume', 'N/A')} searches/month")


async def main():
    """Run debug tests."""
    print("DataForSEO API Debug Script")
    print("="*60)
    
    # Validate configuration
    try:
        Config.validate()
        print("✓ Configuration validated")
        print(f"  Login: {Config.DATAFORSEO_LOGIN_DECODED}")
        print(f"  API Key: {Config.DATAFORSEO_API_KEY}")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        return
    
    # Test regular search volume endpoint
    await debug_api_call()
    
    # Test Google Ads endpoint
    await test_google_ads_endpoint()


if __name__ == "__main__":
    asyncio.run(main())