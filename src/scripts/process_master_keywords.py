#!/usr/bin/env python3
"""
Process all keywords from master_keywords.json and get search volume data.
Output format: keyword, volume, date
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.dataforseo_client import DataForSEOClient, DataForSEOError
from src.config.config import Config


async def process_keywords_batch(
    client: DataForSEOClient,
    keywords: List[str],
    location_code: int = 2840  # United States
) -> List[Dict]:
    """
    Process a batch of keywords and return formatted results.
    
    Args:
        client: DataForSEO client instance
        keywords: List of keywords to process
        location_code: Location code (default: US)
        
    Returns:
        List of dictionaries with keyword, volume, date
    """
    results = []
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Get search volume data
        search_results = await client.get_search_volume(
            keywords=keywords,
            location_code=location_code,
            language_code="en"
        )
        
        # Format results
        for result in search_results:
            results.append({
                "keyword": result.keyword,
                "volume": result.search_volume if result.search_volume is not None else 0,
                "date": current_date
            })
            
        # Add missing keywords with 0 volume
        found_keywords = {r.keyword.lower() for r in search_results}
        for keyword in keywords:
            if keyword.lower() not in found_keywords:
                results.append({
                    "keyword": keyword,
                    "volume": 0,
                    "date": current_date
                })
                
    except DataForSEOError as e:
        print(f"Error processing batch: {e}")
        # Add all keywords with error status
        for keyword in keywords:
            results.append({
                "keyword": keyword,
                "volume": -1,  # -1 indicates error
                "date": current_date
            })
    
    return results


async def main():
    """Process all master keywords and save results."""
    
    print("DataForSEO Master Keywords Processor")
    print("=" * 60)
    
    # Load master keywords
    master_keywords_path = Path("/workspace/dataforseo_app/config/master_keywords.json")
    with open(master_keywords_path, "r") as f:
        data = json.load(f)
        keywords = data["products"]
    
    print(f"Loaded {len(keywords)} keywords from master list")
    
    # Validate configuration
    try:
        Config.validate()
        print("✓ Configuration validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Initialize results
    all_results = []
    
    # Process keywords in batches
    # DataForSEO allows up to 700 keywords per request
    batch_size = 100  # Conservative batch size
    total_batches = (len(keywords) + batch_size - 1) // batch_size
    
    async with DataForSEOClient(
        login=Config.DATAFORSEO_LOGIN_DECODED,
        password=Config.DATAFORSEO_PASSWORD_DECODED,
        rate_limit=Config.DATAFORSEO_RATE_LIMIT
    ) as client:
        
        print(f"\nProcessing {total_batches} batches...")
        
        for i in range(0, len(keywords), batch_size):
            batch_num = (i // batch_size) + 1
            batch = keywords[i:i + batch_size]
            
            print(f"\nBatch {batch_num}/{total_batches}: Processing {len(batch)} keywords...")
            
            # Process batch
            batch_results = await process_keywords_batch(client, batch)
            all_results.extend(batch_results)
            
            # Show progress
            processed = min(i + batch_size, len(keywords))
            print(f"Progress: {processed}/{len(keywords)} keywords processed")
            
            # Rate limiting - wait between batches
            if batch_num < total_batches:
                wait_time = 5  # 5 seconds between batches
                print(f"Waiting {wait_time} seconds before next batch...")
                await asyncio.sleep(wait_time)
    
    # Save results
    output_path = Path("/workspace/dataforseo_app/config/keyword_volumes.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n✅ Results saved to {output_path}")
    
    # Summary statistics
    total_keywords = len(all_results)
    keywords_with_volume = sum(1 for r in all_results if r["volume"] > 0)
    keywords_no_volume = sum(1 for r in all_results if r["volume"] == 0)
    keywords_error = sum(1 for r in all_results if r["volume"] == -1)
    total_volume = sum(r["volume"] for r in all_results if r["volume"] > 0)
    
    print(f"\n📊 Summary:")
    print(f"   Total keywords: {total_keywords}")
    print(f"   Keywords with volume: {keywords_with_volume}")
    print(f"   Keywords with no volume: {keywords_no_volume}")
    print(f"   Keywords with errors: {keywords_error}")
    print(f"   Total search volume: {total_volume:,}")
    
    # Show top 10 keywords by volume
    top_keywords = sorted(
        [r for r in all_results if r["volume"] > 0],
        key=lambda x: x["volume"],
        reverse=True
    )[:10]
    
    if top_keywords:
        print(f"\n🏆 Top 10 keywords by volume:")
        for i, kw in enumerate(top_keywords, 1):
            print(f"   {i}. {kw['keyword']}: {kw['volume']:,}")
    
    # Estimate cost
    estimated_cost = total_batches * 0.075  # $0.075 per request
    print(f"\n💰 Estimated API cost: ${estimated_cost:.2f}")


if __name__ == "__main__":
    asyncio.run(main())