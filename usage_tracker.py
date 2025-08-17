"""
Usage Tracking System for PDF Parser Pro
Tracks page processing for billing and limits
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import sqlite3
from contextlib import contextmanager

@dataclass
class UsageRecord:
    user_id: str
    subscription_id: str
    pages_processed: int
    timestamp: datetime
    document_name: str
    processing_strategy: str
    ai_used: bool
    cost_estimate: float

@dataclass
class UserLimits:
    user_id: str
    subscription_id: str
    plan_type: str
    pages_included: int
    pages_used_this_month: int
    overage_rate: float
    billing_cycle_start: datetime
    billing_cycle_end: datetime

class UsageTracker:
    def __init__(self, db_path: str = "usage_tracking.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for usage tracking"""
        with self.get_db_connection() as conn:
            # Usage records table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS usage_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    subscription_id TEXT NOT NULL,
                    pages_processed INTEGER NOT NULL,
                    timestamp DATETIME NOT NULL,
                    document_name TEXT,
                    processing_strategy TEXT,
                    ai_used BOOLEAN,
                    cost_estimate REAL,
                    billing_period TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # User limits table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_limits (
                    user_id TEXT PRIMARY KEY,
                    subscription_id TEXT NOT NULL,
                    plan_type TEXT NOT NULL,
                    pages_included INTEGER NOT NULL,
                    overage_rate REAL NOT NULL,
                    billing_cycle_start DATETIME NOT NULL,
                    billing_cycle_end DATETIME NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Monthly usage summary table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS monthly_usage (
                    user_id TEXT,
                    billing_period TEXT,
                    total_pages INTEGER DEFAULT 0,
                    total_ai_pages INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0.0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, billing_period)
                )
            ''')
            
            conn.commit()
    
    @contextmanager
    def get_db_connection(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def track_usage(self, 
                   user_id: str, 
                   subscription_id: str, 
                   pages_processed: int,
                   document_name: str = "",
                   processing_strategy: str = "auto",
                   ai_used: bool = False,
                   cost_estimate: float = 0.0) -> Dict[str, Any]:
        """Track page usage for a user"""
        
        try:
            timestamp = datetime.now()
            billing_period = self._get_billing_period(timestamp)
            
            # Record usage
            with self.get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO usage_records 
                    (user_id, subscription_id, pages_processed, timestamp, 
                     document_name, processing_strategy, ai_used, cost_estimate, billing_period)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, subscription_id, pages_processed, timestamp,
                      document_name, processing_strategy, ai_used, cost_estimate, billing_period))
                
                # Update monthly summary
                conn.execute('''
                    INSERT OR REPLACE INTO monthly_usage 
                    (user_id, billing_period, total_pages, total_ai_pages, total_cost, last_updated)
                    VALUES (?, ?, 
                            COALESCE((SELECT total_pages FROM monthly_usage WHERE user_id = ? AND billing_period = ?), 0) + ?,
                            COALESCE((SELECT total_ai_pages FROM monthly_usage WHERE user_id = ? AND billing_period = ?), 0) + ?,
                            COALESCE((SELECT total_cost FROM monthly_usage WHERE user_id = ? AND billing_period = ?), 0) + ?,
                            ?)
                ''', (user_id, billing_period, user_id, billing_period, pages_processed,
                      user_id, billing_period, (1 if ai_used else 0),
                      user_id, billing_period, cost_estimate, timestamp))
                
                conn.commit()
            
            # Report to Stripe for billing
            from stripe_service import stripe_service
            stripe_result = stripe_service.track_usage(subscription_id, pages_processed)
            
            return {
                "success": True,
                "pages_tracked": pages_processed,
                "billing_period": billing_period,
                "stripe_reported": stripe_result.get("success", False)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_user_limits(self, user_id: str, pages_to_process: int) -> Dict[str, Any]:
        """Check if user can process additional pages"""
        
        try:
            # Get user limits
            user_limits = self.get_user_limits(user_id)
            if not user_limits:
                return {
                    "success": False,
                    "error": "User limits not found. Please check subscription."
                }
            
            # Get current usage
            current_usage = self.get_monthly_usage(user_id)
            total_pages_used = current_usage.get("total_pages", 0)
            
            # Calculate if within limits
            total_after_processing = total_pages_used + pages_to_process
            pages_included = user_limits["pages_included"]
            
            within_limit = total_after_processing <= pages_included
            overage_pages = max(0, total_after_processing - pages_included)
            overage_cost = overage_pages * user_limits["overage_rate"]
            
            return {
                "success": True,
                "can_process": True,  # Always allow, just charge overage
                "within_limit": within_limit,
                "current_usage": total_pages_used,
                "pages_included": pages_included,
                "pages_remaining": max(0, pages_included - total_pages_used),
                "overage_pages": overage_pages,
                "overage_cost": overage_cost,
                "plan_type": user_limits["plan_type"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_user_limits(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's subscription limits"""
        
        try:
            with self.get_db_connection() as conn:
                result = conn.execute('''
                    SELECT * FROM user_limits WHERE user_id = ?
                ''', (user_id,)).fetchone()
                
                if result:
                    return dict(result)
                return None
                
        except Exception as e:
            print(f"Error getting user limits: {e}")
            return None
    
    def update_user_limits(self, 
                          user_id: str,
                          subscription_id: str,
                          plan_type: str,
                          pages_included: int,
                          overage_rate: float,
                          billing_cycle_start: datetime,
                          billing_cycle_end: datetime) -> bool:
        """Update user's subscription limits"""
        
        try:
            with self.get_db_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO user_limits 
                    (user_id, subscription_id, plan_type, pages_included, overage_rate,
                     billing_cycle_start, billing_cycle_end, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, subscription_id, plan_type, pages_included, overage_rate,
                      billing_cycle_start, billing_cycle_end, datetime.now()))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error updating user limits: {e}")
            return False
    
    def get_monthly_usage(self, user_id: str, billing_period: str = None) -> Dict[str, Any]:
        """Get user's monthly usage summary"""
        
        if not billing_period:
            billing_period = self._get_billing_period(datetime.now())
        
        try:
            with self.get_db_connection() as conn:
                result = conn.execute('''
                    SELECT * FROM monthly_usage 
                    WHERE user_id = ? AND billing_period = ?
                ''', (user_id, billing_period)).fetchone()
                
                if result:
                    return dict(result)
                else:
                    return {
                        "total_pages": 0,
                        "total_ai_pages": 0,
                        "total_cost": 0.0
                    }
                    
        except Exception as e:
            print(f"Error getting monthly usage: {e}")
            return {"total_pages": 0, "total_ai_pages": 0, "total_cost": 0.0}
    
    def get_usage_history(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get user's usage history"""
        
        try:
            with self.get_db_connection() as conn:
                since_date = datetime.now() - timedelta(days=days)
                
                results = conn.execute('''
                    SELECT * FROM usage_records 
                    WHERE user_id = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                ''', (user_id, since_date)).fetchall()
                
                return [dict(row) for row in results]
                
        except Exception as e:
            print(f"Error getting usage history: {e}")
            return []
    
    def get_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get usage analytics for user"""
        
        try:
            current_usage = self.get_monthly_usage(user_id)
            user_limits = self.get_user_limits(user_id)
            recent_history = self.get_usage_history(user_id, 7)  # Last 7 days
            
            # Calculate daily average
            daily_pages = []
            for record in recent_history:
                date = record["timestamp"][:10]  # Get date part
                daily_pages.append(record["pages_processed"])
            
            avg_daily_pages = sum(daily_pages) / len(daily_pages) if daily_pages else 0
            
            # Projected monthly usage
            days_in_month = 30
            projected_monthly = avg_daily_pages * days_in_month
            
            return {
                "current_month": current_usage,
                "user_limits": user_limits,
                "avg_daily_pages": round(avg_daily_pages, 2),
                "projected_monthly": round(projected_monthly, 2),
                "recent_documents": len(recent_history),
                "ai_usage_rate": (current_usage.get("total_ai_pages", 0) / 
                                max(current_usage.get("total_pages", 1), 1) * 100)
            }
            
        except Exception as e:
            print(f"Error getting analytics: {e}")
            return {}
    
    def _get_billing_period(self, date: datetime) -> str:
        """Get billing period string (YYYY-MM format)"""
        return date.strftime("%Y-%m")
    
    def reset_monthly_usage(self, user_id: str, billing_period: str = None):
        """Reset monthly usage (called at billing cycle start)"""
        
        if not billing_period:
            billing_period = self._get_billing_period(datetime.now())
        
        try:
            with self.get_db_connection() as conn:
                conn.execute('''
                    DELETE FROM monthly_usage 
                    WHERE user_id = ? AND billing_period = ?
                ''', (user_id, billing_period))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error resetting monthly usage: {e}")
            return False

# Global instance
usage_tracker = UsageTracker()