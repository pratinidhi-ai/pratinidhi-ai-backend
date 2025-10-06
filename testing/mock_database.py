"""
Mock Database for Local Testing
Replaces Firebase connections for local task testing
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import os

class MockFirestoreClient:
    """Mock Firestore client for local testing"""
    
    def __init__(self):
        self.collections = {
            'users': {},
            'question_bank': {
                '_metadata': {
                    'facets': {
                        'math|algebra|11': {
                            'available_tags': [
                                'linear_equations', 'quadratic_equations', 'polynomials', 
                                'factoring', 'inequalities', 'systems', 'functions',
                                'graphing', 'slopes', 'intercepts', 'domain_range'
                            ]
                        },
                        'math|data analysis|11': {
                            'available_tags': [
                                'statistics', 'probability', 'mean_median_mode', 
                                'standard_deviation', 'correlation', 'scatter_plots',
                                'histograms', 'box_plots', 'sampling'
                            ]
                        },
                        'reading & writing|grammar|11': {
                            'available_tags': [
                                'subject_verb_agreement', 'pronouns', 'modifiers',
                                'punctuation', 'comma_usage', 'semicolons',
                                'parallel_structure', 'sentence_fragments'
                            ]
                        },
                        'reading & writing|vocabulary|11': {
                            'available_tags': [
                                'context_clues', 'word_meanings', 'synonyms',
                                'antonyms', 'prefixes', 'suffixes', 'root_words',
                                'figurative_language', 'tone', 'connotation'
                            ]
                        }
                    }
                }
            }
        }
    
    def collection(self, name: str):
        """Mock collection method"""
        return MockCollection(self.collections.setdefault(name, {}))

class MockCollection:
    """Mock Firestore collection"""
    
    def __init__(self, data: Dict):
        self.data = data
    
    def document(self, doc_id: str):
        """Mock document method"""
        return MockDocument(self.data, doc_id)
    
    def where(self, field: str, op: str, value: Any):
        """Mock where query (simplified)"""
        return MockQuery(self.data, [(field, op, value)])
    
    def stream(self):
        """Mock stream method"""
        for doc_id, doc_data in self.data.items():
            if doc_id != '_metadata':  # Skip metadata
                yield MockDocumentSnapshot(doc_id, doc_data)

class MockDocument:
    """Mock Firestore document"""
    
    def __init__(self, collection_data: Dict, doc_id: str):
        self.collection_data = collection_data
        self.doc_id = doc_id
    
    def get(self):
        """Mock get method"""
        data = self.collection_data.get(self.doc_id)
        return MockDocumentSnapshot(self.doc_id, data, exists=data is not None)
    
    def set(self, data: Dict):
        """Mock set method"""
        self.collection_data[self.doc_id] = data
        return True
    
    def update(self, data: Dict):
        """Mock update method"""
        if self.doc_id not in self.collection_data:
            self.collection_data[self.doc_id] = {}
        self.collection_data[self.doc_id].update(data)
        return True
    
    def collection(self, name: str):
        """Mock subcollection method"""
        if self.doc_id not in self.collection_data:
            self.collection_data[self.doc_id] = {}
        if name not in self.collection_data[self.doc_id]:
            self.collection_data[self.doc_id][name] = {}
        return MockCollection(self.collection_data[self.doc_id][name])

class MockDocumentSnapshot:
    """Mock document snapshot"""
    
    def __init__(self, doc_id: str, data: Optional[Dict], exists: bool = True):
        self.id = doc_id
        self._data = data
        self.exists = exists and data is not None
    
    def to_dict(self):
        """Return document data"""
        return self._data or {}

class MockQuery:
    """Mock Firestore query"""
    
    def __init__(self, data: Dict, conditions: List):
        self.data = data
        self.conditions = conditions
    
    def order_by(self, field: str, direction: str = 'ASCENDING'):
        """Mock order by"""
        return self
    
    def limit(self, count: int):
        """Mock limit"""
        return self
    
    def stream(self):
        """Mock stream with filtering"""
        for doc_id, doc_data in self.data.items():
            if self._matches_conditions(doc_data):
                yield MockDocumentSnapshot(doc_id, doc_data)
    
    def _matches_conditions(self, doc_data: Dict) -> bool:
        """Check if document matches query conditions"""
        for field, op, value in self.conditions:
            doc_value = doc_data.get(field)
            
            if op == '==' and doc_value != value:
                return False
            elif op == '>=' and (doc_value is None or doc_value < value):
                return False
            elif op == '<=' and (doc_value is None or doc_value > value):
                return False
            elif op == '<' and (doc_value is None or doc_value >= value):
                return False
            elif op == '>' and (doc_value is None or doc_value <= value):
                return False
        
        return True

class MockAuth:
    """Mock Firebase Auth"""
    
    def verify_id_token(self, token: str):
        """Mock token verification"""
        return {
            'uid': 'test_user_uid',
            'email': 'test@example.com',
            'name': 'Test User'
        }

# Monkey patch database connections for testing
def setup_mock_database():
    """Replace database connections with mocks for testing"""
    
    # Mock the firebase client
    import database.firebase_client
    
    mock_client = MockFirestoreClient()
    mock_auth = MockAuth()
    
    database.firebase_client._db_client = mock_client
    database.firebase_client.get_firestore_client = lambda: mock_client
    database.firebase_client.get_auth = lambda: mock_auth
    
    print("🔧 Mock database setup complete")
    return mock_client

def load_test_data(mock_client: MockFirestoreClient):
    """Load test data into mock database"""
    
    # Add some test users
    test_users = [
        {
            'id': 'existing_user_001',
            'name': 'Existing User 1',
            'email': 'existing1@test.com',
            'completed_chapters': ['Chapter 1'],
            'current_week_start': None
        }
    ]
    
    for user in test_users:
        mock_client.collections['users'][user['id']] = user
    
    print("📚 Test data loaded into mock database")

if __name__ == "__main__":
    # Test the mock database
    client = setup_mock_database()
    load_test_data(client)
    
    # Test basic operations
    print("Testing mock database operations...")
    
    # Test document creation
    users_ref = client.collection('users')
    test_doc = users_ref.document('test123')
    test_doc.set({'name': 'Test User', 'email': 'test@example.com'})
    
    # Test document retrieval
    retrieved = test_doc.get()
    print(f"Retrieved: {retrieved.to_dict()}")
    
    # Test metadata access
    metadata_doc = client.collection('question_bank').document('_metadata').get()
    print(f"Metadata exists: {metadata_doc.exists}")
    
    print("✅ Mock database test completed!")