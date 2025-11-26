from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
import razorpay
import os
from helper.middleware import authenticate_request
from database.user_db import getUserbyId, get_user_db
from models.users_schema import User, SubscriptionType, PlanType, SubscriptionInfo
from datetime import datetime, timedelta, timezone
import logging
import hashlib



router = APIRouter(prefix='/api/subscription', tags=['Subscription'])
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

class VerifyPaymentRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: str
    user_id: str
    plan_type: str
    
class StartFreeTrialRequest(BaseModel):
    user_id: str

@router.post('/create-order', status_code=status.HTTP_201_CREATED)
def create_order(request: CreateOrderRequest, user: dict = Depends(authenticate_request)):
    try:
        # Validate input
        user_id = request.user_id
        plan_type = request.plan_type.lower()
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= {
                    'error': 'User not found',
                    'message': 'User ID is required to create an order'
                }
            )
        
        if plan_type not in ['monthly', 'annual']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= {
                    'error': 'Invalid plan type',
                    'message': 'Plan type must be either "monthly" or "annual"'
                }
            )
            
        # Get plan details
        plan_details = SUBSCRIPTION_PLANS[plan_type]
        
        user_hash = hashlib.md5(user_id.encode()).hexdigest()[:8]
        timestamp = int(datetime.now().timestamp())

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


@router.post('/verify-payment', status_code=status.HTTP_200_OK)
def verify_payment(request: VerifyPaymentRequest, user: dict = Depends(authenticate_request)):
    logger.info(f"Verifying payment for user {request.user_id} with order ID {request.order_id}")
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
        
        # Payment is verified - Update user subscription in database here
        user = getUserbyId(user_id=request.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    'error': 'User not found',
                    'message': 'No user exists with the provided ID'
                }
            )
            
        if user.get('subscription') is None:
            user['subscription'] = {}
                
        expiry_date = user.get('subscription', {}).get('pro_expiry_date')
        if expiry_date is None:
            expiry_date = datetime.now(timezone.utc)
        
            
        user['subscription'] = {
            'type': SubscriptionType.PRO.value,
            'plan_type': request.plan_type.lower(),
            'pro_expiry_date': expiry_date + timedelta(days=30) if request.plan_type.lower() == PlanType.MONTHLY.value else expiry_date + timedelta(days=365),
            'taken_free_trial': user.get('subscription', {}).get('taken_free_trial', False),
            'payment_detail_list': user.get('subscription', {}).get('payment_detail_list', []) + [{
                'payment_id': request.payment_id,
                'order_id': request.order_id,
                'plan_type': request.plan_type.lower(),
                'time': datetime.now(timezone.utc).isoformat()
            }]
        }
        
        user_db = get_user_db()
        is_updated = user_db.update_user(user_id=request.user_id, update_data=user)
        if not is_updated:
            logger.error(f"Failed to update subscription for user {request.user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'error': 'Subscription update failed',
                    'message': 'Could not update user subscription details in the database'
                }
            )
        
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
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= {
                    'error': 'User not found',
                    'message': 'User ID is required to start free trial'
                }
            )
        
        user_data = getUserbyId(user_id=user_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    'error': 'User not found',
                    'message': 'No user exists with the provided ID'
                }
            )
        
        subscription_info = user_data.get('subscription', {})
        if subscription_info.get('taken_free_trial', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    'error': 'Free trial already used',
                    'message': 'User has already taken the free trial'
                }
            )
        
        expiry_date = datetime.now(timezone.utc) + timedelta(days=7)
        
        user_data['subscription'] = {
            'type': SubscriptionType.PRO.value,
            'plan_type': PlanType.TRIAL.value,
            'pro_expiry_date': expiry_date,
            'taken_free_trial': True,
            'payment_detail_list': subscription_info.get('payment_detail_list', [])
        }
        
        user_db = get_user_db()
        is_updated = user_db.update_user(user_id=user_id, update_data=user_data)
        if not is_updated:
            logger.error(f"Failed to update free trial subscription for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'error': 'Free trial activation failed',
                    'message': 'Could not update user subscription details in the database'
                }
            )
        
        return {
            'success': True,
            'message': 'Free trial started successfully',
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
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= {
                    'error': 'User not found',
                    'message': 'User ID is required to fetch subscription status'
                }
            )
        
        user_data = getUserbyId(user_id=user_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    'error': 'User not found',
                    'message': 'No user exists with the provided ID'
                }
            )
        subscription_data = user_data.get('subscription', {})
        
        
        remaining_days = 0
        if subscription_data.get('pro_expiry_date'):
            expiry_date = subscription_data['pro_expiry_date']
            remaining_days = max(0,(expiry_date - datetime.now(timezone.utc)).days)
            
        
        response = SubscriptionState(
            remaining_days= remaining_days,
            plan_type=subscription_data.get('plan_type', PlanType.NONE.value),
            subscription_type=subscription_data.get('type', SubscriptionType.REGULAR.value),
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