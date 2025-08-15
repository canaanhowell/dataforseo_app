#!/usr/bin/env python3
"""
Standalone script to get monthly search volume data for keywords.

This script can work with:
1. A list of keywords provided as command line arguments
2. Keywords from a JSON file
3. Keywords from Firestore (optional)

Output format:
{
    "keyword": {
        "total_search_volume": 5000000,
        "monthly_breakdown": {
            "2024-01": 4500000,
            "2024-02": 4800000,
            ...
        },
        "location": "United States",
        "language": "English",
        "last_updated": "2024-08-14T..."
    }
}
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import logging

# Add parent path to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent))

from utils.dataforseo_client import DataForSEOClient, DataForSEOError
from config.config import Config


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_monthly_volumes_for_keywords(
    keywords: List[str],
    location_name: str = "United States",
    language_name: str = "English"
) -> Dict[str, Dict[str, Any]]:
    """
    Get monthly search volume data for a list of keywords.
    
    Args:
        keywords: List of keywords to analyze
        location_name: Target location (default: United States)
        language_name: Target language (default: English)
        
    Returns:
        Dictionary with keyword as key and volume data as value
    """
    # Validate configuration
    Config.validate()
    
    results = {}
    
    async with DataForSEOClient(
        login=Config.DATAFORSEO_LOGIN_DECODED,
        password=Config.DATAFORSEO_PASSWORD_DECODED,
        rate_limit=Config.DATAFORSEO_RATE_LIMIT
    ) as client:
        
        # Process in batches (DataForSEO recommends max 700 keywords per request)
        batch_size = 700
        total_batches = (len(keywords) + batch_size - 1) // batch_size
        
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} keywords)")
            
            try:
                # Get search volume data
                search_results = await client.get_search_volume(
                    keywords=batch,
                    location_name=location_name,
                    language_name=language_name,
                    use_clickstream=True,
                    tag=f"monthly_volumes_batch_{batch_num}"
                )
                
                # Process results
                for result in search_results:
                    # Convert monthly searches to dictionary format
                    monthly_data = {}
                    
                    for month_data in result.monthly_searches:
                        year = month_data.get('year')
                        month = month_data.get('month')
                        volume = month_data.get('search_volume', 0)
                        
                        if year and month:
                            # Format as YYYY-MM
                            month_key = f"{year}-{month:02d}"
                            monthly_data[month_key] = volume
                    
                    # Store result
                    results[result.keyword] = {
                        "total_search_volume": result.search_volume,
                        "monthly_breakdown": monthly_data,
                        "location": location_name,
                        "language": language_name,
                        "last_updated": datetime.now().isoformat()
                    }
                    
                logger.info(f"Batch {batch_num} completed: {len([r for r in batch if r in results])} keywords with data")
                
            except DataForSEOError as e:
                logger.error(f"API error in batch {batch_num}: {e}")
                # Continue with next batch
                
            except Exception as e:
                logger.error(f"Unexpected error in batch {batch_num}: {e}")
                # Continue with next batch
            
            # Rate limiting between batches
            if i + batch_size < len(keywords):
                logger.info("Waiting 5 seconds before next batch...")
                await asyncio.sleep(5)
    
    return results


def load_keywords_from_file(file_path: str) -> List[str]:
    """Load keywords from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Handle different JSON formats
        if isinstance(data, list):
            # Simple list of keywords
            return data
        elif isinstance(data, dict):
            # Try to extract keywords from dict values
            keywords = []
            for key, value in data.items():
                if isinstance(value, str):
                    keywords.append(value)
                elif isinstance(value, dict) and 'keyword' in value:
                    keywords.append(value['keyword'])
                else:
                    keywords.append(key)
            return keywords
        else:
            raise ValueError("Unsupported JSON format")
            
    except Exception as e:
        logger.error(f"Error loading keywords from file: {e}")
        raise


def print_summary(results: Dict[str, Dict[str, Any]]) -> None:
    """Print a summary of the results."""
    total_keywords = len(results)
    keywords_with_volume = len([k for k, v in results.items() if v['total_search_volume'] > 0])
    
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    print(f"Total keywords processed: {total_keywords}")
    print(f"Keywords with search volume: {keywords_with_volume}")
    print(f"Keywords with no volume: {total_keywords - keywords_with_volume}")
    
    # Top 10 by volume
    sorted_results = sorted(
        results.items(),
        key=lambda x: x[1]['total_search_volume'],
        reverse=True
    )
    
    print(f"\n{'='*50}")
    print("TOP 10 KEYWORDS BY SEARCH VOLUME")
    print(f"{'='*50}")
    
    for i, (keyword, data) in enumerate(sorted_results[:10], 1):
        print(f"\n{i}. {keyword}")
        print(f"   Total Volume: {data['total_search_volume']:,}")
        
        # Show last 3 months
        monthly = data['monthly_breakdown']
        if monthly:
            recent_months = sorted(monthly.items())[-3:]
            print("   Recent months:")
            for month, volume in recent_months:
                print(f"     {month}: {volume:,}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Get monthly search volume data for keywords from DataForSEO"
    )
    parser.add_argument(
        "keywords",
        nargs="*",
        help="Keywords to analyze (can also use --file)"
    )
    parser.add_argument(
        "--file", "-f",
        help="JSON file containing keywords"
    )
    parser.add_argument(
        "--output", "-o",
        default="monthly_search_volumes.json",
        help="Output file path (default: monthly_search_volumes.json)"
    )
    parser.add_argument(
        "--location",
        default="United States",
        help="Target location (default: United States)"
    )
    parser.add_argument(
        "--language",
        default="English",
        help="Target language (default: English)"
    )
    
    args = parser.parse_args()
    
    # Get keywords
    keywords = []
    
    if args.file:
        logger.info(f"Loading keywords from file: {args.file}")
        keywords = load_keywords_from_file(args.file)
    elif args.keywords:
        keywords = args.keywords
    else:
        # Use sample keywords for testing
        keywords = [
            "chatgpt",
            "midjourney", 
            "stable diffusion",
            "claude ai",
            "perplexity ai"
        ]
        logger.info("No keywords provided, using sample keywords for testing")
    
    logger.info(f"Processing {len(keywords)} keywords...")
    
    # Get search volumes
    results = asyncio.run(get_monthly_volumes_for_keywords(
        keywords,
        location_name=args.location,
        language_name=args.language
    ))
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(exist_ok=True, parents=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to: {output_path}")
    
    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()