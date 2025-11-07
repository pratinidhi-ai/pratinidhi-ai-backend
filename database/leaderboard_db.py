"""
Leaderboard Database Operations
Handles all leaderboard-related database interactions
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union

from database.firebase_client import get_firestore_client
from models.leaderboard_schema import LeaderboardEntity, PerformanceMetric, Region

logger = logging.getLogger(__name__)


class LeaderboardDatabase:
    """Database operations for leaderboard management"""
    
    def __init__(self):
        self.db = get_firestore_client()
    
    def _check_connection(self) -> bool:
        """Check if database connection is available"""
        if self.db is None:
            logger.error("Firestore client is not initialized")
            return False
        return True
    
    def get_leaderboard_entity(
        self,
        user_id: Optional[str] = None,
        limit: Optional[int] = 100,
        country: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        sort_by: str = 'rating',
        sort_order: str = 'desc'
    ) -> Union[LeaderboardEntity, List[Dict[str, Any]], None]:
        """
        Get leaderboard entity/entities with flexible filtering and sorting
        
        Args:
            user_id: If provided, returns single entity for this user (ignores other params)
            limit: Maximum number of entries to return (default 100, None for all)
            country: Filter by country
            state: Filter by state (requires country)
            city: Filter by city (requires state and country)
            sort_by: Sort by metric - 'rating', 'score', 'correct_questions', 'total_quiz' (default 'rating')
            sort_order: Sort order - 'desc' or 'asc' (default 'desc')
            
        Returns:
            - If user_id provided: Single LeaderboardEntity or None
            - Otherwise: List of leaderboard dictionaries with rankings
        """
        try:
            if not self._check_connection():
                return None if user_id else []
            
            # If user_id is provided, get single entity
            if user_id:
                return self._get_single_entity(user_id)
            
            # Otherwise, get filtered and sorted list
            return self._get_filtered_entities(
                limit=limit,
                country=country,
                state=state,
                city=city,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
        except Exception as e:
            logger.error(f"Error in get_leaderboard_entity: {str(e)}")
            import traceback
            traceback.print_exc()
            return None if user_id else []
    
    def _get_single_entity(self, user_id: str) -> Optional[LeaderboardEntity]:
        """
        Internal method to get a single leaderboard entity by user_id
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            LeaderboardEntity object or None if not found
        """
        try:
            doc_ref = self.db.collection('leaderboard').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                logger.info(f"Retrieved leaderboard entity for user {user_id}")
                return LeaderboardEntity.from_dict(doc.to_dict())
            
            logger.info(f"No leaderboard entity found for user {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting single entity for {user_id}: {str(e)}")
            return None
    
    def _get_filtered_entities(
        self,
        limit: Optional[int],
        country: Optional[str],
        state: Optional[str],
        city: Optional[str],
        sort_by: str,
        sort_order: str
    ) -> List[Dict[str, Any]]:
        """
        Internal method to get filtered and sorted leaderboard entities
        
        Args:
            limit: Maximum number of entries
            country: Filter by country
            state: Filter by state
            city: Filter by city
            sort_by: Sort by metric
            sort_order: Sort order
            
        Returns:
            List of leaderboard dictionaries with rankings
        """
        try:
            # Build query with filters
            query = self.db.collection('leaderboard')
            
            # Apply regional filters
            if country:
                query = query.where('region.country', '==', country)
                logger.debug(f"Applied country filter: {country}")
            
            if state and country:
                query = query.where('region.state', '==', state)
                logger.debug(f"Applied state filter: {state}")
            
            if city and state and country:
                query = query.where('region.city', '==', city)
                logger.debug(f"Applied city filter: {city}")
            
            # Map sort_by to field path
            field_map = {
                'rating': 'performance_metric.rating',
                'score': 'performance_metric.score',
                'correct_questions': 'performance_metric.correct_questions',
                'total_quiz': 'performance_metric.total_quiz',
                'total_questions': 'performance_metric.total_questions'
            }
            
            field_name = field_map.get(sort_by, 'performance_metric.rating')
            
            # Apply sorting
            direction = 'DESCENDING' if sort_order.lower() == 'desc' else 'ASCENDING'
            query = query.order_by(field_name, direction=direction)
            
            # Apply limit if specified
            if limit is not None and limit > 0:
                query = query.limit(limit)
            
            # Execute query
            docs = query.stream()
            
            # Build leaderboard list
            leaderboard = []
            rank = 1
            
            for doc in docs:
                entity_data = doc.to_dict()
                entity_data['rank'] = rank
                
                # Add calculated accuracy
                perf = entity_data.get('performance_metric', {})
                if perf.get('total_questions', 0) > 0:
                    accuracy = (perf['correct_questions'] / perf['total_questions']) * 100
                    entity_data['accuracy'] = round(accuracy, 2)
                else:
                    entity_data['accuracy'] = 0.0
                
                leaderboard.append(entity_data)
                rank += 1
            
            # Build location string for logging
            location_parts = []
            if city:
                location_parts.append(city)
            if state:
                location_parts.append(state)
            if country:
                location_parts.append(country)
            location = ', '.join(location_parts) if location_parts else 'Global'
            
            logger.info(f"Retrieved {location} leaderboard: {len(leaderboard)} entries, sorted by {sort_by} ({sort_order})")
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting filtered entities: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    # def update_entity(self, entity: LeaderboardEntity) -> bool:
    #     """
    #     Update an existing leaderboard entity
        
    #     Args:
    #         entity: LeaderboardEntity object with updated data
            
    #     Returns:
    #         bool: Success status
    #     """
    #     try:
    #         if not self._check_connection():
    #             return False
            
    #         # Check if entity exists
    #         doc_ref = self.db.collection('leaderboard').document(entity.user_id)
    #         doc = doc_ref.get()
            
    #         if not doc.exists:
    #             logger.error(f"Cannot update: Leaderboard entity not found for user {entity.user_id}")
    #             return False
            
    #         # Update timestamp
    #         entity.updated_at = datetime.now(timezone.utc)
            
    #         # Update in Firestore
    #         doc_ref.set(entity.to_dict())
            
    #         logger.info(f"Successfully updated leaderboard entity for user {entity.user_id}")
    #         return True
            
    #     except Exception as e:
    #         logger.error(f"Error updating leaderboard entity: {str(e)}")
    #         import traceback
    #         traceback.print_exc()
    #         return False
    
    # def create_entity(self, entity: LeaderboardEntity) -> bool:
    #     """
    #     Create a new leaderboard entity
        
    #     Args:
    #         entity: LeaderboardEntity object
            
    #     Returns:
    #         bool: Success status
    #     """
    #     try:
    #         if not self._check_connection():
    #             return False
            
    #         # Check if entity already exists
    #         doc_ref = self.db.collection('leaderboard').document(entity.user_id)
    #         doc = doc_ref.get()
            
    #         if doc.exists:
    #             logger.warning(f"Entity already exists for user {entity.user_id}. Use update_entity() instead.")
    #             return False
            
    #         # Set timestamps
    #         entity.created_at = datetime.now(timezone.utc)
    #         entity.updated_at = datetime.now(timezone.utc)
            
    #         # Save to Firestore
    #         doc_ref.set(entity.to_dict())
            
    #         logger.info(f"Successfully created leaderboard entity for user {entity.user_id}")
    #         return True
            
    #     except Exception as e:
    #         logger.error(f"Error creating leaderboard entity: {str(e)}")
    #         import traceback
    #         traceback.print_exc()
    #         return False
    
    def create_or_update_entity(self, entity: LeaderboardEntity) -> bool:
        """
        Create or update a leaderboard entity
        
        Args:
            entity: LeaderboardEntity object
            
        Returns:
            bool: Success status
        """
        try:
            if not self._check_connection():
                return False
            
            leaderboard_ref = self.db.collection('leaderboard').document(entity.user_id)
            
            # Check if entity exists
            existing_doc = leaderboard_ref.get()
            
            if existing_doc.exists:
                entity.updated_at = datetime.now(timezone.utc)
                logger.info(f"Updating existing entity for user {entity.user_id}")
            else:
                entity.created_at = datetime.now(timezone.utc)
                entity.updated_at = datetime.now(timezone.utc)
                logger.info(f"Creating new entity for user {entity.user_id}")
            
            # Save to Firestore
            leaderboard_ref.set(entity.to_dict())
            
            logger.info(f"Successfully saved leaderboard entity for user {entity.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error in create_or_update_entity: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def delete_entity(self, user_id: str) -> bool:
        """
        Delete a user's leaderboard entity
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            bool: Success status
        """
        try:
            if not self._check_connection():
                return False
            
            doc_ref = self.db.collection('leaderboard').document(user_id)
            doc_ref.delete()
            
            logger.info(f"Deleted leaderboard entity for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting leaderboard entity for {user_id}: {str(e)}")
            return False
    
    def get_user_rank(
        self,
        user_id: str,
        sort_by: str = 'rating',
        country: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get user's rank in the leaderboard with optional regional filtering
        
        Args:
            user_id: User's unique identifier
            sort_by: Metric to rank by ('rating', 'score', 'correct_questions')
            country: Filter by country
            state: Filter by state
            city: Filter by city
            
        Returns:
            Dictionary with rank information or None
        """
        try:
            if not self._check_connection():
                return None
            
            # Get user's entity
            user_entity = self.get_leaderboard_entity(user_id=user_id)
            
            if not user_entity:
                return None
            
            # If regional filters not provided, use user's region
            if not country and user_entity.region:
                country = user_entity.region.country if city or state else None
                state = user_entity.region.state if city else None
                city = user_entity.region.city if city else None
            
            # Get leaderboard with same filters
            leaderboard = self.get_leaderboard_entity(
                limit=None,
                country=country,
                state=state,
                city=city,
                sort_by=sort_by,
                sort_order='desc'
            )
            
            # Find user's rank
            rank = None
            for entry in leaderboard:
                if entry['user_id'] == user_id:
                    rank = entry['rank']
                    break
            
            if rank is None:
                logger.warning(f"User {user_id} not found in leaderboard")
                return None
            
            # Build scope string
            scope_parts = []
            if city:
                scope_parts.append(city)
            if state:
                scope_parts.append(state)
            if country:
                scope_parts.append(country)
            scope = ', '.join(scope_parts) if scope_parts else 'Global'
            
            return {
                'user_id': user_id,
                'rank': rank,
                'total_users': len(leaderboard),
                'scope': scope,
                'sort_by': sort_by,
                'rating': user_entity.performance_metric.rating,
                'score': user_entity.performance_metric.score,
                'correct_questions': user_entity.performance_metric.correct_questions,
                'total_questions': user_entity.performance_metric.total_questions,
                'total_quiz': user_entity.performance_metric.total_quiz,
                'accuracy': user_entity.performance_metric.calculate_accuracy(),
                'region': user_entity.region.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error getting user rank for {user_id}: {str(e)}")
            return None


# Singleton instance
_leaderboard_db_instance = None


def get_leaderboard_db() -> LeaderboardDatabase:
    """Get singleton instance of LeaderboardDatabase"""
    global _leaderboard_db_instance
    if _leaderboard_db_instance is None:
        _leaderboard_db_instance = LeaderboardDatabase()
    return _leaderboard_db_instance