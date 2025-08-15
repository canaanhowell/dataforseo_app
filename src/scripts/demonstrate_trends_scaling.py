#!/usr/bin/env python3
"""
Demonstrate how Google Trends scaling works with different keyword comparisons.
"""

print("Google Trends Relative Scaling Explained")
print("=" * 60)

print("\n1. HOW GOOGLE TRENDS WORKS:")
print("   - Values are ALWAYS relative to the highest point in the data")
print("   - The highest point = 100")
print("   - Everything else is scaled relative to that peak")

print("\n2. SINGLE KEYWORD EXAMPLE:")
print("   If you search 'chatgpt' alone:")
print("   - Its highest day in the period = 100")
print("   - A day with half the searches = 50")
print("   - The numbers tell you about relative popularity over time")

print("\n3. MULTIPLE KEYWORDS EXAMPLE:")
print("   If you search 'chatgpt' vs 'claude':")
print("   - The highest point ACROSS BOTH keywords = 100")
print("   - If ChatGPT's peak is 10x higher than Claude's peak:")
print("     * ChatGPT's peak = 100")
print("     * Claude's peak = 10")
print("   - All other values scale accordingly")

print("\n4. REAL EXAMPLE - ChatGPT in different contexts:")
print("\n   Searched alone:")
print("     ChatGPT: averages 75-85 (relative to its own peak)")
print("\n   Searched with 'perplexity ai':")
print("     ChatGPT: would show ~100 (much bigger)")
print("     Perplexity: would show ~5-10 (much smaller)")
print("\n   Searched with 'google':")
print("     ChatGPT: might show ~20-30 (Google is much bigger)")
print("     Google: would show ~90-100")

print("\n5. KEY INSIGHTS:")
print("   ✗ You CANNOT compare absolute values across different searches")
print("   ✗ 'ChatGPT=50' when searched alone ≠ 'ChatGPT=50' when compared to others")
print("   ✓ You CAN see relative popularity between keywords in the same search")
print("   ✓ You CAN track trends over time within the same search")

print("\n6. FOR ABSOLUTE DATA:")
print("   Use the Search Volume API instead:")
print("   - ChatGPT: 55,600,000 searches/month (absolute)")
print("   - Perplexity AI: 368,000 searches/month (absolute)")
print("   - Character AI: 5,000,000 searches/month (absolute)")
print("\n" + "=" * 60)