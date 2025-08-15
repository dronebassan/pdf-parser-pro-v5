"""
Customer authentication and API key system
"""

import jwt
import hashlib
import secrets
import time
from typing import Optional, Dict
from dataclasses import dataclass
from fastapi import HTTPException, Depends, Header
from api_key_manager import api_key_manager, SubscriptionTier

@dataclass
class Customer:
    customer_id: str
    email: str
    api_key: str
    subscription_tier: SubscriptionTier
    created_at: int

class AuthSystem:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.customers = {}  # In production, use database
    
    def generate_api_key(self) -> str:
        """Generate unique API key for customer"""
        return f"pdf_parser_{secrets.token_urlsafe(32)}"
    
    def create_customer(self, email: str, subscription_tier: SubscriptionTier = SubscriptionTier.FREE) -> Customer:
        """Create new customer account"""
        
        customer_id = hashlib.md5(email.encode()).hexdigest()
        api_key = self.generate_api_key()
        
        customer = Customer(
            customer_id=customer_id,
            email=email,
            api_key=api_key,
            subscription_tier=subscription_tier,
            created_at=int(time.time())
        )
        
        # Store customer (in production: database)
        self.customers[api_key] = customer
        
        # Create customer config in API key manager
        api_key_manager.create_customer(customer_id, email, subscription_tier)
        
        return customer
    
    def authenticate_api_key(self, api_key: str) -> Optional[Customer]:
        """Validate API key and return customer"""
        return self.customers.get(api_key)
    
    def upgrade_customer(self, api_key: str, new_tier: SubscriptionTier):
        """Upgrade customer subscription"""
        customer = self.authenticate_api_key(api_key)
        if customer:
            customer.subscription_tier = new_tier
            # Update in API key manager
            config = api_key_manager.get_customer_config(customer.customer_id)
            if config:
                config.subscription_tier = new_tier
                api_key_manager.save_customer_config(config)

# Global auth system
auth_system = AuthSystem(secret_key="your-jwt-secret-here")

# FastAPI dependency for authentication
async def get_current_customer(x_api_key: str = Header(None)) -> Customer:
    """FastAPI dependency to authenticate requests"""
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    customer = auth_system.authenticate_api_key(x_api_key)
    if not customer:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return customer