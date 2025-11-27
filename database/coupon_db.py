"""
Coupon database operations
Handles all database interactions related to coupons
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from database.firebase_client import get_firestore_client
from models.coupon_schema import Coupon

logger = logging.getLogger(__name__)

class CouponDatabase:
	"""Database operations for coupon management"""
	
	def __init__(self):
		self.db = get_firestore_client()
	
	def _check_connection(self) -> bool:
		"""Check if database connection is available"""
		if self.db is None:
			logger.error("Firestore client is not initialized")
			return False
		return True
	
	def _coupon_to_firestore(self, coupon: Coupon) -> Dict[str, Any]:
		"""Convert Coupon object to Firestore-compatible dictionary"""
		data = coupon.to_dict()
		# Convert datetime to ISO string for Firestore
		if isinstance(data['expiry_date'], datetime):
			data['expiry_date'] = data['expiry_date'].isoformat()
		return data
	
	def _firestore_to_coupon(self, data: Dict[str, Any]) -> Coupon:
		"""Convert Firestore dictionary to Coupon object"""
		# Convert ISO string back to datetime if needed
		if isinstance(data.get('expiry_date'), str):
			data['expiry_date'] = datetime.fromisoformat(data['expiry_date'])
		return Coupon.from_dict(data)
	
	def get_coupons(self) -> List[Coupon]:
		"""Get all coupons"""
		try:
			if self.db is None:
				logger.error("Firestore client is not initialized")
				return []
				
			coupons_collection = self.db.collection('coupons')
			docs = coupons_collection.stream()
			coupons_list = []
			
			for doc in docs:
				coupon_data = doc.to_dict()
				coupon_data['coupon_id'] = doc.id  # Use document ID as coupon_id
				try:
					coupon = self._firestore_to_coupon(coupon_data)
					coupons_list.append(coupon)
				except Exception as e:
					logger.error(f"Error parsing coupon {doc.id}: {str(e)}")
					continue
			
			logger.info(f"Retrieved {len(coupons_list)} coupons")
			return coupons_list
			
		except Exception as e:
			logger.error(f"Error getting coupons: {str(e)}")
			return []
	
	def get_coupon_by_id(self, coupon_id: str) -> Optional[Coupon]:
		"""Get a coupon by its ID"""
		try:
			if self.db is None:
				logger.error("Firestore client is not initialized")
				return None
				
			doc_ref = self.db.collection('coupons').document(coupon_id)
			doc = doc_ref.get()
			
			if doc.exists:
				coupon_data = doc.to_dict()
				if coupon_data is not None:
					coupon_data['coupon_id'] = doc.id
					return self._firestore_to_coupon(coupon_data)
			
			logger.info(f"Coupon not found: {coupon_id}")
			return None
			
		except Exception as e:
			logger.error(f"Error getting coupon {coupon_id}: {str(e)}")
			return None
	
		"""Get a coupon by its name"""
		try:
			if self.db is None:
				logger.error("Firestore client is not initialized")
				return None
				
			coupons_collection = self.db.collection('coupons').where('coupon_name', '==', coupon_name.upper())
			docs = coupons_collection.limit(1).stream()
			
			for doc in docs:
				coupon_data = doc.to_dict()
				coupon_data['coupon_id'] = doc.id
				return self._firestore_to_coupon(coupon_data)
			
			logger.info(f"Coupon not found with name: {coupon_name}")
			return None
			
		except Exception as e:
			logger.error(f"Error getting coupon by name {coupon_name}: {str(e)}")
			return None
	
	def create_coupon(self, coupon: Coupon) -> bool:
		"""Create a new coupon"""
		try:
			# Convert coupon to Firestore format
			coupon_data = self._coupon_to_firestore(coupon)
			
			# Normalize coupon name to uppercase
			coupon_data['coupon_name'] = coupon_data['coupon_name'].upper()
			
			# Use coupon_id as document ID
			self.db.collection('coupons').document(coupon.coupon_id).set(coupon_data)
			
			logger.info(f"Successfully created coupon: {coupon.coupon_id}")
			return True
			
		except Exception as e:
			logger.error(f"Error creating coupon: {str(e)}")
			return False
	
	def update_coupon(self, coupon_id: str, coupon: Coupon) -> bool:
		"""Update an existing coupon"""
		try:
			# Convert coupon to Firestore format
			coupon_data = self._coupon_to_firestore(coupon)
			
			# Normalize coupon name if present
			if 'coupon_name' in coupon_data:
				coupon_data['coupon_name'] = coupon_data['coupon_name'].upper()
			
			doc_ref = self.db.collection('coupons').document(coupon_id)
			doc_ref.set(coupon_data, merge=True)
			
			logger.info(f"Successfully updated coupon: {coupon_id}")
			return True
			
		except Exception as e:
			logger.error(f"Error updating coupon {coupon_id}: {str(e)}")
			return False
	
	def delete_coupon(self, coupon_id: str) -> bool:
		"""Delete a coupon (hard delete)"""
		try:
			doc_ref = self.db.collection('coupons').document(coupon_id)
			doc_ref.delete()
			
			logger.info(f"Successfully deleted coupon: {coupon_id}")
			return True
			
		except Exception as e:
			logger.error(f"Error deleting coupon {coupon_id}: {str(e)}")
			return False

# Convenience functions for backward compatibility and easy access
_coupon_db_instance = None

def get_coupon_db() -> CouponDatabase:
	"""Get singleton instance of CouponDatabase"""
	global _coupon_db_instance
	if _coupon_db_instance is None:
		_coupon_db_instance = CouponDatabase()
	return _coupon_db_instance

# Legacy function wrappers for backward compatibility (returning dicts)
def getCoupons(active_only: bool = True) -> List[Dict[str, Any]]:
	"""Legacy wrapper for get_coupons - returns dictionaries"""
	coupons = get_coupon_db().get_coupons()
	return [coupon.to_dict() for coupon in coupons]

def getCouponById(coupon_id: str) -> Optional[Dict[str, Any]]:
	"""Legacy wrapper for get_coupon_by_id - returns dictionary"""
	coupon = get_coupon_db().get_coupon_by_id(coupon_id)
	return coupon.to_dict() if coupon else None

def createCoupon(coupon_data: Dict[str, Any]) -> bool:
	"""Legacy wrapper for create_coupon - accepts dictionary"""
	try:
		coupon = Coupon.from_dict(coupon_data)
		return get_coupon_db().create_coupon(coupon)
	except Exception as e:
		logger.error(f"Error creating coupon from dict: {str(e)}")
		return False

def updateCoupon(coupon_id: str, coupon_data: Dict[str, Any]) -> bool:
    """Legacy wrapper for update_coupon - accepts dictionary"""
    try:
        coupon = Coupon.from_dict(coupon_data)
        return get_coupon_db().update_coupon(coupon_id, coupon)
    except Exception as e:
        logger.error(f"Error updating coupon from dict: {str(e)}")
        return False
    
def deleteCoupon(coupon_id: str) -> bool:
    """Legacy wrapper for delete_coupon"""
    return get_coupon_db().delete_coupon(coupon_id)

