from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, Dict
from models.users_schema import PlanType


@dataclass
class Coupon:
    coupon_id: str
    coupon_name: str
    coupon_description: str
    discount_percentage: float
    max_usage: Dict[PlanType, int] = field(default_factory=dict)
    current_usage: Dict[PlanType, int] = field(default_factory=dict)
    expiry_date: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "coupon_id": self.coupon_id,
            "coupon_name": self.coupon_name,
            "coupon_description": self.coupon_description,
            "discount_percentage": self.discount_percentage,

            # Convert Enum keys to strings
            "max_usage": {k.value: v for k, v in self.max_usage.items()},
            "current_usage": {k.value: v for k, v in self.current_usage.items()},

            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
        }

    @classmethod
    def from_dict(cls, data: dict):
        expiry_date = data.get("expiry_date")
        if isinstance(expiry_date, str):
            expiry_date = datetime.fromisoformat(expiry_date)

        # Convert string keys back to Enums
        max_usage = {
            PlanType(k): v for k, v in data.get("max_usage", {}).items()
        }
        current_usage = {
            PlanType(k): v for k, v in data.get("current_usage", {}).items()
        }

        return cls(
            coupon_id=data["coupon_id"],
            coupon_name=data["coupon_name"],
            coupon_description=data["coupon_description"],
            discount_percentage=data["discount_percentage"],
            max_usage=max_usage,
            current_usage=current_usage,
            expiry_date=expiry_date,
        )
