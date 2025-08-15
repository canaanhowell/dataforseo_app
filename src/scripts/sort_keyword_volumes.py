#!/usr/bin/env python3
"""
Sort keyword volumes by volume in descending order.
"""

import json
from pathlib import Path


def main():
    """Sort keyword volumes and save."""
    
    # Load the data
    input_path = Path("/workspace/dataforseo_app/config/keyword_volumes.json")
    with open(input_path, "r") as f:
        data = json.load(f)
    
    # Sort by volume descending (handle None values)
    sorted_data = sorted(
        data, 
        key=lambda x: x["volume"] if x["volume"] is not None else 0, 
        reverse=True
    )
    
    # Save sorted data
    output_path = Path("/workspace/dataforseo_app/config/keyword_volumes_sorted.json")
    with open(output_path, "w") as f:
        json.dump(sorted_data, f, indent=2)
    
    print(f"✅ Sorted data saved to: {output_path}")
    
    # Show top 20
    print("\nTop 20 keywords by search volume:")
    print("-" * 50)
    for i, item in enumerate(sorted_data[:20], 1):
        volume = item["volume"] if item["volume"] is not None else 0
        print(f"{i:2d}. {item['keyword']:<30} {volume:>12,}")
    
    # Show some statistics
    volumes = [item["volume"] for item in sorted_data if item["volume"] is not None and item["volume"] > 0]
    if volumes:
        print(f"\nStatistics:")
        print(f"  Total keywords: {len(sorted_data)}")
        print(f"  Keywords with volume > 0: {len(volumes)}")
        print(f"  Total monthly searches: {sum(volumes):,}")
        print(f"  Highest volume: {max(volumes):,}")
        print(f"  Lowest volume > 0: {min(volumes):,}")


if __name__ == "__main__":
    main()