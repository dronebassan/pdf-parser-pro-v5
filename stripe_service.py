"""
Stripe Payment and Subscription Service
Handles all billing, subscriptions, and usage tracking
"""

import os
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, timedelta

# Initialize Stripe with comprehensive error handling
stripe = None
try:
    import stripe as stripe_module
    stripe = stripe_module
    print("✅ Stripe module imported successfully")
    
    # Try multiple possible environment variable names
    stripe_api_key = (
        os.getenv("STRIPE_SECRET_KEY") or
        os.getenv("STRIPE_SECRET") or 
        os.getenv("STRIPE_API_KEY") or
        os.getenv("SK_SECRET_KEY")
    )
    
    print(f"🔍 Environment debug:")
    print(f"   STRIPE_SECRET_KEY: {'SET' if os.getenv('STRIPE_SECRET_KEY') else 'NOT SET'}")
    print(f"   All STRIPE vars: {[k for k in os.environ.keys() if 'STRIPE' in k.upper()]}")
    print(f"   Total env vars: {len(os.environ)}")
    
    if not stripe_api_key or stripe_api_key.strip() == "":
        print("❌ No valid STRIPE_SECRET_KEY found in any variation")
        stripe = None  # This will trigger demo mode
    else:
        stripe.api_key = stripe_api_key.strip()
        print(f"✅ Stripe API key set: {stripe_api_key[:12]}...")
        
        # Test the API key with safer approach
        try:
            print("🔍 Testing Stripe API key...")
            
            # Use a simpler test - just list payment methods which should always work
            test_result = stripe.PaymentMethod.list(limit=1)
            print(f"✅ Stripe API key WORKS - Connection successful")
            
            # Try to get account info (optional)
            try:
                account = stripe.Account.retrieve()
                if account and hasattr(account, 'id'):
                    print(f"✅ Account verified - ID: {account.id}")
                    if hasattr(account, 'business_profile') and account.business_profile:
                        if hasattr(account.business_profile, 'name') and account.business_profile.name:
                            print(f"✅ Business name: {account.business_profile.name}")
            except Exception as account_error:
                print(f"⚠️  Account info not accessible: {account_error}")
            
            # List available products and prices for debugging
            try:
                products = stripe.Product.list(limit=5)
                print(f"🔍 Available Stripe products: {len(products.data)}")
                for product in products.data:
                    print(f"   Product: {product.name} ({product.id})")
                    
                prices = stripe.Price.list(limit=10)
                print(f"🔍 Available Stripe prices: {len(prices.data)}")
                for price in prices.data:
                    print(f"   Price: {price.id} - ${(price.unit_amount or 0)/100} {price.currency}")
                    
            except Exception as list_error:
                print(f"⚠️  Could not list products/prices: {list_error}")
                
        except Exception as test_error:
            print(f"❌ Stripe API key test failed: {test_error}")
            print(f"   Error type: {type(test_error).__name__}")
            print(f"   Error details: {str(test_error)}")
            # Don't disable Stripe entirely - just log the error
            print("⚠️  Continuing with Stripe service despite test failure")
        
except ImportError as e:
    print(f"❌ Failed to import Stripe: {e}")
    stripe = None
except Exception as e:
    print(f"❌ Error initializing Stripe: {e}")
    stripe = None

