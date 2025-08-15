#!/usr/bin/env python3
"""
Script to fetch keywords from Firestore and update their search volume data with monthly breakdown.
This version cleanly handles keywords with special characters by removing/replacing them.

This script:
1. Fetches keywords from Firestore
2. Cleans keywords to remove invalid characters
3. Gets monthly search volume data from DataForSEO API
4. Outputs JSON with monthly breakdown
5. Updates Firestore with the new data
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
import firebase_admin
from firebase_admin import credentials, firestore

# Add parent path to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent))

from utils.dataforseo_client import DataForSEOClient, SearchVolumeResult, DataForSEOError
from config.config import Config


# Setup logging
def setup_logging():
    """Initialize logging with proper handlers and formatters."""
    Path("logs").mkdir(exist_ok=True)
    
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    app_handler = logging.FileHandler('logs/app.log')
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(detailed_formatter)
    
    error_handler = logging.FileHandler('logs/error.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    
    network_logger = logging.getLogger('network')
    network_logger.setLevel(logging.INFO)
    network_logger.propagate = False
    
    network_handler = logging.FileHandler('logs/network.log')
    network_handler.setFormatter(detailed_formatter)
    network_logger.addHandler(network_handler)
    
    return logging.getLogger(__name__)


logger = setup_logging()


class FirestoreKeywordUpdater:
    """Handles fetching keywords from Firestore and updating their search volumes."""
    
    def __init__(self):
        """Initialize Firestore client."""
        self.db = self._initialize_firebase()
        # Keep track of original to cleaned keyword mapping
        self.keyword_mapping = {}
        # Track keywords that were modified
        self.modified_keywords = []
        
    def _initialize_firebase(self) -> firestore.Client:
        """Initialize Firebase Admin SDK."""
        try:
            # Check if already initialized
            try:
                firebase_admin.get_app()
                logger.info("Firebase app already initialized")
            except ValueError:
                # Look for service account file
                service_account_files = [
                    'ai-tracker-466821-bc88c21c2489.json',
                    '/workspace/ai-tracker-466821-bc88c21c2489.json',
                    str(Path(__file__).parent.parent.parent / 'ai-tracker-466821-bc88c21c2489.json')
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
                logger.info(f"Firebase initialized with: {service_account_path}")
            
            return firestore.client()
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    def clean_keyword_for_api(self, keyword: str) -> Tuple[str, bool]:
        """
        Clean keyword for DataForSEO API by removing/replacing invalid characters.
        
        Args:
            keyword: Original keyword
            
        Returns:
            Tuple of (cleaned keyword, was_modified)
        """
        original = keyword
        
        # Handle specific known patterns
        replacements = {
            ", Inc.": "",  # Remove company suffixes
            ".Ai": " AI",  # Replace .Ai with space AI
            ".AI": " AI",  # Replace .AI with space AI
            ".Io": " IO",  # Replace .Io with space IO
            ".IO": " IO",  # Replace .IO with space IO
            ".Com": "",    # Remove .Com
            ".com": "",    # Remove .com
            "2.5": "2",    # Simplify version numbers
        }
        
        # Apply replacements
        for old, new in replacements.items():
            keyword = keyword.replace(old, new)
        
        # Remove any remaining commas and periods at the end
        keyword = keyword.rstrip('.,')
        
        # Check if we modified it
        was_modified = keyword != original
        
        if was_modified:
            logger.info(f"Cleaned keyword: '{original}' -> '{keyword}'")
            self.modified_keywords.append((original, keyword))
        
        return keyword, was_modified
    
    def fetch_keywords_from_firestore(self, collection_name: str = "dataforseo_keywords") -> List[str]:
        """
        Fetch all keywords from Firestore collection.
        
        Args:
            collection_name: Name of the Firestore collection containing keywords
            
        Returns:
            List of keyword strings
        """
        try:
            keywords = []
            docs = self.db.collection(collection_name).stream()
            
            for doc in docs:
                data = doc.to_dict()
                # Handle different possible field names
                keyword = data.get('keyword') or data.get('name') or doc.id
                if keyword:
                    keywords.append(keyword)
                    
            logger.info(f"Fetched {len(keywords)} keywords from Firestore collection: {collection_name}")
            return keywords
            
        except Exception as e:
            logger.error(f"Error fetching keywords from Firestore: {e}")
            raise
    
    async def get_monthly_search_volumes(
        self, 
        keywords: List[str],
        location_name: str = "United States",
        language_name: str = "English"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get monthly search volume data for keywords.
        
        Args:
            keywords: List of keywords to process
            location_name: Target location
            language_name: Target language
            
        Returns:
            Dictionary mapping keywords to their monthly search data
        """
        Config.validate()
        
        results = {}
        
        # Clean keywords and maintain mapping
        cleaned_keywords = []
        for keyword in keywords:
            cleaned, was_modified = self.clean_keyword_for_api(keyword)
            cleaned_keywords.append(cleaned)
            # Store mapping from cleaned to original
            self.keyword_mapping[cleaned] = keyword
        
        async with DataForSEOClient(
            login=Config.DATAFORSEO_LOGIN_DECODED,
            password=Config.DATAFORSEO_PASSWORD_DECODED,
            rate_limit=Config.DATAFORSEO_RATE_LIMIT
        ) as client:
            
            # Process in batches
            batch_size = min(700, Config.MAX_KEYWORDS_PER_BATCH)  # DataForSEO recommends 700 max
            
            for i in range(0, len(cleaned_keywords), batch_size):
                batch = cleaned_keywords[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(cleaned_keywords) + batch_size - 1)//batch_size}")
                
                try:
                    search_results = await client.get_search_volume(
                        keywords=batch,
                        location_name=location_name,
                        language_name=language_name,
                        use_clickstream=True,
                        tag=f"firestore_update_batch_{i//batch_size + 1}"
                    )
                    
                    for result in search_results:
                        # Skip keywords with no search volume data
                        if result.search_volume is None:
                            logger.warning(f"No search volume data for keyword: {result.keyword}")
                            continue
                        
                        # Get the original keyword from our mapping
                        original_keyword = self.keyword_mapping.get(result.keyword, result.keyword)
                            
                        # Format monthly data with simple month-year format
                        monthly_data = {}
                        month_names = {
                            1: "January", 2: "February", 3: "March", 4: "April",
                            5: "May", 6: "June", 7: "July", 8: "August",
                            9: "September", 10: "October", 11: "November", 12: "December"
                        }
                        
                        if result.monthly_searches:  # Check if monthly_searches exists
                            for month_data in result.monthly_searches:
                                year = month_data.get('year')
                                month_num = month_data.get('month')
                                volume = month_data.get('search_volume', 0)
                                
                                if year and month_num and month_num in month_names:
                                    # Simple format: "June 2025"
                                    month_key = f"{month_names[month_num]} {year}"
                                    monthly_data[month_key] = volume
                        
                        results[original_keyword] = {
                            "search_volume": monthly_data,  # Store monthly data directly as search_volume
                            "total_volume": result.search_volume or 0,  # Keep total for reference
                            "last_updated": datetime.now().isoformat(),
                            "cleaned_keyword": result.keyword if result.keyword != original_keyword else None
                        }
                        
                except DataForSEOError as e:
                    logger.error(f"API error processing batch {i//batch_size + 1}: {e}")
                    # Continue with next batch instead of failing
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error processing batch {i//batch_size + 1}: {e}")
                    continue
                
                # Add delay between batches to respect rate limits
                if i + batch_size < len(cleaned_keywords):
                    await asyncio.sleep(5)  # 5 second delay between batches
        
        return results
    
    def update_firestore_with_volumes(
        self, 
        search_volumes: Dict[str, Dict[str, Any]], 
        collection_name: str = "dataforseo_keywords"
    ) -> None:
        """
        Update Firestore documents with search volume data in main document fields.
        
        Args:
            search_volumes: Dictionary of search volume data
            collection_name: Firestore collection to update
        """
        try:
            batch = self.db.batch()
            batch_size = 0
            max_batch_size = 500  # Firestore batch limit
            updated_count = 0
            skipped_count = 0
            
            for keyword, volume_data in search_volumes.items():
                # Prepare the update data with the search_volume field containing monthly data
                update_data = {
                    'search_volume': volume_data['search_volume'],  # This now contains the monthly breakdown
                    'search_volume_updated': volume_data['last_updated'],
                    'total_search_volume': volume_data['total_volume']  # Store total separately if needed
                }
                
                # If we had to clean the keyword, store that info too
                if volume_data.get('cleaned_keyword'):
                    update_data['search_volume_cleaned_keyword'] = volume_data['cleaned_keyword']
                
                # Since dataforseo_keywords collection uses document ID as the keyword,
                # we can directly reference the document
                doc_ref = self.db.collection(collection_name).document(keyword)
                
                # Check if document exists
                doc = doc_ref.get()
                if doc.exists:
                    batch.update(doc_ref, update_data)
                    batch_size += 1
                    updated_count += 1
                else:
                    # If document doesn't exist by ID, try to find by keyword field
                    query = self.db.collection(collection_name).where('keyword', '==', keyword).limit(1)
                    docs = list(query.stream())
                    
                    if docs:
                        doc_ref = docs[0].reference
                        batch.update(doc_ref, update_data)
                        batch_size += 1
                        updated_count += 1
                    else:
                        logger.warning(f"No document found for keyword: {keyword}")
                        skipped_count += 1
                    
                if batch_size >= max_batch_size:
                    batch.commit()
                    logger.info(f"Committed batch of {batch_size} updates")
                    batch = self.db.batch()
                    batch_size = 0
            
            # Commit remaining updates
            if batch_size > 0:
                batch.commit()
                logger.info(f"Committed final batch of {batch_size} updates")
            
            logger.info(f"Firestore update complete: {updated_count} documents updated, {skipped_count} skipped")
                
        except Exception as e:
            logger.error(f"Error updating Firestore: {e}")
            raise


async def main():
    """Main function to orchestrate the keyword search volume update."""
    
    try:
        # Initialize updater
        updater = FirestoreKeywordUpdater()
        
        # Fetch keywords from Firestore
        logger.info("Fetching keywords from Firestore...")
        keywords = updater.fetch_keywords_from_firestore()
        
        if not keywords:
            logger.warning("No keywords found in Firestore")
            return
        
        logger.info(f"Found {len(keywords)} keywords to process")
        
        # Get monthly search volumes
        logger.info("Fetching search volume data from DataForSEO...")
        search_volumes = await updater.get_monthly_search_volumes(keywords)
        
        # Save results to JSON file
        output_path = Path(__file__).parent.parent.parent / "data" / "firestore_search_volumes.json"
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(search_volumes, f, indent=2)
        
        logger.info(f"Saved search volume data to {output_path}")
        
        # Print summary
        logger.info(f"\nSummary:")
        logger.info(f"- Keywords processed: {len(search_volumes)}")
        logger.info(f"- Keywords with data: {len([k for k, v in search_volumes.items() if v['total_volume'] > 0])}")
        logger.info(f"- Keywords with no data: {len([k for k, v in search_volumes.items() if v['total_volume'] == 0])}")
        logger.info(f"- Keywords modified for API: {len(updater.modified_keywords)}")
        
        if updater.modified_keywords:
            print("\n" + "="*60)
            print("KEYWORDS MODIFIED FOR API COMPATIBILITY")
            print("="*60)
            for original, cleaned in updater.modified_keywords[:10]:
                print(f"{original} -> {cleaned}")
            if len(updater.modified_keywords) > 10:
                print(f"... and {len(updater.modified_keywords) - 10} more")
        
        # Automatically update Firestore
        logger.info("\nUpdating Firestore with new search volume data...")
        updater.update_firestore_with_volumes(search_volumes)
        
        # Print sample of results
        print("\n" + "="*60)
        print("TOP 10 KEYWORDS BY SEARCH VOLUME")
        print("="*60)
        
        sorted_results = sorted(
            search_volumes.items(), 
            key=lambda x: x[1]['total_volume'], 
            reverse=True
        )[:10]
        
        for i, (keyword, data) in enumerate(sorted_results, 1):
            print(f"\n{i}. {keyword}")
            print(f"   Total volume: {data['total_volume']:,}")
            if data.get('cleaned_keyword'):
                print(f"   (Searched as: {data['cleaned_keyword']})")
            print(f"   Recent months:")
            
            # Show first 3 months from the data
            monthly_items = list(data['search_volume'].items())
            for month_key, volume in monthly_items[:3]:
                print(f"     {month_key}: {volume:,}")
        
        print("\n" + "="*60)
        print(f"Process complete! Updated {len(search_volumes)} keywords in Firestore.")
        print(f"Data also saved to: {output_path}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Script failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())