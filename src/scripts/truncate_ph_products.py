#!/usr/bin/env python3
"""
Script to truncate (delete all documents from) the PH-products collection in Firestore.

This script will:
1. Count all documents in the collection
2. Ask for confirmation before deleting
3. Delete all documents in batches
"""

import sys
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_firebase() -> firestore.Client:
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
                if Path(path).exists():
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


def count_documents(db: firestore.Client, collection_name: str) -> int:
    """Count the number of documents in a collection."""
    try:
        # Get all document references (more efficient than loading full documents)
        docs = db.collection(collection_name).select([]).stream()
        count = sum(1 for _ in docs)
        return count
    except Exception as e:
        logger.error(f"Error counting documents: {e}")
        raise


def truncate_collection(db: firestore.Client, collection_name: str) -> int:
    """
    Delete all documents from a Firestore collection.
    
    Args:
        db: Firestore client
        collection_name: Name of the collection to truncate
        
    Returns:
        Number of documents deleted
    """
    deleted_count = 0
    batch_size = 500  # Firestore batch limit
    
    try:
        while True:
            # Get a batch of documents
            docs = db.collection(collection_name).limit(batch_size).stream()
            batch = db.batch()
            batch_count = 0
            
            for doc in docs:
                batch.delete(doc.reference)
                batch_count += 1
            
            if batch_count == 0:
                # No more documents to delete
                break
                
            # Commit the batch
            batch.commit()
            deleted_count += batch_count
            logger.info(f"Deleted batch of {batch_count} documents. Total deleted: {deleted_count}")
            
            # If we deleted less than batch_size, we're done
            if batch_count < batch_size:
                break
                
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error truncating collection: {e}")
        raise


def main():
    """Main function to truncate the PH-products collection."""
    collection_name = "PH-products"
    
    try:
        # Initialize Firebase
        logger.info("Initializing Firebase...")
        db = initialize_firebase()
        
        # Count documents
        logger.info(f"Counting documents in '{collection_name}' collection...")
        doc_count = count_documents(db, collection_name)
        
        if doc_count == 0:
            logger.info(f"Collection '{collection_name}' is already empty.")
            return
            
        logger.info(f"Found {doc_count:,} documents in '{collection_name}' collection.")
        
        # Ask for confirmation
        print(f"\n⚠️  WARNING: This will DELETE ALL {doc_count:,} documents from the '{collection_name}' collection.")
        print("This action cannot be undone!")
        
        confirmation = input("\nType 'DELETE' to confirm deletion: ")
        
        if confirmation != "DELETE":
            logger.info("Deletion cancelled by user.")
            return
            
        # Truncate the collection
        logger.info(f"Starting deletion of all documents from '{collection_name}'...")
        deleted = truncate_collection(db, collection_name)
        
        logger.info(f"✅ Successfully deleted {deleted:,} documents from '{collection_name}' collection.")
        
        # Verify collection is empty
        final_count = count_documents(db, collection_name)
        if final_count == 0:
            logger.info("✅ Verified: Collection is now empty.")
        else:
            logger.warning(f"⚠️  Collection still contains {final_count} documents.")
            
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()