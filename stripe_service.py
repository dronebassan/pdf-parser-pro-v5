"""
Stripe Payment and Subscription Service
Handles all billing, subscriptions, and usage tracking
"""

import stripe
import os
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, timedelta

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class PlanType(Enum):
    STUDENT = "student"
    GROWTH = "growth"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"

@dataclass
class Plan:
    name: str
    price_monthly: float
    pages_included: int
    overage_rate: float
    features: List[str]
    stripe_price_id: str
    stripe_usage_price_id: str

@dataclass
class Customer:
    id: str
    email: str
    stripe_customer_id: str
    subscription_id: str
    plan_type: PlanType
    pages_used_this_month: int
    subscription_status: str
    current_period_start: datetime
    current_period_end: datetime

class StripeService:
    def __init__(self):
        self.plans = {
            PlanType.STUDENT: Plan(
                name="Student Plan",
                price_monthly=6.99,
                pages_included=500,
                overage_rate=0.01,
                features=[
                    "500 pages/month",
                    "Revolutionary AI processing",
                    "All advanced features",
                    "Email support"
                ],
                stripe_price_id=os.getenv("STRIPE_STUDENT_PRICE_ID", "price_1RxLhYCVZzvkFjSrXR0pCSoO"),
                stripe_usage_price_id=os.getenv("STRIPE_STUDENT_USAGE_PRICE_ID", "")
            ),
            PlanType.GROWTH: Plan(
                name="Growth Plan",
                price_monthly=26.99,
                pages_included=2500,
                overage_rate=0.008,
                features=[
                    "2,500 pages/month",
                    "Priority processing",
                    "Advanced analytics",
                    "Chat support",
                    "API access"
                ],
                stripe_price_id=os.getenv("STRIPE_GROWTH_PRICE_ID", "price_1RxLjPCVZzvkFjSr8Fm6xVAj"),
                stripe_usage_price_id=os.getenv("STRIPE_GROWTH_USAGE_PRICE_ID", "")
            ),
            PlanType.BUSINESS: Plan(
                name="Business Plan",
                price_monthly=109.99,
                pages_included=10000,
                overage_rate=0.008,
                features=[
                    "10,000 pages/month",
                    "Faster processing queues",
                    "Performance dashboard",
                    "Phone + chat support",
                    "Full API access",
                    "Custom integrations"
                ],
                stripe_price_id=os.getenv("STRIPE_BUSINESS_PRICE_ID", "price_1RxLk5CVZzvkFjSrSfrJfv0S"),
                stripe_usage_price_id=os.getenv("STRIPE_BUSINESS_USAGE_PRICE_ID", "")
            ),
            PlanType.ENTERPRISE: Plan(
                name="Enterprise Plan",
                price_monthly=399.99,
                pages_included=50000,
                overage_rate=0.006,
                features=[
                    "50,000 pages/month",
                    "Dedicated processing",
                    "White-label options",
                    "24/7 priority support",
                    "Custom deployment",
                    "SLA guarantees"
                ],
                stripe_price_id=os.getenv("STRIPE_ENTERPRISE_PRICE_ID", "price_1RxLkqCVZzvkFjSra9ykMxJp"),
                stripe_usage_price_id=os.getenv("STRIPE_ENTERPRISE_USAGE_PRICE_ID", "")
            )
        }
    
    def create_checkout_session(self, plan_type: PlanType, customer_email: str, success_url: str, cancel_url: str) -> Dict[str, Any]:
        """Create a Stripe checkout session for subscription"""
        
        plan = self.plans[plan_type]
        
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer_email=customer_email,
                line_items=[{
                    'price': plan.stripe_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url,
                metadata={
                    'plan_type': plan_type.value,
                    'plan_name': plan.name
                }
            )
            
            return {
                "success": True,
                "checkout_url": checkout_session.url,
                "session_id": checkout_session.id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_customer_portal_session(self, customer_id: str, return_url: str) -> Dict[str, Any]:
        """Create customer portal session for managing subscription"""
        
        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            
            return {
                "success": True,
                "portal_url": portal_session.url
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_subscription_info(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription information from Stripe"""
        
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            return {
                "success": True,
                "subscription": {
                    "id": subscription.id,
                    "status": subscription.status,
                    "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                    "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                    "plan_id": subscription.items.data[0].price.id,
                    "customer_id": subscription.customer
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def track_usage(self, subscription_id: str, pages_processed: int) -> Dict[str, Any]:
        """Track usage and report to Stripe for billing"""
        
        try:
            # Get subscription to find usage price item
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Find the usage-based price item
            usage_item = None
            for item in subscription.items.data:
                # Check if this is the usage-based item (you'll need to identify this)
                if item.price.recurring.usage_type == "metered":
                    usage_item = item
                    break
            
            if not usage_item:
                return {
                    "success": False,
                    "error": "No usage-based item found in subscription"
                }
            
            # Create usage record
            usage_record = stripe.SubscriptionItem.create_usage_record(
                subscription_item_id=usage_item.id,
                quantity=pages_processed,
                timestamp=int(time.time()),
                action="increment"  # Add to existing usage
            )
            
            return {
                "success": True,
                "usage_record_id": usage_record.id,
                "total_usage": usage_record.total_usage
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_current_usage(self, subscription_id: str) -> Dict[str, Any]:
        """Get current month's usage for a subscription"""
        
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Find usage-based item
            usage_item = None
            for item in subscription.items.data:
                if item.price.recurring.usage_type == "metered":
                    usage_item = item
                    break
            
            if not usage_item:
                return {
                    "success": False,
                    "error": "No usage-based item found"
                }
            
            # Get usage records for current billing period
            usage_records = stripe.SubscriptionItem.list_usage_record_summaries(
                subscription_item_id=usage_item.id,
                limit=1
            )
            
            current_usage = 0
            if usage_records.data:
                current_usage = usage_records.data[0].total_usage
            
            return {
                "success": True,
                "current_usage": current_usage,
                "period_start": datetime.fromtimestamp(subscription.current_period_start),
                "period_end": datetime.fromtimestamp(subscription.current_period_end)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_usage_limits(self, subscription_id: str, additional_pages: int) -> Dict[str, Any]:
        """Check if customer can process additional pages within their plan"""
        
        try:
            # Get subscription info
            sub_info = self.get_subscription_info(subscription_id)
            if not sub_info["success"]:
                return sub_info
            
            # Get current usage
            usage_info = self.get_current_usage(subscription_id)
            if not usage_info["success"]:
                return usage_info
            
            # Determine plan type from price ID
            plan_type = None
            for pt, plan in self.plans.items():
                if plan.stripe_price_id == sub_info["subscription"]["plan_id"]:
                    plan_type = pt
                    break
            
            if not plan_type:
                return {
                    "success": False,
                    "error": "Unknown plan type"
                }
            
            plan = self.plans[plan_type]
            current_usage = usage_info["current_usage"]
            total_after_processing = current_usage + additional_pages
            
            # Check if within included pages
            within_limit = total_after_processing <= plan.pages_included
            overage_pages = max(0, total_after_processing - plan.pages_included)
            overage_cost = overage_pages * plan.overage_rate
            
            return {
                "success": True,
                "can_process": True,  # Always allow processing, just charge for overage
                "within_limit": within_limit,
                "current_usage": current_usage,
                "pages_included": plan.pages_included,
                "overage_pages": overage_pages,
                "overage_cost": overage_cost,
                "plan_name": plan.name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def handle_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        
        try:
            event_type = event['type']
            
            if event_type == 'customer.subscription.created':
                # New subscription created
                subscription = event['data']['object']
                return self._handle_subscription_created(subscription)
            
            elif event_type == 'customer.subscription.updated':
                # Subscription updated (plan change, etc.)
                subscription = event['data']['object']
                return self._handle_subscription_updated(subscription)
            
            elif event_type == 'customer.subscription.deleted':
                # Subscription cancelled
                subscription = event['data']['object']
                return self._handle_subscription_deleted(subscription)
            
            elif event_type == 'invoice.payment_succeeded':
                # Payment succeeded
                invoice = event['data']['object']
                return self._handle_payment_succeeded(invoice)
            
            elif event_type == 'invoice.payment_failed':
                # Payment failed
                invoice = event['data']['object']
                return self._handle_payment_failed(invoice)
            
            else:
                return {
                    "success": True,
                    "message": f"Unhandled event type: {event_type}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_subscription_created(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle new subscription creation"""
        try:
            # Get customer details from Stripe
            customer = stripe.Customer.retrieve(subscription["customer"])
            customer_email = customer["email"]
            
            # Determine plan type from subscription
            plan_type = "student"  # default
            if subscription.get("metadata", {}).get("plan_type"):
                plan_type = subscription["metadata"]["plan_type"]
            
            # Create user account if auth system is available
            try:
                from auth_system import auth_system
                from api_key_manager import SubscriptionTier
                
                if auth_system:
                    existing_customer = auth_system.get_customer_by_email(customer_email)
                    if not existing_customer:
                        # Map plan type to subscription tier
                        tier_map = {
                            "student": SubscriptionTier.STUDENT,
                            "growth": SubscriptionTier.GROWTH,
                            "business": SubscriptionTier.BUSINESS,
                            "enterprise": SubscriptionTier.ENTERPRISE
                        }
                        
                        subscription_tier = tier_map.get(plan_type.lower(), SubscriptionTier.STUDENT)
                        new_customer = auth_system.create_customer(
                            email=customer_email,
                            subscription_tier=subscription_tier
                        )
                        
                        # Set up usage tracking
                        try:
                            from usage_tracker import usage_tracker
                            from datetime import datetime, timedelta
                            
                            if usage_tracker:
                                plan_details = {
                                    "student": {"pages": 500, "rate": 0.01},
                                    "growth": {"pages": 2500, "rate": 0.008},
                                    "business": {"pages": 10000, "rate": 0.008},
                                    "enterprise": {"pages": 50000, "rate": 0.006}
                                }
                                
                                plan = plan_details.get(plan_type.lower(), {"pages": 500, "rate": 0.01})
                                cycle_start = datetime.now()
                                cycle_end = cycle_start + timedelta(days=30)
                                
                                usage_tracker.update_user_limits(
                                    user_id=new_customer.customer_id,
                                    subscription_id=subscription["id"],
                                    plan_type=plan_type.lower(),
                                    pages_included=plan["pages"],
                                    overage_rate=plan["rate"],
                                    billing_cycle_start=cycle_start,
                                    billing_cycle_end=cycle_end
                                )
                        except Exception as e:
                            print(f"Usage tracking setup failed: {e}")
                        
                        print(f"✅ Created user account for {customer_email} with {plan_type} plan")
                        return {
                            "success": True,
                            "message": f"User created and subscription activated for {customer_email}",
                            "subscription_id": subscription["id"],
                            "customer_id": subscription["customer"],
                            "api_key": new_customer.api_key
                        }
                    else:
                        print(f"✅ User {customer_email} already exists, updating subscription")
                        return {
                            "success": True,
                            "message": f"Subscription updated for existing user {customer_email}",
                            "subscription_id": subscription["id"],
                            "customer_id": subscription["customer"]
                        }
            except Exception as e:
                print(f"Auth system error: {e}")
            
            return {
                "success": True,
                "message": "Subscription created",
                "subscription_id": subscription["id"],
                "customer_id": subscription["customer"]
            }
            
        except Exception as e:
            print(f"❌ Error handling subscription creation: {e}")
            return {
                "success": False,
                "error": str(e),
                "subscription_id": subscription.get("id", "unknown")
            }
    
    def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription updates"""
        return {
            "success": True,
            "message": "Subscription updated",
            "subscription_id": subscription["id"]
        }
    
    def _handle_subscription_deleted(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation"""
        try:
            # Get customer details from Stripe
            customer = stripe.Customer.retrieve(subscription["customer"])
            customer_email = customer["email"]
            
            # Downgrade user to free tier
            try:
                from auth_system import auth_system
                from api_key_manager import SubscriptionTier, api_key_manager
                
                if auth_system:
                    existing_customer = auth_system.get_customer_by_email(customer_email)
                    if existing_customer:
                        # Downgrade customer to free tier
                        success = api_key_manager.downgrade_customer_to_free(existing_customer.customer_id)
                        
                        if success:
                            print(f"✅ Downgraded {customer_email} to free tier (10 pages/month)")
                            
                            # Update usage tracker
                            try:
                                from usage_tracker import usage_tracker
                                from datetime import datetime, timedelta
                                
                                if usage_tracker:
                                    cycle_start = datetime.now()
                                    cycle_end = cycle_start + timedelta(days=30)
                                    
                                    usage_tracker.update_user_limits(
                                        user_id=existing_customer.customer_id,
                                        subscription_id="",  # No active subscription
                                        plan_type="free",
                                        pages_included=10,
                                        overage_rate=0.0,  # No overage for free tier
                                        billing_cycle_start=cycle_start,
                                        billing_cycle_end=cycle_end
                                    )
                            except Exception as e:
                                print(f"Usage tracking update failed: {e}")
                            
                            return {
                                "success": True,
                                "message": f"Subscription cancelled and user {customer_email} downgraded to free tier",
                                "subscription_id": subscription["id"],
                                "customer_id": subscription["customer"]
                            }
            except Exception as e:
                print(f"Error downgrading user: {e}")
            
            return {
                "success": True,
                "message": "Subscription cancelled",
                "subscription_id": subscription["id"]
            }
            
        except Exception as e:
            print(f"❌ Error handling subscription cancellation: {e}")
            return {
                "success": False,
                "error": str(e),
                "subscription_id": subscription.get("id", "unknown")
            }
    
    def _handle_payment_succeeded(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment"""
        return {
            "success": True,
            "message": "Payment succeeded",
            "invoice_id": invoice["id"],
            "subscription_id": invoice["subscription"]
        }
    
    def _handle_payment_failed(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment"""
        return {
            "success": True,
            "message": "Payment failed",
            "invoice_id": invoice["id"],
            "subscription_id": invoice["subscription"]
        }

# Global instance
stripe_service = StripeService()