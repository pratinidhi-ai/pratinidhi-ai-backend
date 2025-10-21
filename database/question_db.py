"""
Question database operations
Handles all database interactions related to questions and question banks
"""

import logging
import random
from typing import List, Dict, Any, Optional
from database.firebase_client import get_firestore_client

logger = logging.getLogger(__name__)

class QuestionDatabase:
	"""Database operations for question management"""
	
	def __init__(self):
		self.db = get_firestore_client()
	
	def get_metadata(self) -> Optional[Dict[str, Any]]:
		"""Get question bank metadata"""
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
		Get questions based on provided attributes
		
		Args:
			attributes: Dictionary containing:
				- subject: Subject name
				- subcategory: Subcategory name  
				- standard: Grade/standard
				- difficulty: Difficulty level
				- nques: Number of questions (optional, default 5)
				- tags: Specific tags (optional)
				- exam: Specific exam (optional)
		"""
		nques = attributes.get('nques', 5)
		
		# Validate and convert nques to int
		try:
			nques = int(nques) if nques is not None else 5
		except (ValueError, TypeError):
			nques = 5
			logger.warning("Invalid nques value, defaulting to 5")
		
		try:
			# Build the path based on attributes
			sub_path = f"{attributes['subject']}|{attributes['subcategory']}|{attributes['standard']}"
			
			# Determine collection reference based on attributes
			collection_ref = self._build_question_collection_ref(sub_path, attributes)
			
			# Get random questions using rand field
			rand_value = random.random()
			query_random = (collection_ref
						   .where("rand", ">=", rand_value)
						   .order_by("rand")
						   .limit(nques))
			
			docs_random = list(query_random.stream())
			result = []
			
			# Get questions from the random docs
			for doc in docs_random:
				question = self.get_question_by_id(doc.to_dict()['question_id'])
				if question:
					result.append(question)
			
			# If we don't have enough questions, get more with fallback query
			if len(result) < nques:
				remaining_needed = nques - len(result)
				query_fallback = (collection_ref
								 .where("rand", "<", rand_value)
								 .order_by("rand")
								 .limit(remaining_needed))
				
				docs_fallback = list(query_fallback.stream())
				
				for doc in docs_fallback:
					question = self.get_question_by_id(doc.to_dict()['question_id'])
					if question:
						result.append(question)
			
			logger.info(f"Retrieved {len(result)} questions for query: {attributes}")
			return result 
			
		except Exception as e:
			logger.error(f"Error getting questions: {str(e)}")
			return []
	
	def _build_question_collection_ref(self, sub_path: str, attributes: Dict[str, Any]):
		"""Build Firestore collection reference based on query attributes"""
		if self.db is None:
			logger.error("Firestore client is not initialized in _build_question_collection_ref.")
			raise ValueError("Firestore client is not initialized.")
		base_ref = (self.db.collection('question_bank')
				   .document(sub_path)
				   .collection('difficulty')
				   .document(attributes['difficulty']))
		
		# Handle tags and exam combinations
		tags = attributes.get('tags')
		exam = attributes.get('exam')
		
		if not tags:  # No specific tags
			if not exam:  # No specific exam
				return (base_ref
					   .collection('all')
					   .document('members')
					   .collection('items'))
			else:  # Has exam, no tags
				return (base_ref
					   .collection('by_exam')
					   .document(exam)
					   .collection('members'))
		else:  # Has specific tags
			if not exam:  # Has tags, no exam
				return (base_ref
					   .collection('tags')
					   .document(tags)
					   .collection('members'))
			else:  # Has both tags and exam
				return (base_ref
					   .collection('tags')
					   .document(tags)
					   .collection('by_exam')
					   .document(exam)
					   .collection('members'))
	
	def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
		"""Get a specific question by its ID"""
		try:
			if self.db is None:
				logger.error("Firestore client is not initialized in _build_question_collection_ref.")
				raise ValueError("Firestore client is not initialized.")
			doc_ref = self.db.collection('questions').document(question_id)
			doc = doc_ref.get()
			
			if doc.exists:
				question_data = doc.to_dict()
				if question_data is not None:
					question_data['id'] = doc.id  # Ensure ID is included
					return question_data
				else:
					logger.warning(f"Document {question_id} exists but contains no data.")
					return None
			
			logger.warning(f"Question not found: {question_id}")
			return None
			
		except Exception as e:
			logger.error(f"Error getting question {question_id}: {str(e)}")
			return None

		
	def get_random_tags_by_facets(self, facets: str, num_tags: int = 10) -> List[str]:
		"""
		Get random tags based on provided facets
		In the question_bank collection, each facet has a doc, which contains available_tags
		"""
		try:
			if self.db is None:
				logger.error("Firestore client is not initialized in get_random_tags_by_facets.")
				raise ValueError("Firestore client is not initialized.")

			# Get the document for the specified facets
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
		Get available question tags for a specific facet
		This is used for task assignment
		
		Args:
			facet: Facet string like "math|algebra|11"
			num_questions: Number of question tags to return
			
		Returns:
			List of question tag strings
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
			# This assumes metadata has a structure like:
			# { "facets": { "math|algebra|11": { "available_tags": [...] } } }
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
		"""Generate mock tags based on subcategory for fallback"""
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
		"""Get metadata for a specific facet"""
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
		"""Get list of all available facets"""
		try:
			metadata = self.get_metadata()
			if not metadata:
				return []
			
			facets = metadata.get('facets', {})
			return list(facets.keys())
			
		except Exception as e:
			logger.error(f"Error getting available facets: {str(e)}")
			return []

# Convenience functions for backward compatibility and easy access
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