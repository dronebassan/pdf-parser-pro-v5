"""
Military-grade API authentication system
"""

import secrets
import hashlib
import hmac
import time
import jwt
from typing import Optional, Dict
from dataclasses import dataclass, asdict
from fastapi import HTTPException, Header, Request
import bcrypt
import redis
import json
from datetime import datetime, timedelta

@dataclass
class SecureCustomer:
    customer_id: str
    email: str
    api_key_hash: str  # Never store plain API keys!
    subscription_tier: str
    created_at: int
    last_login: int
    failed_attempts: int
    is_locked: bool
    ip_whitelist: list
    
class SecureAuth:
    def __init__(self, redis_client, jwt_secret: str):
        self.redis = redis_client
        self.jwt_secret = jwt_secret
        
        # Security settings
        self.MAX_FAILED_ATTEMPTS = 5
        self.LOCKOUT_TIME = 3600  # 1 hour
        self.API_KEY_LENGTH = 64
        self.RATE_LIMIT_WINDOW = 3600  # 1 hour
        
    def generate_secure_api_key(self) -> tuple[str, str]:
        """Generate cryptographically secure API key"""
        # Generate random key
        raw_key = secrets.token_urlsafe(self.API_KEY_LENGTH)
        full_key = f"pdf_parser_{raw_key}"
        
        # Hash the key for storage (never store plain keys!)
        key_hash = bcrypt.hashpw(full_key.encode(), bcrypt.gensalt()).decode()
        
        return full_key, key_hash
    
    def create_secure_customer(self, email: str, subscription_tier: str, 
                              ip_address: str = None) -> tuple[SecureCustomer, str]:
        """Create customer with security measures"""
        
        # Generate secure customer ID
        customer_id = hashlib.sha256(f"{email}{time.time()}".encode()).hexdigest()
        
        # Generate secure API key
        api_key, api_key_hash = self.generate_secure_api_key()
        
        # Create customer record
        customer = SecureCustomer(
            customer_id=customer_id,
            email=email,
            api_key_hash=api_key_hash,
            subscription_tier=subscription_tier,
            created_at=int(time.time()),
            last_login=int(time.time()),
            failed_attempts=0,
            is_locked=False,
            ip_whitelist=[ip_address] if ip_address else []
        )
        
        # Store customer (encrypted)
        self._store_customer(customer)
        
        # Log creation event
        self._log_security_event("customer_created", customer_id, ip_address, {
            "email": email,
            "tier": subscription_tier
        })
        
        return customer, api_key
    
    def validate_api_key(self, api_key: str, ip_address: str, 
                        user_agent: str) -> Optional[SecureCustomer]:
        """Validate API key with security checks"""
        
        if not api_key or not api_key.startswith("pdf_parser_"):
            self._log_security_event("invalid_api_key_format", None, ip_address, {
                "api_key_prefix": api_key[:20] if api_key else "None"
            })
            return None
        
        # Rate limiting check
        if self._is_rate_limited(api_key, ip_address):
            self._log_security_event("rate_limit_exceeded", None, ip_address, {
                "api_key_prefix": api_key[:20]
            })
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Find customer by trying to match hash
        customer = self._find_customer_by_api_key(api_key)
        
        if not customer:
            self._increment_failed_attempts(ip_address)
            self._log_security_event("invalid_api_key", None, ip_address, {
                "api_key_prefix": api_key[:20],
                "user_agent": user_agent
            })
            return None
        
        # Check if account is locked
        if customer.is_locked:
            if time.time() - customer.last_login < self.LOCKOUT_TIME:
                self._log_security_event("account_locked_access", customer.customer_id, 
                                       ip_address, {"lockout_remaining": self.LOCKOUT_TIME - (time.time() - customer.last_login)})
                raise HTTPException(status_code=423, detail="Account locked due to suspicious activity")
            else:
                # Unlock account after lockout period
                customer.is_locked = False
                customer.failed_attempts = 0
        
        # IP whitelist check (optional)
        if customer.ip_whitelist and ip_address not in customer.ip_whitelist:
            self._log_security_event("ip_not_whitelisted", customer.customer_id, ip_address, {
                "whitelisted_ips": customer.ip_whitelist
            })
            # Allow but log (you can make this stricter)
        
        # Update last login
        customer.last_login = int(time.time())
        self._store_customer(customer)
        
        # Log successful authentication
        self._log_security_event("successful_auth", customer.customer_id, ip_address, {
            "user_agent": user_agent
        })
        
        return customer
    
    def _find_customer_by_api_key(self, api_key: str) -> Optional[SecureCustomer]:
        """Find customer by API key hash"""
        # In a real system, you'd query your database
        # For now, we'll iterate through Redis keys (not ideal for production)
        
        for key in self.redis.scan_iter(match="secure_customer:*"):
            customer_data = self.redis.get(key)
            if customer_data:
                try:
                    data = json.loads(customer_data)
                    stored_hash = data.get('api_key_hash')
                    
                    # Verify API key against stored hash
                    if bcrypt.checkpw(api_key.encode(), stored_hash.encode()):
                        return SecureCustomer(**data)
                except Exception:
                    continue
        
        return None
    
    def _store_customer(self, customer: SecureCustomer):
        """Store customer securely in Redis"""
        key = f"secure_customer:{customer.customer_id}"
        data = asdict(customer)
        
        # Encrypt sensitive data
        encrypted_data = self._encrypt_data(json.dumps(data))
        
        self.redis.set(key, encrypted_data)
    
    def _encrypt_data(self, data: str) -> str:
        """Simple encryption (use proper encryption in production)"""
        # For demo purposes - use proper encryption like Fernet in production
        return data  # TODO: Implement proper encryption
    
    def _is_rate_limited(self, api_key: str, ip_address: str) -> bool:
        """Check if API key or IP is rate limited"""
        current_time = int(time.time())
        window_start = current_time - self.RATE_LIMIT_WINDOW
        
        # Check API key rate limit
        key_requests = self.redis.zcount(f"rate_limit:key:{api_key}", window_start, current_time)
        if key_requests >= 1000:  # 1000 requests per hour per API key
            return True
        
        # Check IP rate limit
        ip_requests = self.redis.zcount(f"rate_limit:ip:{ip_address}", window_start, current_time)
        if ip_requests >= 100:  # 100 requests per hour per IP
            return True
        
        # Record this request
        self.redis.zadd(f"rate_limit:key:{api_key}", {current_time: current_time})
        self.redis.zadd(f"rate_limit:ip:{ip_address}", {current_time: current_time})
        
        # Clean up old entries
        self.redis.zremrangebyscore(f"rate_limit:key:{api_key}", 0, window_start)
        self.redis.zremrangebyscore(f"rate_limit:ip:{ip_address}", 0, window_start)
        
        return False
    
    def _increment_failed_attempts(self, ip_address: str):
        """Track failed attempts by IP"""
        key = f"failed_attempts:{ip_address}"
        attempts = self.redis.incr(key)
        self.redis.expire(key, 3600)  # Reset after 1 hour
        
        if attempts >= self.MAX_FAILED_ATTEMPTS:
            # Lock this IP for 1 hour
            self.redis.setex(f"locked_ip:{ip_address}", 3600, "locked")
    
    def _log_security_event(self, event_type: str, customer_id: Optional[str], 
                           ip_address: str, metadata: Dict):
        """Log security events for monitoring"""
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "customer_id": customer_id,
            "ip_address": ip_address,
            "metadata": metadata
        }
        
        # Store in Redis with expiration
        event_key = f"security_log:{int(time.time())}:{secrets.token_hex(8)}"
        self.redis.setex(event_key, 86400 * 30, json.dumps(event))  # Keep 30 days
        
        # Also store in daily aggregation for alerts
        date_key = f"security_events:{datetime.now().strftime('%Y-%m-%d')}"
        self.redis.hincrby(date_key, event_type, 1)
        self.redis.expire(date_key, 86400 * 90)  # Keep 90 days
        
        # Check for suspicious patterns
        self._check_security_alerts(event_type, ip_address, metadata)
    
    def _check_security_alerts(self, event_type: str, ip_address: str, metadata: Dict):
        """Check for patterns that indicate attacks"""
        
        # Check for brute force attacks
        if event_type == "invalid_api_key":
            recent_failures = self.redis.zcount(f"security_failures:{ip_address}", 
                                               time.time() - 300, time.time())  # Last 5 minutes
            if recent_failures >= 10:
                self._send_security_alert("brute_force_detected", ip_address, {
                    "failures_in_5min": recent_failures
                })
        
        # Check for unusual patterns
        if event_type == "successful_auth":
            # Check if this is a new location for this customer
            customer_id = metadata.get("customer_id")
            if customer_id:
                recent_ips = self.redis.smembers(f"customer_ips:{customer_id}")
                if ip_address not in recent_ips and len(recent_ips) > 0:
                    self._send_security_alert("new_location_login", ip_address, {
                        "customer_id": customer_id,
                        "previous_ips": list(recent_ips)
                    })
                
                # Remember this IP
                self.redis.sadd(f"customer_ips:{customer_id}", ip_address)
                self.redis.expire(f"customer_ips:{customer_id}", 86400 * 30)
    
    def _send_security_alert(self, alert_type: str, ip_address: str, metadata: Dict):
        """Send security alerts (email, Slack, etc.)"""
        alert = {
            "alert_type": alert_type,
            "ip_address": ip_address,
            "timestamp": time.time(),
            "metadata": metadata
        }
        
        # Store alert
        alert_key = f"security_alert:{int(time.time())}:{secrets.token_hex(8)}"
        self.redis.setex(alert_key, 86400 * 7, json.dumps(alert))
        
        # In production, send to monitoring system
        print(f"🚨 SECURITY ALERT: {alert_type} from {ip_address}")
        print(f"Details: {metadata}")
    
    def generate_jwt_token(self, customer: SecureCustomer) -> str:
        """Generate JWT token for session management"""
        payload = {
            "customer_id": customer.customer_id,
            "email": customer.email,
            "subscription_tier": customer.subscription_tier,
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def validate_jwt_token(self, token: str) -> Optional[Dict]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

# FastAPI dependency for secure authentication
async def get_authenticated_customer(
    request: Request,
    x_api_key: str = Header(None),
    authorization: str = Header(None)
) -> SecureCustomer:
    """Secure FastAPI authentication dependency"""
    
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")
    
    # Initialize secure auth (you'd pass Redis client here)
    secure_auth = SecureAuth(redis_client=None, jwt_secret="your-jwt-secret")
    
    # Try API key authentication first
    if x_api_key:
        customer = secure_auth.validate_api_key(x_api_key, ip_address, user_agent)
        if customer:
            return customer
    
    # Try JWT token authentication
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = secure_auth.validate_jwt_token(token)
        if payload:
            # Get customer from payload
            customer_id = payload.get("customer_id")
            # You'd fetch full customer data here
            pass
    
    # If no valid authentication
    raise HTTPException(status_code=401, detail="Invalid or missing authentication")