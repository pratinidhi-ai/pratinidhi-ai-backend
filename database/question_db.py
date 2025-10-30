"""
Question database operations
Handles all database interactions related to questions and question banks
"""

import logging
import random
from typing import List, Dict, Any, Optional
from database.firebase_client import get_question_db_client

logger = logging.getLogger(__name__)

class QuestionDatabase:
    """Database operations for question management"""
    
    def __init__(self):
        self.db = get_question_db_client()
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Get question bank metadata.
        
        NOTE: This function is UNCHANGED. It assumes the '_metadata'
        document still exists and has the same structure as before.
        If its structure has also changed, this (and the functions
        that depend on it) will need to be updated.
        """
        try:
            if self.db is None:
                logger.error("Firestore client is not initialized.")
                return None

            doc = self.db.collection('question_bank').document('_metadata').get()
            
            if doc.exists:
                metadata = doc.to_dict()
                logger.info("Retrieved question bank metadata")
                return metadata
            
            logger.warning("Question bank metadata not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting metadata: {str(e)}")
            return None
    
    def get_questions(self, attributes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get questions based on provided attributes.
        
        REFACTORED for the new database structure.
        """
        nques = attributes.get('nques', 5)
        
        # Validate and convert nques to int
        try:
            nques = int(nques) if nques is not None else 5
        except (ValueError, TypeError):
            nques = 5
            logger.warning("Invalid nques value, defaulting to 5")
        
        try:
            if self.db is None:
                logger.error("Firestore client is not initialized.")
                return []

            # --- START OF REFACTORED LOGIC ---

            # 1. Build the new document path (standard is no longer in the path)
            doc_path = f"{attributes['subject']}|{attributes['subcategory']}"
            
            # 2. Build the new base collection reference
            base_query = (self.db.collection('question_bank')
                          .document(doc_path)
                          .collection('difficulty_levels')
                          .document(str(attributes['difficulty']))
                          .collection('questions'))

            # 3. Apply filters using .where() instead of complex paths
            #    These fields are now inside the question document
            
            # Filter by standard (assuming 'standard' is passed as a string, e.g., "11")
            query = base_query.where("question_standard", "==", str(attributes['standard']))
            
            # Filter by exam, if provided
            exam = attributes.get('exam')
            if exam:
                query = query.where("question_exam", "==", exam)
                
            # Filter by tags, if provided
            # Assumes 'tags' is a single tag string, matching old behavior
            # The 'tags' field in Firestore must be an ARRAY
            tags = attributes.get('tags')
            if tags:
                query = query.where("tags", "array_contains", tags)

            # 4. Get random questions using 'random_value' field
            rand_value = random.random()
            query_random = (query
                            .where("random_value", ">=", rand_value)
                            .order_by("random_value")
                            .limit(nques))
            
            docs_random = list(query_random.stream())
            result = []
            
            # 5. Process results directly (no need for get_question_by_id)
            #    The documents returned ARE the questions.
            for doc in docs_random:
                question_data = doc.to_dict()
                if question_data:
                    question_data['id'] = doc.id  # Add the Firestore document ID
                    result.append(question_data)
            
            # 6. Fallback query if not enough questions were found
            if len(result) < nques:
                remaining_needed = nques - len(result)
                query_fallback = (query
                                  .where("random_value", "<", rand_value)
                                  .order_by("random_value")
                                  .limit(remaining_needed))
                
                docs_fallback = list(query_fallback.stream())
                
                for doc in docs_fallback:
                    question_data = doc.to_dict()
                    if question_data:
                        question_data['id'] = doc.id
                        result.append(question_data)
            
            # --- END OF REFACTORED LOGIC ---
            
            logger.info(f"Retrieved {len(result)} questions for query: {attributes}")
            return result 
            
        except Exception as e:
            logger.error(f"Error getting questions: {str(e)}")
            return []
    
    def _build_question_collection_ref(self, sub_path: str, attributes: Dict[str, Any]):
        """
        DEPRECATED: This method's logic is no longer needed with the new
        DB structure. Filters are now applied using .where() in get_questions.
        """
        logger.warning("_build_question_collection_ref is deprecated and should not be called.")
        raise NotImplementedError
    
    def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific question by its ID.
        
        REFACTORED: Uses a Collection Group query to find the question
        in any 'questions' subcollection, based on its 'question_id' FIELD.
        
        !! IMPORTANT !!
        This requires a Firestore Index:
        - Collection ID: questions
        - Field: question_id (Ascending)
        - Scope: Collection Group
        """
        try:
            if self.db is None:
                logger.error("Firestore client is not initialized in get_question_by_id.")
                return None

            # Use a collection group query to find the doc in any "questions" collection
            query_ref = self.db.collection_group('questions').where("question_id", "==", question_id).limit(1)
            docs = list(query_ref.stream())
            
            if docs:
                doc = docs[0]
                question_data = doc.to_dict()
                if question_data is not None:
                    question_data['id'] = doc.id  # Ensure Firestore doc ID is included
                    return question_data
                else:
                    logger.warning(f"Document for question_id {question_id} exists but contains no data.")
                    return None
            
            logger.warning(f"Question not found with question_id: {question_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting question {question_id}: {str(e)}")
            return None

        
    def get_random_tags_by_facets(self, facets: str, num_tags: int = 10) -> List[str]:
        """
        Get random tags based on provided facets.
        
        NOTE: This function is UNCHANGED. It appears compatible with the
        new structure, as it queries the facet document directly
        (e.g., 'question_bank/math|advanced-math').
        """
        try:
            if self.db is None:
                logger.error("Firestore client is not initialized in get_random_tags_by_facets.")
                raise ValueError("Firestore client is not initialized.")

            # Get the document for the specified facets
            # This path (e.g., question_bank/math|algebra) seems correct
            doc_ref = self.db.collection('question_bank').document(facets)
            doc = doc_ref.get()

            if doc.exists:
                doc_dict = doc.to_dict()
                available_tags = doc_dict.get('available_tags', []) if doc_dict is not None else []
                if available_tags:
                    # Randomly select tags
                    selected_tags = random.sample(available_tags, min(num_tags, len(available_tags)))
                    logger.info(f"Retrieved {len(selected_tags)} random tags for facets {facets}")
                    return selected_tags

            logger.warning(f"No available tags found for facets {facets}, using mock tags")
            return self._generate_mock_tags(facets, num_tags)

        except Exception as e:
            logger.error(f"Error getting random tags for facets {facets}: {str(e)}")
            return self._generate_mock_tags(facets, num_tags)

    def get_questions_by_facet(self, facet: str, num_questions: int = 10) -> List[str]:
        """
        Get available question tags for a specific facet.
        
        NOTE: This function is UNCHANGED. It relies on get_metadata()
        and the '_metadata' document. If that doc's structure has
        changed (e.g., it no longer uses 'subject|subcategory|standard'
        as keys), this will need to be refactored.
        """
        try:
            # Split facet into components
            facet_parts = facet.split('|')
            if len(facet_parts) != 3:
                logger.error(f"Invalid facet format: {facet}")
                return []
            
            subject, subcategory, standard = facet_parts
            
            # Get metadata to find available tags for this facet
            metadata = self.get_metadata()
            if not metadata:
                logger.error("Could not retrieve metadata for facet query")
                return self._generate_mock_tags(subcategory, num_questions)
            
            # Navigate metadata structure to find available tags
            facets = metadata.get('facets', {})
            facet_data = facets.get(facet, {})
            available_tags = facet_data.get('available_tags', [])
            
            if not available_tags:
                logger.warning(f"No available tags found for facet {facet}, using mock tags")
                return self._generate_mock_tags(subcategory, num_questions)
            
            # Randomly select tags
            selected_tags = random.sample(available_tags, min(num_questions, len(available_tags)))
            
            logger.info(f"Retrieved {len(selected_tags)} tags for facet {facet}")
            return selected_tags
            
        except Exception as e:
            logger.error(f"Error getting tags for facet {facet}: {str(e)}")
            return self._generate_mock_tags(subcategory, num_questions)
    
    def _generate_mock_tags(self, subcategory: str, num_tags: int) -> List[str]:
        """
        Generate mock tags based on subcategory for fallback.

        """
        tag_mapping = {
            'algebra': ['linear_equations', 'quadratic_equations', 'polynomials', 'factoring', 
                        'inequalities', 'systems', 'functions', 'graphing', 'slopes', 'intercepts',
                        'domain_range', 'composition', 'inverse_functions', 'exponentials', 'logarithms'],
            'data analysis': ['statistics', 'probability', 'mean_median_mode', 'standard_deviation',
                            'correlation', 'scatter_plots', 'histograms', 'box_plots', 'sampling',
                            'confidence_intervals', 'hypothesis_testing', 'distributions', 'percentiles',
                            'margin_error', 'surveys'],
            'grammar': ['subject_verb_agreement', 'pronouns', 'modifiers', 'punctuation',
                        'comma_usage', 'semicolons', 'apostrophes', 'parallel_structure',
                        'sentence_fragments', 'run_on_sentences', 'verb_tenses', 'active_passive',
                        'clauses', 'phrases', 'conjunctions'],
            'vocabulary': ['context_clues', 'word_meanings', 'synonyms', 'antonyms', 'prefixes',
                           'suffixes', 'root_words', 'figurative_language', 'tone', 'connotation',
                           'denotation', 'analogies', 'word_relationships', 'academic_vocabulary',
                           'literary_terms']
        }
        
        # Find matching tags or use generic ones
        available_tags = []
        for key, tags in tag_mapping.items():
            if key.lower() in subcategory.lower():
                available_tags = tags
                break
        
        if not available_tags:
            available_tags = [f"general_tag_{i}" for i in range(1, 21)]
        
        return random.sample(available_tags, min(num_tags, len(available_tags)))
    
    def get_facet_metadata(self, facet: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific facet.

        """
        try:
            metadata = self.get_metadata()
            if not metadata:
                return None
            
            facets = metadata.get('facets', {})
            return facets.get(facet)
            
        except Exception as e:
            logger.error(f"Error getting facet metadata for {facet}: {str(e)}")
            return None
    
    def get_available_facets(self) -> List[str]:
        """
        Get list of all available facets.
        """
        try:
            metadata = self.get_metadata()
            if not metadata:
                return []
            
            facets = metadata.get('facets', {})
            return list(facets.keys())
            
        except Exception as e:
            logger.error(f"Error getting available facets: {str(e)}")
            return []

# --- Convenience functions (UNCHANGED) ---

_question_db_instance = None

def get_question_db() -> QuestionDatabase:
    """Get singleton instance of QuestionDatabase"""
    global _question_db_instance
    if _question_db_instance is None:
        _question_db_instance = QuestionDatabase()
    return _question_db_instance

# Legacy function wrappers for backward compatibility
def _getMetaData() -> Optional[Dict[str, Any]]:
    """Legacy wrapper for get_metadata"""
    return get_question_db().get_metadata()

def _getQuestions(attributes: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Legacy wrapper for get_questions"""
    return get_question_db().get_questions(attributes)

def getQuestionFromId(question_id: str) -> Optional[Dict[str, Any]]:
    """Legacy wrapper for get_question_by_id"""
    return get_question_db().get_question_by_id(question_id)