"""
Payment processing with Stripe integration
"""

import stripe
import os
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

# Set Stripe API key
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class PaymentIntent:
    customer_id: str
    amount: int  # in cents
    currency: str
    subscription_tier: str
    stripe_payment_intent_id: str
    status: PaymentStatus

class PaymentSystem:
    def __init__(self):
        # Stripe price IDs (create these in Stripe dashboard)
        self.stripe_prices = {
            'basic_monthly': 'price_basic_monthly_id',
            'premium_monthly': 'price_premium_monthly_id', 
            'enterprise_monthly': 'price_enterprise_monthly_id'
        }
        
        # Your pricing in cents
        self.pricing = {
            'basic': 2900,      # $29.00
            'premium': 9900,    # $99.00
            'enterprise': 29900 # $299.00
        }
    
    def create_payment_intent(self, customer_id: str, subscription_tier: str) -> PaymentIntent:
        """Create Stripe payment intent for subscription"""
        
        amount = self.pricing.get(subscription_tier.lower())
        if not amount:
            raise ValueError(f"Invalid subscription tier: {subscription_tier}")
        
        try:
            # Create payment intent with Stripe
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency='usd',
                metadata={
                    'customer_id': customer_id,
                    'subscription_tier': subscription_tier,
                    'service': 'pdf_parser_pro'
                }
            )
            
            return PaymentIntent(
                customer_id=customer_id,
                amount=amount,
                currency='usd',
                subscription_tier=subscription_tier,
                stripe_payment_intent_id=intent.id,
                status=PaymentStatus.PENDING
            )
            
        except stripe.error.StripeError as e:
            raise Exception(f"Payment processing error: {str(e)}")
    
    def create_subscription(self, customer_email: str, subscription_tier: str) -> Dict:
        """Create recurring subscription"""
        
        price_id = self.stripe_prices.get(f'{subscription_tier.lower()}_monthly')
        if not price_id:
            raise ValueError(f"Invalid subscription tier: {subscription_tier}")
        
        try:
            # Create or get Stripe customer
            customers = stripe.Customer.list(email=customer_email, limit=1)
            
            if customers.data:
                customer = customers.data[0]
            else:
                customer = stripe.Customer.create(email=customer_email)
            
            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': price_id}],
                metadata={
                    'service': 'pdf_parser_pro',
                    'tier': subscription_tier
                }
            )
            
            return {
                'subscription_id': subscription.id,
                'customer_id': customer.id,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end
            }
            
        except stripe.error.StripeError as e:
            raise Exception(f"Subscription creation error: {str(e)}")
    
    def handle_webhook(self, payload: str, sig_header: str) -> Dict:
        """Handle Stripe webhook events"""
        
        endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            raise Exception("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise Exception("Invalid signature")
        
        # Handle different event types
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            return self._handle_payment_success(payment_intent)
        
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            return self._handle_payment_failure(payment_intent)
        
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            return self._handle_subscription_payment(invoice)
        
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            return self._handle_subscription_cancelled(subscription)
        
        return {'status': 'unhandled'}
    
    def _handle_payment_success(self, payment_intent: Dict) -> Dict:
        """Handle successful payment"""
        customer_id = payment_intent['metadata']['customer_id']
        subscription_tier = payment_intent['metadata']['subscription_tier']
        
        # Upgrade customer in your system
        from auth_system import auth_system, SubscriptionTier
        # You'll need to find customer by customer_id and upgrade them
        
        return {
            'status': 'payment_successful',
            'customer_id': customer_id,
            'tier': subscription_tier
        }
    
    def _handle_payment_failure(self, payment_intent: Dict) -> Dict:
        """Handle failed payment"""
        customer_id = payment_intent['metadata']['customer_id']
        
        # Maybe send email notification, downgrade account, etc.
        
        return {
            'status': 'payment_failed',
            'customer_id': customer_id
        }
    
    def _handle_subscription_payment(self, invoice: Dict) -> Dict:
        """Handle recurring subscription payment"""
        customer_id = invoice['customer']
        
        # Extend customer's subscription, reset quota, etc.
        
        return {
            'status': 'subscription_renewed',
            'customer_id': customer_id
        }
    
    def _handle_subscription_cancelled(self, subscription: Dict) -> Dict:
        """Handle subscription cancellation"""
        customer_id = subscription['customer']
        
        # Downgrade customer to free tier
        
        return {
            'status': 'subscription_cancelled',
            'customer_id': customer_id
        }

# Global payment system
payment_system = PaymentSystem()