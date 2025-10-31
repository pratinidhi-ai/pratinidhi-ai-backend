"""
Test script to fetch all documents from question_bank collection
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.firebase_client import get_question_db_client
import json
import logging
from datetime import datetime
from google.api_core.datetime_helpers import DatetimeWithNanoseconds

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def datetime_converter(obj):
    """Convert Firestore DatetimeWithNanoseconds to ISO format string"""
    if isinstance(obj, (datetime, DatetimeWithNanoseconds)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def fetch_all_question_bank_docs():
    """
    Fetch all documents from the 'question_bank' collection
    and store them in a map with doc_id as key and content as value
    """
    try:
        # Get the Firestore client
        db = get_question_db_client()
        
        if db is None:
            logger.error("Failed to initialize Firestore client")
            return None
        
        logger.info("Fetching all documents from 'question_bank' collection...")
        
        # Fetch all documents from question_bank collection
        docs = db.collection('question_bank').stream()
        
        # Create a map with doc_id as key and content as value
        question_bank_map = {}
        doc_count = 0
        
        for doc in docs:
            doc_id = doc.id
            doc_data = doc.to_dict()
            question_bank_map[doc_id] = doc_data
            doc_count += 1
            logger.info(f"Fetched document: {doc_id}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Total documents fetched: {doc_count}")
        logger.info(f"{'='*60}\n")
        
        # Print summary of each document
        for doc_id, content in question_bank_map.items():
            logger.info(f"\nDocument ID: {doc_id}")
            logger.info(f"Keys in document: {list(content.keys()) if content else 'Empty'}")
            logger.info(f"-" * 60)
        
        return question_bank_map
        
    except Exception as e:
        logger.error(f"Error fetching question bank documents: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def save_to_json(question_bank_map, filename="question_bank_data.json"):
    """
    Save the question bank map to a JSON file for inspection
    """
    try:
        output_path = os.path.join(os.path.dirname(__file__), filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(question_bank_map, f, indent=2, ensure_ascii=False, default=datetime_converter)
        logger.info(f"\n✅ Data saved to: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error saving to JSON: {str(e)}")
        return None

if __name__ == "__main__":
    logger.info("="*60)
    logger.info("QUESTION BANK DATABASE TEST")
    logger.info("="*60 + "\n")
    
    # Fetch all documents
    question_bank_map = fetch_all_question_bank_docs()
    
    if question_bank_map is not None:
        logger.info(f"\n✅ Successfully fetched {len(question_bank_map)} documents from question_bank collection")
        
        # Save to JSON file for inspection
        save_to_json(question_bank_map)
        
        # Print a sample of the first document (if any)
        if question_bank_map:
            first_doc_id = list(question_bank_map.keys())[0]
            first_doc_content = question_bank_map[first_doc_id]
            
            logger.info(f"\n{'='*60}")
            logger.info(f"SAMPLE DOCUMENT")
            logger.info(f"{'='*60}")
            logger.info(f"Document ID: {first_doc_id}")
            logger.info(f"Content: {json.dumps(first_doc_content, indent=2, ensure_ascii=False, default=datetime_converter)[:500]}...")
    else:
        logger.error("❌ Failed to fetch question bank documents")
