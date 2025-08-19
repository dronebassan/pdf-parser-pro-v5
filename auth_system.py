"""
User-friendly authentication system with email/password
"""

import jwt
import hashlib
import secrets
import time
import bcrypt
from typing import Optional, Dict
from dataclasses import dataclass
from fastapi import HTTPException, Depends, Header
# Import removed to fix deployment crash
try:
    from api_key_manager import api_key_manager, SubscriptionTier
except ImportError:
    api_key_manager = None
    class SubscriptionTier:
        FREE = "free"
        STUDENT = "student" 
        GROWTH = "growth"
        BUSINESS = "business"

@dataclass
class Customer:
    customer_id: str
    email: str
    password_hash: str
    api_key: str  # Internal use only - users never see this
    subscription_tier: SubscriptionTier
    created_at: int

class AuthSystem:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.customers = {}  # In production, use database
    
    def generate_api_key(self) -> str:
        """Generate unique API key for customer"""
        return f"pdf_parser_{secrets.token_urlsafe(32)}"
    
    def hash_password(self, password: str) -> str:
        """Hash password securely"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_customer(self, email: str, password: str, subscription_tier = "free") -> Customer:
        """Create new customer account with email/password"""
        
        # Check if customer already exists
        if self.get_customer_by_email(email):
            raise HTTPException(status_code=400, detail="Email already registered")
        
        customer_id = hashlib.md5(email.encode()).hexdigest()
        api_key = self.generate_api_key()
        password_hash = self.hash_password(password)
        
        customer = Customer(
            customer_id=customer_id,
            email=email,
            password_hash=password_hash,
            api_key=api_key,
            subscription_tier=subscription_tier,
            created_at=int(time.time())
        )
        
        # Store customer (in production: database)
        self.customers[email] = customer  # Store by email for easy lookup
        
        # Create customer config in API key manager  
        if api_key_manager:
            try:
                api_key_manager.create_customer(customer_id, email, subscription_tier)
            except Exception as e:
                print(f"API key manager error: {e}")
                pass  # Don't let this break registration
        
        return customer
    
    def authenticate_password(self, email: str, password: str) -> Optional[Customer]:
        """Authenticate user with email/password"""
        customer = self.customers.get(email)
        if customer and self.verify_password(password, customer.password_hash):
            return customer
        return None
    
    def authenticate_api_key(self, api_key: str) -> Optional[Customer]:
        """Validate API key and return customer (internal use)"""
        for customer in self.customers.values():
            if customer.api_key == api_key:
                return customer
        return None
    
    def get_customer_by_api_key(self, api_key: str) -> Optional[Customer]:
        """Get customer by API key (internal use)"""
        return self.authenticate_api_key(api_key)
    
    def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email"""
        return self.customers.get(email)
    
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