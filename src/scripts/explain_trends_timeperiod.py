#!/usr/bin/env python3
"""
Explain how time period affects Google Trends scaling with examples.
"""

print("How Time Period Affects Google Trends Scaling")
print("=" * 60)

print("\nIMAGINE CHATGPT'S ACTUAL SEARCH VOLUME:")
print("  - December 2022: 100 million searches (launch spike)")
print("  - January 2023: 80 million searches")
print("  - August 2025: 55 million searches (current)")

print("\n1. LAST 7 DAYS VIEW:")
print("   Period: Aug 8-14, 2025")
print("   - Highest day (Aug 13): 55.5M searches → Shows as 100")
print("   - Today (Aug 14): 55.2M searches → Shows as ~99")
print("   - Lowest day (Aug 10): 54.8M searches → Shows as ~98")
print("   Result: Values range 98-100 (very stable week)")

print("\n2. LAST 30 DAYS VIEW:")
print("   Period: Jul 15 - Aug 14, 2025")
print("   - Highest day (Jul 20): 58M searches → Shows as 100")
print("   - Today (Aug 14): 55.2M searches → Shows as ~95")
print("   - Lowest day (Aug 1): 52M searches → Shows as ~90")
print("   Result: More variation visible (90-100 range)")

print("\n3. LAST 365 DAYS VIEW:")
print("   Period: Aug 2024 - Aug 2025")
print("   - Highest day (Apr 2025): 101M searches → Shows as 100")
print("   - Today (Aug 14): 55.2M searches → Shows as ~55")
print("   - December 2022 peak would be off the chart!")
print("   Result: Current interest looks much lower (55 vs peak)")

print("\n4. ALL TIME VIEW (if available):")
print("   - December 2022: 100M → Shows as 100")
print("   - Today: 55.2M → Shows as ~55")
print("   Result: Shows the full rise and fall story")

print("\nKEY TAKEAWAYS:")
print("✓ Same date, different values in different time ranges")
print("✓ Shorter periods = Recent trends magnified")
print("✓ Longer periods = Historical context included")
print("✓ Peak in the selected period ALWAYS = 100")

print("\nPRACTICAL IMPLICATIONS:")
print("- Want to see if interest is growing this week? Use 7 days")
print("- Want to see seasonal patterns? Use 365 days")
print("- Want to compare to historical peaks? Use longest period")
print("- Want current momentum? Use shortest period")

print("\nFOR ABSOLUTE DATA:")
print("Use Search Volume API - it gives you the actual numbers")
print("regardless of time period or comparison keywords!")
print("=" * 60)