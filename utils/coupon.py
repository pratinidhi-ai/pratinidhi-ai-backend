from database.coupon_db import get_coupon_db 
from models.users_schema import PlanType
from models.coupon_schema import Coupon
import logging
from datetime import datetime, timezone
from typing import Dict

logger = logging.getLogger(__name__)

def get_validation_status(coupon: Coupon) -> tuple[Dict[PlanType,bool], str]:
    try:
        coupon_db = get_coupon_db()
        
        planTypeValidations = {
            PlanType.MONTHLY: False,
            PlanType.YEARLY: False,
        }

        coupon = coupon_db.get_coupon_by_id(coupon.coupon_id)
        if not coupon:
            return planTypeValidations, "Coupon not found"
        
        if coupon.expiry_date and coupon.expiry_date < datetime.now(timezone.utc):
            return planTypeValidations, "Coupon has expired"
        
        for planType in planTypeValidations.keys():
            if coupon.current_usage[planType]+1 < coupon.max_usage[planType]:
                planTypeValidations[planType] = True
        
        
        return planTypeValidations, "Coupon is valid"
        
    except Exception as e:
        logger.error(f"Error validating coupon {coupon.coupon_id}: {str(e)}")
        return False, f"Error validating coupon: {str(e)}"

def apply_coupon(coupon_id: str):
    try:
        if not coupon_id:
            return
        
        coupon_db = get_coupon_db()
        coupon = coupon_db.get_coupon_by_id(coupon_id)
        if not coupon:
            logger.error(f"Coupon with ID {coupon_id} not found for application")
            return
        
        coupon.current_usage += 1
        coupon_db.update_coupon(coupon_id, coupon)
        logger.info(f"Coupon {coupon_id} applied successfully in background task")
        
    except Exception as e:
        logger.error(f"Error applying coupon {coupon_id}: {str(e)}")
