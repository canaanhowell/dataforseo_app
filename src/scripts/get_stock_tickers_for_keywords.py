#!/usr/bin/env python3
"""
Script to check if keywords are publicly traded companies and get their stock ticker symbols.

This script:
1. Reads keywords from master_keywords_detailed.json
2. Uses OpenAI GPT-5 to check if each keyword is a publicly traded company
3. If yes, gets the stock ticker symbol
4. Adds ticker symbols to the JSON file
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

def check_publicly_traded_and_get_ticker(client: OpenAI, keyword: str) -> dict:
    """
    Check if a keyword represents a publicly traded company and get its ticker symbol.
    
    Args:
        client: OpenAI client instance
        keyword: The keyword/company name to check
        
    Returns:
        dict with is_publicly_traded (bool) and ticker_symbol (str or None)
    """
    prompt = f"""
Analyze the following keyword/name and determine:
1. Is this a publicly traded company? (Yes/No)
2. If yes, what is the primary stock ticker symbol?

Keyword: "{keyword}"

Please respond in this exact format:
Is Publicly Traded: [Yes/No]
Ticker Symbol: [SYMBOL or None]

Important:
- Only answer "Yes" if this is clearly a publicly traded company
- For the ticker symbol, provide the most common/primary ticker (e.g., for Google/Alphabet, use GOOGL)
- If it's a subsidiary of a public company, use the parent company's ticker
- If not publicly traded or not a company, respond with "No" and "None"
"""

    try:
        response = client.chat.completions.create(
            model="gpt-5",  # Using GPT-5 for accurate analysis
            messages=[
                {"role": "system", "content": "You are a financial analyst expert who identifies publicly traded companies and their stock ticker symbols."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=100
            # GPT-5 only supports default temperature (1)
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse the response
        lines = result.split('\n')
        is_publicly_traded = False
        ticker_symbol = None
        
        for line in lines:
            if "Is Publicly Traded:" in line:
                is_publicly_traded = "Yes" in line or "yes" in line
            elif "Ticker Symbol:" in line:
                ticker_part = line.split(":", 1)[1].strip()
                if ticker_part and ticker_part.lower() != "none" and ticker_part != "N/A":
                    ticker_symbol = ticker_part.upper()
        
        return {
            "is_publicly_traded": is_publicly_traded,
            "ticker_symbol": ticker_symbol,
            "raw_response": result
        }
        
    except Exception as e:
        print(f"    ✗ Error checking {keyword}: {str(e)}")
        return {
            "is_publicly_traded": False,
            "ticker_symbol": None,
            "error": str(e)
        }


def main():
    """Main execution function."""
    
    # Load API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables")
        return
    
    client = OpenAI(api_key=api_key)
    
    # Load master keywords file
    keywords_file = Path("/workspace/exploding_topics_app/config/master_keywords_detailed.json")
    if not keywords_file.exists():
        print(f"Error: Keywords file not found at {keywords_file}")
        return
    
    with open(keywords_file, 'r') as f:
        data = json.load(f)
    
    keywords = data.get("keywords", [])
    total_keywords = len(keywords)
    
    print(f"Processing {total_keywords} keywords to find publicly traded companies...")
    print("=" * 60)
    
    # Process each keyword
    publicly_traded_count = 0
    processed_count = 0
    
    # Create backup before modifying
    backup_file = keywords_file.with_suffix('.backup.json')
    with open(backup_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Created backup at: {backup_file}")
    print()
    
    for idx, keyword_data in enumerate(keywords, 1):
        keyword_name = keyword_data.get("name", "")
        
        # Skip if empty name or if ticker already exists
        if not keyword_name:
            continue
            
        if "ticker_symbol" in keyword_data:
            print(f"[{idx}/{total_keywords}] {keyword_name} - Already has ticker: {keyword_data['ticker_symbol']}")
            continue
        
        print(f"[{idx}/{total_keywords}] Checking: {keyword_name}")
        
        # Check with OpenAI
        result = check_publicly_traded_and_get_ticker(client, keyword_name)
        
        if result["is_publicly_traded"] and result["ticker_symbol"]:
            keyword_data["ticker_symbol"] = result["ticker_symbol"]
            keyword_data["is_publicly_traded"] = True
            publicly_traded_count += 1
            print(f"    ✓ Publicly traded: {result['ticker_symbol']}")
        else:
            print(f"    - Not publicly traded")
        
        processed_count += 1
        
        # Rate limiting - GPT-5 might have different limits
        if processed_count % 10 == 0:
            time.sleep(2)  # Brief pause every 10 requests
            
            # Save progress periodically
            with open(keywords_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"    💾 Progress saved...")
    
    # Update metadata
    data["metadata"]["ticker_update"] = {
        "updated_at": datetime.now().isoformat(),
        "publicly_traded_count": publicly_traded_count,
        "processed_count": processed_count,
        "model_used": "gpt-5"
    }
    
    # Save final results
    with open(keywords_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"Complete! Found {publicly_traded_count} publicly traded companies out of {processed_count} processed")
    print(f"Results saved to: {keywords_file}")
    
    # Show summary of companies with tickers
    print("\nPublicly traded companies found:")
    for keyword_data in keywords:
        if keyword_data.get("ticker_symbol"):
            print(f"  • {keyword_data['name']}: {keyword_data['ticker_symbol']}")


if __name__ == "__main__":
    main()