from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

@dataclass
class Coupon:
    coupon_id: str 
    coupon_name: str
    coupon_description: str
    discount_percentage: float
    max_usage: int
    current_usage: int = 0
    expiry_date: datetime = None
    total_discount_given: float = 0.0
    vendor_share_percent: float = 0.0
    vendor_share_amount: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "coupon_id": self.coupon_id,
            "coupon_name": self.coupon_name,
            "coupon_description": self.coupon_description,
            "discount_percentage": self.discount_percentage,
            "max_usage": self.max_usage,
            "current_usage": self.current_usage,
            "expiry_date": self.expiry_date.isoformat() if isinstance(self.expiry_date, datetime) else self.expiry_date,
            "total_discount_given": self.total_discount_given,
            "vendor_share_percent": self.vendor_share_percent,
            "vendor_share_amount": self.vendor_share_amount
        }

    @classmethod
    def from_dict(cls, data: dict):
        # Handle datetime conversion
        expiry_date = data.get("expiry_date")
        if isinstance(expiry_date, str):
            expiry_date = datetime.fromisoformat(expiry_date)
        elif expiry_date is None:
            expiry_date = datetime.now(timezone.utc)
        
        return cls(
            coupon_id=data["coupon_id"],
            coupon_name=data["coupon_name"],
            coupon_description=data["coupon_description"],
            discount_percentage=data["discount_percentage"],
            max_usage=data["max_usage"],
            current_usage=data.get("current_usage", 0),
            expiry_date=expiry_date,
            total_discount_given=data.get("total_discount_given", 0.0),
            vendor_share_percent=data.get("vendor_share_percent", 0.0),
            vendor_share_amount=data.get("vendor_share_amount", 0.0)
        )
    
    def is_valid(self) -> tuple[bool, Optional[str]]:
        """Check if coupon is valid for use"""
        if datetime.now(timezone.utc) > self.expiry_date.replace(tzinfo=timezone.utc):
            return False, "Coupon has expired"
        
        if self.current_usage >= self.max_usage:
            return False, "Coupon usage limit reached"
        
        return True, None
    
    def calculate_discount(self, order_amount: float) -> dict:
        """Calculate discount details for an order"""
        discount_amount = order_amount * (self.discount_percentage / 100)
        vendor_share = discount_amount * (self.vendor_share_percent / 100)
        final_amount = order_amount - discount_amount
        
        return {
            "original_amount": order_amount,
            "discount_amount": discount_amount,
            "vendor_share": vendor_share,
            "final_amount": final_amount,
            "discount_percentage": self.discount_percentage
        }
