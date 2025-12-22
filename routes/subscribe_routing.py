from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from pydantic import BaseModel
import razorpay
import os
from helper.middleware import authenticate_request
from database.user_db import getUserbyId, get_user_db
from models.users_schema import SubscriptionType, PlanType
from datetime import datetime, timedelta, timezone
import logging
import hashlib
import math
from utils.users import validate_user_id, get_user, update_user
from utils.coupon import apply_coupon
from utils.datetime_utils import parse_datetime  
router = APIRouter(prefix='/api/subscription', tags=["subscription"])

def parse_expiry_date(expiry_date) -> datetime | None:
    """Parse pro_expiry_date from various formats to datetime object"""
    if expiry_date is None:
        return None
    if isinstance(expiry_date, datetime):
        return expiry_date
    if isinstance(expiry_date, str):
        return datetime.fromisoformat(expiry_date)
    return None
logger = logging.getLogger(__name__)

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(
    os.getenv('RAZORPAY_KEY_ID'),
    os.getenv('RAZORPAY_KEY_SECRET')
))

class PlanDetails(BaseModel):
    amount: int
    period: str
    interval: int
    currency: str

FREE_TRIAL_DAYS = 14
MONTHLY_DAYS = 30
YEARLY_DAYS = 365
SECONDS_PER_DAY = 86400

# Subscription plans configuration
SUBSCRIPTION_PLANS = {
    PlanType.MONTHLY.value : PlanDetails(
        amount=99900,  
        period='monthly',
        interval=1,
        currency='INR'
    ),
    PlanType.YEARLY.value : PlanDetails(
        amount=999900,   
        period='yearly',
        interval=1,
        currency='INR'
    ),  
}

# Response Models
class SubscriptionState(BaseModel):
    remaining_days: int
    plan_type: str
    subscription_type: str  
    all_plan_details: dict[str, PlanDetails]
    taken_free_trial: bool = False
    

# Request Models
class CreateOrderRequest(BaseModel):
    user_id: str
    plan_type: str
    discount_percentage: float | None = None

class VerifyPaymentRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: str
    user_id: str
    plan_type: str
    coupon_code: str | None = None
    
class StartFreeTrialRequest(BaseModel):
    user_id: str

@router.post('/create-order', status_code=status.HTTP_201_CREATED)
def create_order(request: CreateOrderRequest, user: dict = Depends(authenticate_request)):
    try:
        logger.info(f'Creating order for user {request.user_id} with plan {request.plan_type}')
        # Validate input
        user_id = request.user_id
        plan_type = request.plan_type.lower()
        validate_user_id(user_id)
        
        if plan_type not in ['monthly', 'yearly']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= {
                    'error': 'Invalid plan type',
                    'message': 'Plan type must be either "monthly" or "yearly"'
                }
            )
            
        # Get plan details
        plan_details = SUBSCRIPTION_PLANS[plan_type].model_copy()        
        user_hash = hashlib.md5(user_id.encode()).hexdigest()[:8]
        timestamp = int(datetime.now().timestamp())
        
        if request.discount_percentage:
            discount_amount = int(plan_details.amount * (request.discount_percentage / 100))
            plan_details.amount -= discount_amount
            logger.info(f"Applied discount of {request.discount_percentage}% for user {user_id}. New amount: {plan_details.amount}")

        # Create Razorpay order
        order_data = {
            'amount': plan_details.amount,
            'currency': plan_details.currency,
            'receipt': f'sub_{user_hash}_{timestamp}',  # e.g., sub_a1b2c3d4_1732636800 (30 chars)
            'notes': {
                'user_id': user_id,
                'subscription_type': plan_type
            }
        }
        
        order = razorpay_client.order.create(data=order_data)
        
        logger.info(f"Created order {order['id']} for user {user_id} with plan {plan_type}")
        
        return {
            'success': True,
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'key_id': os.getenv('RAZORPAY_KEY_ID'),
            'subscription_type': plan_type,
            'user_id': user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= {
                'error': 'Order creation failed',
                'message': str(e)
            }
        )

