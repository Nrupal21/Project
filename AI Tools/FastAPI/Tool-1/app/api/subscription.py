from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
import razorpay
import os
from typing import Optional, Dict
import logging
from forex_python.converter import CurrencyRates

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize Razorpay client
client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)

router = APIRouter()

# Currency conversion utility
c = CurrencyRates()

# Base prices in USD
BASE_PRICES = {
    "hobby": 5,      # $5/month
    "basic": 10,     # $10/month
    "pro": 25,       # $25/month
    "enterprise": 99  # $99/month
}

# Regional pricing adjustments (multiplier based on purchasing power parity)
REGIONAL_ADJUSTMENTS = {
    "US": 1.0,    # Base price (USD)
    "IN": 0.4,    # India
    "BR": 0.5,    # Brazil
    "NG": 0.3,    # Nigeria
    "ID": 0.4,    # Indonesia
    "PH": 0.4,    # Philippines
    "default": 0.7  # Other regions
}

# Subscription plans with features
SUBSCRIPTION_PLANS = {
    "hobby": {
        "name": "Hobby Plan",
        "features": [
            "GPT-3.5 Access",
            "Basic AI Features",
            "Community Support",
            "5 AI Requests/day"
        ]
    },
    "basic": {
        "name": "Basic Plan",
        "features": [
            "GPT-3.5 Access",
            "All Basic AI Features",
            "Email Support",
            "50 AI Requests/day",
            "Basic Analytics"
        ]
    },
    "pro": {
        "name": "Pro Plan",
        "features": [
            "GPT-4 Access",
            "All Advanced AI Features",
            "Priority Support",
            "Unlimited AI Requests",
            "Advanced Analytics",
            "API Access"
        ]
    },
    "enterprise": {
        "name": "Enterprise Plan",
        "features": [
            "GPT-4 & Claude Access",
            "All Premium AI Features",
            "24/7 Dedicated Support",
            "Unlimited AI Requests",
            "Custom Analytics",
            "API Access",
            "Custom Model Training",
            "SLA Guarantee"
        ]
    }
}

class SubscriptionRequest(BaseModel):
    plan: str
    email: str
    name: str
    country_code: str = "US"
    currency: str = "USD"

class SubscriptionResponse(BaseModel):
    subscription_id: str
    order_id: str
    amount: float
    currency: str
    key: str
    name: str
    description: str
    image: str
    prefill: dict
    theme: dict

def get_adjusted_price(base_price: float, country_code: str, currency: str) -> float:
    """Calculate regionally adjusted price in specified currency"""
    # Get regional adjustment factor
    adjustment = REGIONAL_ADJUSTMENTS.get(country_code, REGIONAL_ADJUSTMENTS["default"])
    
    # Calculate adjusted price in USD
    adjusted_usd = base_price * adjustment
    
    # Convert to target currency if not USD
    if currency != "USD":
        try:
            adjusted_price = c.convert("USD", currency, adjusted_usd)
            # Round to appropriate number of decimal places
            if currency in ["JPY", "KRW", "IDR"]:
                return round(adjusted_price)
            return round(adjusted_price, 2)
        except:
            # Fallback to USD if conversion fails
            logger.warning(f"Currency conversion failed for {currency}, using USD")
            return adjusted_usd
    
    return adjusted_usd

@router.get("/plans")
async def get_subscription_plans(country_code: str = "US", currency: str = "USD"):
    """
    Get available subscription plans with adjusted pricing
    """
    try:
        plans = {}
        for plan_id, plan_data in SUBSCRIPTION_PLANS.items():
            base_price = BASE_PRICES[plan_id]
            adjusted_price = get_adjusted_price(base_price, country_code, currency)
            
            plans[plan_id] = {
                **plan_data,
                "price": adjusted_price,
                "currency": currency
            }
        
        return {
            "plans": plans,
            "country_code": country_code,
            "currency": currency
        }
    except Exception as e:
        logger.error(f"Error getting subscription plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving subscription plans")

@router.post("/create-subscription", response_model=SubscriptionResponse)
async def create_subscription(request: SubscriptionRequest):
    """
    Create a new subscription order with Razorpay
    """
    try:
        if request.plan not in SUBSCRIPTION_PLANS:
            raise HTTPException(status_code=400, detail="Invalid plan selected")

        base_price = BASE_PRICES[request.plan]
        adjusted_price = get_adjusted_price(base_price, request.country_code, request.currency)
        
        # Convert to smallest currency unit (e.g., cents, paise)
        amount = int(adjusted_price * 100)
        
        # Create order
        order = client.order.create({
            "amount": amount,
            "currency": request.currency,
            "receipt": f"order_{request.email}",
            "notes": {
                "plan": request.plan,
                "email": request.email,
                "country_code": request.country_code
            }
        })

        # Prepare response
        response = SubscriptionResponse(
            subscription_id=order["id"],
            order_id=order["id"],
            amount=adjusted_price,
            currency=request.currency,
            key=os.getenv("RAZORPAY_KEY_ID"),
            name="AI Assistant Hub",
            description=SUBSCRIPTION_PLANS[request.plan]["name"],
            image="https://your-logo-url.com/logo.png",  # Replace with your logo
            prefill={
                "name": request.name,
                "email": request.email
            },
            theme={
                "color": "#10a37f"
            }
        )

        logger.info(f"Created subscription order for {request.email} - Plan: {request.plan}, Country: {request.country_code}")
        return response

    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating subscription")

@router.post("/verify-payment")
async def verify_payment(request: Request):
    """
    Verify Razorpay payment webhook
    """
    try:
        body = await request.json()
        params_dict = dict(body)
        
        # Verify the payment signature
        client.utility.verify_payment_signature(params_dict)
        
        # Process the payment
        if params_dict.get("event") == "payment.captured":
            # Update user subscription status
            # Add your logic here to update the database
            logger.info(f"Payment verified for order: {params_dict.get('payload', {}).get('payment', {}).get('entity', {}).get('order_id')}")
            return {"status": "success"}
        
        return {"status": "ignored"}
    
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid payment signature") 