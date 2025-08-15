#!/usr/bin/env python3
"""
Debug script to examine what's actually stored in Firestore
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path

def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    try:
        # Check if already initialized
        try:
            firebase_admin.get_app()
            print("✓ Firebase app already initialized")
        except ValueError:
            # Look for service account file
            service_account_files = [
                'ai-tracker-466821-bc88c21c2489.json',
                '/workspace/ai-tracker-466821-bc88c21c2489.json',
                str(Path(__file__).parent / 'ai-tracker-466821-bc88c21c2489.json')
            ]
            
            service_account_path = None
            for path in service_account_files:
                if os.path.exists(path):
                    service_account_path = path
                    break
            
            if not service_account_path:
                raise FileNotFoundError(f"Service account file not found. Tried: {service_account_files}")
            
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            print(f"✓ Firebase initialized with: {service_account_path}")
        
        return firestore.client()
        
    except Exception as e:
        print(f"✗ Failed to initialize Firebase: {e}")
        raise

def debug_firestore_data():
    """Check what's actually stored in Firestore for specific keywords."""
    
    print("Debugging Firestore Data")
    print("=" * 60)
    
    db = initialize_firebase()
    
    # Test keywords that we know have recent data
    test_keywords = ["airtable", "apple vision pro", "chatgpt"]
    
    for keyword in test_keywords:
        print(f"\nChecking Firestore data for: {keyword}")
        print("-" * 40)
        
        # Try to find document by ID first
        doc_ref = db.collection("dataforseo_keywords").document(keyword)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            print(f"✓ Found document with ID: {keyword}")
            
            # Check for search_volume field
            if 'search_volume' in data:
                search_volume = data['search_volume']
                print(f"search_volume type: {type(search_volume)}")
                
                if isinstance(search_volume, dict):
                    print(f"Monthly data entries: {len(search_volume)}")
                    
                    # Sort months chronologically
                    from datetime import datetime
                    monthly_items = []
                    for month_year, volume in search_volume.items():
                        try:
                            date_obj = datetime.strptime(month_year, "%B %Y")
                            monthly_items.append((date_obj, month_year, volume))
                        except:
                            continue
                    
                    monthly_items.sort(key=lambda x: x[0])
                    
                    print("All stored months:")
                    for date_obj, month_year, volume in monthly_items:
                        print(f"  {month_year}: {volume:,}")
                    
                    print(f"\nMost recent 3 months in Firestore:")
                    for date_obj, month_year, volume in monthly_items[-3:]:
                        print(f"  {month_year}: {volume:,}")
                        
                else:
                    print(f"search_volume value: {search_volume}")
            else:
                print("✗ No search_volume field found")
            
            # Show other relevant fields
            print(f"\nOther fields:")
            for key, value in data.items():
                if key != 'search_volume':
                    if key == 'search_volume_updated':
                        print(f"  {key}: {value}")
                    elif key == 'total_search_volume':
                        print(f"  {key}: {value:,}" if isinstance(value, (int, float)) else f"  {key}: {value}")
                    else:
                        print(f"  {key}: {str(value)[:100]}...")  # Truncate long values
        
        else:
            # Try to find by keyword field
            query = db.collection("dataforseo_keywords").where('keyword', '==', keyword).limit(1)
            docs = list(query.stream())
            
            if docs:
                doc = docs[0]
                data = doc.to_dict()
                print(f"✓ Found document with keyword field: {keyword} (ID: {doc.id})")
                
                if 'search_volume' in data:
                    search_volume = data['search_volume']
                    print(f"search_volume: {search_volume}")
                else:
                    print("✗ No search_volume field found")
            else:
                print(f"✗ No document found for keyword: {keyword}")

if __name__ == "__main__":
    debug_firestore_data()