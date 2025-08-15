#!/usr/bin/env python3
"""
Analyze the keyword volumes data and provide insights.
"""

import json
from pathlib import Path
from datetime import datetime


def main():
    """Analyze keyword volumes and print statistics."""
    
    # Load the data
    data_path = Path("/workspace/exploding_topics_app/config/keyword_volumes.json")
    with open(data_path, "r") as f:
        data = json.load(f)
    
    print("Keyword Volume Analysis")
    print("=" * 60)
    print(f"Date: {data[0]['date'] if data else 'N/A'}")
    print(f"Total keywords: {len(data)}")
    
    # Calculate statistics
    volumes = [item["volume"] for item in data]
    keywords_with_volume = [item for item in data if item["volume"] > 0]
    keywords_no_volume = [item for item in data if item["volume"] == 0]
    
    print(f"\nKeywords with search volume: {len(keywords_with_volume)}")
    print(f"Keywords with no search volume: {len(keywords_no_volume)}")
    
    if keywords_with_volume:
        total_volume = sum(item["volume"] for item in keywords_with_volume)
        avg_volume = total_volume / len(keywords_with_volume)
        
        print(f"\nTotal monthly search volume: {total_volume:,}")
        print(f"Average volume per keyword: {avg_volume:,.0f}")
        
        # Top 20 keywords
        sorted_keywords = sorted(keywords_with_volume, key=lambda x: x["volume"], reverse=True)
        
        print(f"\nTop 20 keywords by search volume:")
        for i, item in enumerate(sorted_keywords[:20], 1):
            print(f"{i:2d}. {item['keyword']:<30} {item['volume']:>10,}")
        
        # Volume distribution
        print(f"\nVolume distribution:")
        ranges = [
            (0, 100, "0-100"),
            (100, 1000, "100-1K"),
            (1000, 10000, "1K-10K"),
            (10000, 100000, "10K-100K"),
            (100000, 1000000, "100K-1M"),
            (1000000, float('inf'), "1M+")
        ]
        
        for min_vol, max_vol, label in ranges:
            count = sum(1 for item in keywords_with_volume 
                       if min_vol <= item["volume"] < max_vol)
            if count > 0:
                print(f"  {label:<10} {count:>4} keywords")
    
    # Keywords with no volume
    if keywords_no_volume:
        print(f"\nKeywords with no search volume ({len(keywords_no_volume)}):")
        for item in keywords_no_volume[:20]:  # Show first 20
            print(f"  - {item['keyword']}")
        if len(keywords_no_volume) > 20:
            print(f"  ... and {len(keywords_no_volume) - 20} more")


if __name__ == "__main__":
    main()