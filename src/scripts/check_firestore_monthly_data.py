#!/usr/bin/env python3
"""
Quick script to check what monthly data is actually in Firestore for a few sample keywords.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
from pathlib import Path

# Initialize Firebase
try:
    firebase_admin.get_app()
except ValueError:
    service_account_path = '/workspace/ai-tracker-466821-bc88c21c2489.json'
    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Check a few keywords
keywords_to_check = ["chatgpt", "character ai", "deepseek", "airtable", "apple vision pro"]

print("Checking monthly search volume data in Firestore:\n")

for keyword in keywords_to_check:
    try:
        # Try document ID first
        doc = db.collection('dataforseo_keywords').document(keyword).get()
        
        if doc.exists:
            data = doc.to_dict()
            print(f"\n{keyword}:")
            
            if 'search_volume' in data and isinstance(data['search_volume'], dict):
                # Get all months and sort them
                months = list(data['search_volume'].keys())
                
                # Sort by parsing the month-year format
                from datetime import datetime
                sorted_months = []
                for month in months:
                    try:
                        date_obj = datetime.strptime(month, "%B %Y")
                        sorted_months.append((date_obj, month))
                    except:
                        pass
                
                sorted_months.sort(key=lambda x: x[0], reverse=True)
                
                # Show the most recent 5 months
                print("  Most recent months:")
                for _, month in sorted_months[:5]:
                    volume = data['search_volume'][month]
                    print(f"    {month}: {volume:,}")
                    
                # Show total count
                print(f"  Total months stored: {len(months)}")
                
                # Show oldest and newest
                if sorted_months:
                    print(f"  Date range: {sorted_months[-1][1]} to {sorted_months[0][1]}")
            else:
                print("  No search_volume field or it's not a dict")
                print(f"  Fields in document: {list(data.keys())}")
        else:
            print(f"\n{keyword}: Document not found")
            
    except Exception as e:
        print(f"\n{keyword}: Error - {e}")

print("\n" + "="*50)
print("Checking document structure for 'chatgpt':")
doc = db.collection('dataforseo_keywords').document('chatgpt').get()
if doc.exists:
    data = doc.to_dict()
    for key, value in data.items():
        if key == 'search_volume' and isinstance(value, dict):
            print(f"  {key}: <dict with {len(value)} months>")
        else:
            print(f"  {key}: {type(value).__name__} - {str(value)[:100]}")