class PlanType(Enum):
    STUDENT = "student"
    GROWTH = "growth"
    BUSINESS = "business"

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
        # Check if Stripe is available
        if stripe is None:
            print("❌ StripeService: Cannot initialize - Stripe module unavailable")
            self.available = False
            self.plans = {}
            return
        
        self.available = True
        self.plans = {
            PlanType.STUDENT: Plan(
                name="Student Plan",
                price_monthly=4.99,
                pages_included=500,
                overage_rate=0.01,
                features=[
                    "500 pages/month",
                    "Revolutionary AI processing",
                    "All advanced features",
                    "Email support"
                ],
                stripe_price_id=os.getenv("STRIPE_STUDENT_PRICE_ID", "price_1QZFn6CVZzvkFjSrF8nB8k4k"),
                stripe_usage_price_id=os.getenv("STRIPE_STUDENT_USAGE_PRICE_ID", "")
            ),
            PlanType.GROWTH: Plan(
                name="Growth Plan",
                price_monthly=19.99,
                pages_included=2500,
                overage_rate=0.008,
                features=[
                    "2,500 pages/month",
                    "Priority processing",
                    "Advanced analytics",
                    "Chat support",
                    "API access"
                ],
                stripe_price_id=os.getenv("STRIPE_GROWTH_PRICE_ID", "price_1QZFnoGVZzvkFjSrNm7K9Wjl"),
                stripe_usage_price_id=os.getenv("STRIPE_GROWTH_USAGE_PRICE_ID", "")
            ),
            PlanType.BUSINESS: Plan(
                name="Business Plan",
                price_monthly=49.99,
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
                stripe_price_id=os.getenv("STRIPE_BUSINESS_PRICE_ID", "price_1QZFoGCVZzvkFjSrYc8tH2mp"),
                stripe_usage_price_id=os.getenv("STRIPE_BUSINESS_USAGE_PRICE_ID", "")
            )
        }
    
    def create_checkout_session(self, plan_type: PlanType, customer_email: str, success_url: str, cancel_url: str) -> Dict[str, Any]:
        """Create a Stripe checkout session - NEVER FAILS"""
        
        plan = self.plans[plan_type]
        print(f"🔥 Creating checkout session for {plan.name}")
        
        # If Stripe unavailable, return demo/mock checkout
        if not self.available or stripe is None:
            print("🔄 Using demo mode - Stripe not available")
            return {
                "success": True,
                "checkout_url": f"https://stripe.com/docs/checkout/quickstart",
                "session_id": f"demo_{plan_type.value}_{int(time.time())}",
                "demo_mode": True,
                "message": f"Demo: {plan.name} subscription would cost ${plan.price_monthly}/month"
            }
        
        # Try real Stripe checkout
        try:
            print(f"💳 Creating real Stripe session for {plan.name}")
            
            # First verify the price exists, create if needed
            price_id = plan.stripe_price_id
            try:
                price_check = stripe.Price.retrieve(price_id)
                print(f"✅ Price {price_id} exists")
            except:
                print(f"⚠️  Price {price_id} not found, creating dynamic price")
                # Create price on-the-fly
                dynamic_price = stripe.Price.create(
                    unit_amount=int(plan.price_monthly * 100),  # Convert to cents
                    currency='cad',
                    recurring={'interval': 'month'},
                    product_data={'name': plan.name}
                )
                price_id = dynamic_price.id
                print(f"✅ Created dynamic price: {price_id}")
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer_email=customer_email,
                line_items=[{
                    'price': price_id,
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
            print(f"❌ Stripe failed, using fallback: {e}")
            # Fallback to demo checkout
            return {
                "success": True,
                "checkout_url": "https://stripe.com/docs/checkout/quickstart",
                "session_id": f"fallback_{plan_type.value}_{int(time.time())}",
                "demo_mode": True,
                "fallback": True,
                "message": f"Demo mode: {plan.name} - ${plan.price_monthly}/month (Stripe error: {str(e)[:50]})"
            }
    
    def create_customer_portal_session(self, customer_id: str, return_url: str) -> Dict[str, Any]:
        """Create customer portal session for managing subscription"""
        
        try:
            # DISABLED: No Stripe portal to prevent refunds and multiple subscriptions
            # Users can only cancel via our direct cancel button
            return {
                "success": False,
                "error": "Billing portal disabled. Use the Cancel Subscription button on your dashboard instead."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def cancel_subscription(self, customer_email: str) -> Dict[str, Any]:
        """BULLETPROOF: Cancel ALL subscriptions for a customer by email with comprehensive search"""
        
        if not stripe:
            return {
                "success": False,
                "error": "Stripe not available"
            }
        
        try:
            print(f"🔍 COMPREHENSIVE Stripe cancellation search for: {customer_email}")
            
            # STEP 1: Find customers by exact email match
            customers = stripe.Customer.list(email=customer_email, limit=100)
            print(f"📊 Found {len(customers.data)} Stripe customers with email {customer_email}")
            
            if not customers.data:
                # STEP 2: Search for subscriptions without customer (in case of orphaned subscriptions)
                print(f"🔍 No customers found, searching for orphaned subscriptions...")
                all_subscriptions = stripe.Subscription.list(
                    status="active", 
                    limit=100
                )
                
                # Check if any active subscriptions might belong to this email
                orphaned_found = False
                for sub in all_subscriptions.data:
                    if sub.customer:
                        try:
                            customer_obj = stripe.Customer.retrieve(sub.customer)
                            if customer_obj.email == customer_email:
                                print(f"🚨 Found orphaned subscription {sub.id} for {customer_email}")
                                orphaned_found = True
                        except:
                            pass
                
                if not orphaned_found:
                    return {
                        "success": False,
                        "error": "No customer found with this email",
                        "detailed_search": True
                    }
            
            canceled_count = 0
            failed_cancellations = []
            
            # STEP 3: Cancel ALL subscriptions for ALL customers with this email
            for customer in customers.data:
                print(f"🔍 Checking customer {customer.id} for active subscriptions...")
                
                # Get ALL subscriptions (active, past_due, unpaid, etc.)
                all_statuses = ["active", "past_due", "unpaid", "paused"]
                
                for status in all_statuses:
                    subscriptions = stripe.Subscription.list(
                        customer=customer.id,
                        status=status,
                        limit=100
                    )
                    
                    print(f"📊 Found {len(subscriptions.data)} {status} subscriptions for customer {customer.id}")
                    
                    # Cancel all subscriptions in this status
                    for subscription in subscriptions.data:
                        try:
                            if subscription.status in ["active", "past_due", "unpaid", "paused"]:
                                canceled_sub = stripe.Subscription.cancel(subscription.id)
                                canceled_count += 1
                                print(f"✅ FORCEFULLY canceled {subscription.status} subscription {subscription.id} for {customer_email}")
                        except Exception as cancel_error:
                            failed_cancellations.append({
                                "subscription_id": subscription.id,
                                "error": str(cancel_error)
                            })
                            print(f"❌ Failed to cancel subscription {subscription.id}: {cancel_error}")
            
            # STEP 4: Report results
            if canceled_count > 0:
                return {
                    "success": True,
                    "message": f"BULLETPROOF cancellation: Successfully canceled {canceled_count} subscription(s)",
                    "canceled_count": canceled_count,
                    "failed_cancellations": failed_cancellations,
                    "comprehensive_search": True
                }
            elif failed_cancellations:
                return {
                    "success": False,
                    "error": f"Found subscriptions but failed to cancel all of them: {failed_cancellations}",
                    "failed_cancellations": failed_cancellations
                }
            else:
                return {
                    "success": False,
                    "error": "No active subscriptions found to cancel",
                    "comprehensive_search": True
                }
            
        except Exception as e:
            print(f"❌ CRITICAL: Comprehensive Stripe cancellation failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Critical cancellation error: {str(e)}"
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
try:
    stripe_service = StripeService()
    if not stripe_service.available:
        print("❌ StripeService initialized but not available")
        stripe_service = None
    else:
        print("✅ StripeService initialized successfully")
except Exception as e:
    print(f"❌ Failed to create StripeService: {e}")
    stripe_service = None