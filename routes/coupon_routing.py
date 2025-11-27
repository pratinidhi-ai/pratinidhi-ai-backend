from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional
from datetime import datetime, timezone
import logging
from pydantic import BaseModel

from models.coupon_schema import Coupon
from database.coupon_db import get_coupon_db
from helper.middleware import authenticate_request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/coupons", tags=["coupons"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=dict)
def create_coupon(coupon: Coupon, user: dict = Depends(authenticate_request)):
    """
    Create a new coupon
    """
    try:
        # Check if coupon already exists
        existing = get_coupon_db().get_coupon_by_id(coupon.coupon_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Coupon with ID {coupon.coupon_id} already exists"
            )
        
        success = get_coupon_db().create_coupon(coupon)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create coupon"
            )
        
        return {
            "success": True,
            "message": "Coupon created successfully",
            "coupon_id": coupon.coupon_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating coupon: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating coupon: {str(e)}"
        )

@router.get("/", status_code=status.HTTP_200_OK, response_model=List[dict])
def get_all_coupons(active_only: bool = Query(False, description="Filter only active coupons"), user: dict = Depends(authenticate_request)):
    """
    Get all coupons with optional filter for active coupons only
    """
    try:
        coupons = get_coupon_db().get_coupons()
        
        if active_only:
            current_time = datetime.now(timezone.utc)
            coupons = [
                c for c in coupons 
                if c.current_usage < c.max_usage and 
                c.expiry_date.replace(tzinfo=timezone.utc) > current_time
            ]
        
        return [coupon.to_dict() for coupon in coupons]
    except Exception as e:
        logger.error(f"Error getting coupons: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving coupons: {str(e)}"
        )

@router.get("/{coupon_id}", status_code=status.HTTP_200_OK, response_model=dict)
def get_coupon_by_id(coupon_id: str, user: dict = Depends(authenticate_request)):
    """
    Get a specific coupon by ID
    """
    try:
        coupon = get_coupon_db().get_coupon_by_id(coupon_id)
        if not coupon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Coupon with ID {coupon_id} not found"
            )
        
        return coupon.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting coupon {coupon_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving coupon: {str(e)}"
        )

@router.post("/validate/{coupon_id}", status_code=status.HTTP_200_OK, response_model=dict)
def validate_coupon(coupon_id: str, user: dict = Depends(authenticate_request)):
    """
    Validate a coupon and return its details if valid
    """
    try:
        coupon = get_coupon_db().get_coupon_by_id(coupon_id)
        if not coupon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Coupon with ID {coupon_id} not found"
            )
        
        is_valid, error_message = coupon.is_valid()
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        return {
            "valid": True,
            "message": "Coupon is valid",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating coupon {coupon_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating coupon: {str(e)}"
        )

@router.put("/{coupon_id}", status_code=status.HTTP_200_OK, response_model=dict)
def update_coupon(coupon_id: str, coupon: Coupon, user: dict = Depends(authenticate_request)):
    """
    Update an existing coupon
    """
    try:
        # Check if coupon exists
        existing = get_coupon_db().get_coupon_by_id(coupon_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Coupon with ID {coupon_id} not found"
            )
        
        # Ensure the coupon_id in the body matches the path parameter
        coupon.coupon_id = coupon_id
        
        success = get_coupon_db().update_coupon(coupon_id, coupon)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update coupon"
            )
        
        return {
            "success": True,
            "message": "Coupon updated successfully",
            "coupon_id": coupon_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating coupon {coupon_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating coupon: {str(e)}"
        )

@router.delete("/{coupon_id}", status_code=status.HTTP_200_OK, response_model=dict)
def delete_coupon(coupon_id: str, user: dict = Depends(authenticate_request)):
    """
    Delete a coupon
    """
    try:
        # Check if coupon exists
        existing = get_coupon_db().get_coupon_by_id(coupon_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Coupon with ID {coupon_id} not found"
            )
        
        success = get_coupon_db().delete_coupon(coupon_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete coupon"
            )
        
        return {
            "success": True,
            "message": "Coupon deleted successfully",
            "coupon_id": coupon_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting coupon {coupon_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting coupon: {str(e)}"
        )

@router.post("/apply/{coupon_id}", status_code=status.HTTP_200_OK, response_model=dict)
def apply_coupon(coupon_id: str, user: dict = Depends(authenticate_request)):
    """
    Apply a coupon to an order - validates and updates coupon state
    """
    try:
        # Check if coupon exists
        coupon = get_coupon_db().get_coupon_by_id(coupon_id)
        if not coupon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Coupon with ID {coupon_id} not found"
            )
        
        # Validate the coupon
        is_valid, error_message = coupon.is_valid()
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        return {
            "discount_percentage": coupon.discount_percentage,
            "message": "Coupon applied successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying coupon {coupon_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error applying coupon: {str(e)}"
        )

