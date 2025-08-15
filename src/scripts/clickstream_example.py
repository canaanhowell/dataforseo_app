#!/usr/bin/env python3
"""
Example script demonstrating DataForSEO Clickstream API usage.

This script shows how to:
1. Get search volume data for keywords
2. Analyze trends
3. Save results for further processing
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.dataforseo_client import DataForSEOClient, DataForSEOError
from src.config.config import Config


def analyze_keyword_trend(monthly_searches: List[Dict]) -> Dict:
    """
    Analyze keyword trend from monthly search data.
    
    Args:
        monthly_searches: List of monthly search volumes
        
    Returns:
        Dictionary with trend analysis
    """
    if not monthly_searches or len(monthly_searches) < 2:
        return {"trend": "insufficient_data", "change_percent": 0}
    
    # Get most recent and previous month
    recent = monthly_searches[-1]["search_volume"]
    previous = monthly_searches[-2]["search_volume"]
    
    # Calculate change
    if previous == 0:
        if recent > 0:
            return {"trend": "new", "change_percent": 100}
        else:
            return {"trend": "no_data", "change_percent": 0}
    
    change_percent = ((recent - previous) / previous) * 100
    
    # Determine trend
    if change_percent > 10:
        trend = "rising"
    elif change_percent < -10:
        trend = "declining"
    else:
        trend = "stable"
    
    return {
        "trend": trend,
        "change_percent": round(change_percent, 2),
        "recent_volume": recent,
        "previous_volume": previous
    }


async def get_keyword_insights(client: DataForSEOClient, keywords: List[str], location: str = "United States"):
    """
    Get comprehensive keyword insights using clickstream data.
    
    Args:
        client: DataForSEO client instance
        keywords: List of keywords to analyze
        location: Target location
    """
    print(f"\n📊 Analyzing {len(keywords)} keywords for {location}")
    print("=" * 60)
    
    try:
        # Get search volume data
        results = await client.get_search_volume(
            keywords=keywords,
            location_name=location,
            language_name="English",
            use_clickstream=True
        )
        
        print(f"Debug: Received {len(results)} results")
        
        if not results:
            print("No data returned for the specified keywords.")
            # Let's try with location code instead
            print("Trying with location code 2840 (US)...")
            results = await client.get_search_volume(
                keywords=keywords[:3],  # Try with fewer keywords
                location_code=2840,
                language_code="en",
                use_clickstream=True
            )
            print(f"Debug: Received {len(results)} results with location code")
            
        if not results:
            print("Still no results. The API might require different parameters.")
            return
        
        # Process and display results
        insights = []
        
        for result in results:
            # Analyze trend
            trend_data = analyze_keyword_trend(result.monthly_searches)
            
            insight = {
                "keyword": result.keyword,
                "search_volume": result.search_volume,
                "trend": trend_data["trend"],
                "change_percent": trend_data["change_percent"],
                "monthly_data": result.monthly_searches
            }
            insights.append(insight)
            
            # Display result
            print(f"\n🔍 Keyword: {result.keyword}")
            print(f"   Volume: {result.search_volume:,} searches/month")
            
            trend_icon = {
                "rising": "📈",
                "declining": "📉",
                "stable": "➡️",
                "new": "🆕",
                "no_data": "❓",
                "insufficient_data": "⚠️"
            }.get(trend_data["trend"], "")
            
            print(f"   Trend: {trend_icon} {trend_data['trend'].title()}", end="")
            if trend_data["change_percent"] != 0:
                print(f" ({trend_data['change_percent']:+.1f}%)")
            else:
                print()
            
            # Show recent history
            if result.monthly_searches:
                print("   Recent history:")
                for month_data in result.monthly_searches[-3:]:
                    month_str = f"{month_data['year']}-{month_data['month']:02d}"
                    print(f"     {month_str}: {month_data['search_volume']:,}")
        
        # Save results
        output_file = Path("keyword_insights.json")
        with open(output_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "location": location,
                "keywords_analyzed": len(keywords),
                "insights": insights
            }, f, indent=2)
        
        print(f"\n✅ Results saved to {output_file}")
        
        # Summary statistics
        rising = sum(1 for i in insights if i["trend"] == "rising")
        declining = sum(1 for i in insights if i["trend"] == "declining")
        stable = sum(1 for i in insights if i["trend"] == "stable")
        
        print(f"\n📊 Summary:")
        print(f"   Rising: {rising} keywords")
        print(f"   Declining: {declining} keywords")
        print(f"   Stable: {stable} keywords")
        
        # Top keywords by volume
        top_keywords = sorted(insights, key=lambda x: x["search_volume"], reverse=True)[:3]
        print(f"\n🏆 Top keywords by volume:")
        for i, kw in enumerate(top_keywords, 1):
            print(f"   {i}. {kw['keyword']}: {kw['search_volume']:,}")
        
    except DataForSEOError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def main():
    """Run example keyword analysis."""
    
    # Example keywords - you can modify these
    keywords_to_analyze = [
        "chatgpt",
        "artificial intelligence",
        "machine learning",
        "data science",
        "python programming",
        "web development",
        "cloud computing",
        "cybersecurity",
        "blockchain technology",
        "remote work"
    ]
    
    print("🚀 DataForSEO Clickstream API Example")
    print("=" * 60)
    
    # Validate configuration
    try:
        Config.validate()
        print("✓ Configuration loaded successfully")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Create client and analyze keywords
    async with DataForSEOClient(
        login=Config.DATAFORSEO_LOGIN_DECODED,
        password=Config.DATAFORSEO_PASSWORD_DECODED,
        rate_limit=Config.DATAFORSEO_RATE_LIMIT
    ) as client:
        
        # Analyze for US market
        await get_keyword_insights(client, keywords_to_analyze, "United States")
        
        # Optional: Analyze for UK market
        print("\n" + "=" * 60)
        await get_keyword_insights(client, keywords_to_analyze[:5], "United Kingdom")


if __name__ == "__main__":
    asyncio.run(main())