# Workflow of verify payment:
# 1. Verify payment signature using Razorpay utility
# 2. Update user subscription details in the database
# 3. If a coupon code is provided, apply the coupon in a background task
@router.post('/verify-payment', status_code=status.HTTP_200_OK)
def verify_payment(request: VerifyPaymentRequest, background_tasks: BackgroundTasks,
 user: dict = Depends(authenticate_request)):
    logger.info(f"Verifying payment for user {request.user_id} with order ID {request.order_id}")
    logger.info(f"request data: {request.dict()}")
    try:
        # Validate input
        if not all([request.order_id, request.payment_id, request.signature, request.user_id, request.plan_type]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= {
                    'error': 'Invalid request',
                    'message': 'Missing required payment verification fields (order_id, payment_id, signature, user_id, plan_type)'
                }
            )
        
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': request.order_id,
            'razorpay_payment_id': request.payment_id,
            'razorpay_signature': request.signature,
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # update user subscription details
        user = get_user(request.user_id)  
        if user.get('subscription') is None:
            user['subscription'] = {}
                
        expiry_date = parse_expiry_date(user.get('subscription', {}).get('pro_expiry_date'))
        if expiry_date is None:
            expiry_date = datetime.now(timezone.utc)
            
        # apply coupon if provided in background
        background_tasks.add_task(
            apply_coupon,
            coupon_id = request.coupon_code,
            plan_type = request.plan_type.lower()
        )
            
            
        user['subscription'] = {
            'type': SubscriptionType.PRO.value,
            'plan_type': request.plan_type.lower(),
            'pro_expiry_date': (expiry_date + timedelta(days=MONTHLY_DAYS) if request.plan_type.lower() == PlanType.MONTHLY.value else expiry_date + timedelta(days=YEARLY_DAYS)).isoformat(),
            'taken_free_trial': user.get('subscription', {}).get('taken_free_trial', False),
            'payment_detail_list': user.get('subscription', {}).get('payment_detail_list', []) + [{
                'payment_id': request.payment_id,
                'order_id': request.order_id,
                'plan_type': request.plan_type.lower(),
                'time': datetime.now(timezone.utc).isoformat()
            }]
        }
        
        update_user(request.user_id, user, 'Could not update user subscription details in the database')
        logger.info(f"Payment verified and subscription updated for user {request.user_id}")
        return {
            'success': True,
            'message': 'Payment verified successfully'
        }
        
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message ='Payment verification failed'
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= {
                'error': 'Payment verification failed',
                'message': str(e)
            }
        )


@router.post('/start-free-trial', status_code=status.HTTP_201_CREATED)
def start_free_trial(request: StartFreeTrialRequest, user: dict = Depends(authenticate_request)):
    try:
        user_id = request.user_id
        validate_user_id(user_id)
       
        user_data = get_user(user_id)    
    
        if user_data.get('subscription') is None:
            user_data['subscription'] = {}
            
        # Check if user has already taken free trial
        if user_data['subscription'].get('taken_free_trial', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= {
                    'error': 'Free trial already used',
                    'message': 'User has already taken the free trial'
                }
            )
            
        expiry_date = parse_expiry_date(user_data.get('subscription', {}).get('pro_expiry_date'))
        if expiry_date is None:
            expiry_date = datetime.now(timezone.utc)
                        
        expiry_date += timedelta(days=FREE_TRIAL_DAYS)
        
        
        current_plan = user_data['subscription'].get('plan_type')
        if current_plan == PlanType.NONE:
            current_plan = PlanType.TRIAL
        
        user_data['subscription'] = {
            'type': SubscriptionType.PRO.value,
            'plan_type': current_plan,
            'pro_expiry_date': expiry_date.isoformat(),
            'taken_free_trial': True,        
        }
        
        update_user(user_id, user_data, 'Could not update user subscription details in the database')
        
        return {
            'success': True,
            'message': 'Free trial started successfully',
            'days': FREE_TRIAL_DAYS,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= {
                'error': 'Free trial activation failed',
                'message': str(e)
            }
        )

@router.get('/state/{user_id}', status_code=status.HTTP_200_OK)
def subscription_status(user_id: str,user: dict = Depends(authenticate_request)):
    try:
        validate_user_id(user_id)
        
        user_data =get_user(user_id)
        user_data = getUserbyId(user_id=user_id)
        subscription_data = user_data.get('subscription', {})
        
        remaining_days = 0
        if subscription_data.get('pro_expiry_date'):
            expiry_date = parse_datetime(subscription_data['pro_expiry_date'])
            if expiry_date:
                time_diff = (expiry_date - datetime.now(timezone.utc)).total_seconds()
                remaining_days = max(0, math.ceil(time_diff / SECONDS_PER_DAY))  # 86400 seconds in a day
            
        subscription_type = subscription_data.get('type', SubscriptionType.REGULAR.value)
        if remaining_days == 0 and subscription_type == SubscriptionType.PRO.value:
            subscription_type = SubscriptionType.REGULAR.value
            # TODO add a background job to clean expired subscriptions
            # update the plan type in database
            user_db = get_user_db()
            user_db.update_user(user_id, {
                'subscription.type': subscription_type
            })
        
        # Handle None plan_type by using 'or' operator
        plan_type = subscription_data.get('plan_type') or PlanType.NONE.value
        
        response = SubscriptionState(
            remaining_days= remaining_days,
            plan_type=plan_type,
            subscription_type=subscription_type,
            all_plan_details=SUBSCRIPTION_PLANS,
            taken_free_trial=subscription_data.get('taken_free_trial', False)
        )
        
        return {
            'success': True,
            'subscription_state': response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= {
                'error': 'Failed to fetch subscription state',
                'message': str(e)
            }
        )