"""
Rate Limiter for Danny Bot
Prevents spam and ensures system stability with high user loads
"""

import time
import asyncio
import logging
from collections import defaultdict, deque
from typing import Dict, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter to prevent spam and ensure system stability"""
    
    def __init__(self):
        # User-based rate limiting
        self.user_requests: Dict[int, deque] = defaultdict(lambda: deque(maxlen=10))
        self.user_cooldowns: Dict[int, float] = {}
        
        # Global rate limiting
        self.global_requests: deque = deque(maxlen=100)
        
        # Rate limit configurations
        self.USER_RATE_LIMIT = 5  # requests per minute per user
        self.USER_COOLDOWN = 60   # seconds
        self.GLOBAL_RATE_LIMIT = 50  # requests per minute globally
        
        # Spam detection
        self.spam_users: Dict[int, float] = {}  # user_id -> unban_time
        self.SPAM_THRESHOLD = 10  # requests in short time = spam
        self.SPAM_BAN_DURATION = 300  # 5 minutes
    
    def is_user_rate_limited(self, user_id: int) -> tuple[bool, Optional[float]]:
        """Check if user is rate limited"""
        current_time = time.time()
        
        # Check if user is spam-banned
        if user_id in self.spam_users:
            unban_time = self.spam_users[user_id]
            if current_time < unban_time:
                return True, unban_time - current_time
            else:
                # Unban user
                del self.spam_users[user_id]
        
        # Check if user is in cooldown
        if user_id in self.user_cooldowns:
            cooldown_end = self.user_cooldowns[user_id]
            if current_time < cooldown_end:
                return True, cooldown_end - current_time
        
        # Check rate limit
        user_requests = self.user_requests[user_id]
        
        # Remove old requests (older than 1 minute)
        while user_requests and current_time - user_requests[0] > 60:
            user_requests.popleft()
        
        # Check if user exceeded rate limit
        if len(user_requests) >= self.USER_RATE_LIMIT:
            # Apply cooldown
            self.user_cooldowns[user_id] = current_time + self.USER_COOLDOWN
            logger.warning(f"User {user_id} rate limited - too many requests")
            return True, self.USER_COOLDOWN
        
        # Check for spam pattern (many requests in short time)
        recent_requests = [req for req in user_requests if current_time - req < 10]  # Last 10 seconds
        if len(recent_requests) >= self.SPAM_THRESHOLD:
            # Ban user for spam
            self.spam_users[user_id] = current_time + self.SPAM_BAN_DURATION
            logger.warning(f"User {user_id} banned for spam - {len(recent_requests)} requests in 10 seconds")
            return True, self.SPAM_BAN_DURATION
        
        return False, None
    
    def is_globally_rate_limited(self) -> tuple[bool, Optional[float]]:
        """Check if system is globally rate limited"""
        current_time = time.time()
        
        # Remove old requests (older than 1 minute)
        while self.global_requests and current_time - self.global_requests[0] > 60:
            self.global_requests.popleft()
        
        # Check if system exceeded global rate limit
        if len(self.global_requests) >= self.GLOBAL_RATE_LIMIT:
            logger.warning(f"Global rate limit exceeded - {len(self.global_requests)} requests in last minute")
            return True, 60.0  # Wait 1 minute
        
        return False, None
    
    def record_request(self, user_id: int):
        """Record a user request"""
        current_time = time.time()
        self.user_requests[user_id].append(current_time)
        self.global_requests.append(current_time)
    
    def cleanup_old_data(self):
        """Clean up old rate limiting data"""
        current_time = time.time()
        
        # Clean up old cooldowns
        expired_cooldowns = [uid for uid, end_time in self.user_cooldowns.items() if current_time > end_time]
        for uid in expired_cooldowns:
            del self.user_cooldowns[uid]
        
        # Clean up old spam bans
        expired_bans = [uid for uid, end_time in self.spam_users.items() if current_time > end_time]
        for uid in expired_bans:
            del self.spam_users[uid]
        
        # Clean up old user request history
        users_to_clean = []
        for uid, requests in self.user_requests.items():
            # Remove old requests
            while requests and current_time - requests[0] > 300:  # 5 minutes
                requests.popleft()
            # Remove empty request histories
            if not requests:
                users_to_clean.append(uid)
        
        for uid in users_to_clean:
            del self.user_requests[uid]

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(func):
    """Decorator to apply rate limiting to functions"""
    @wraps(func)
    async def wrapper(self, interaction, *args, **kwargs):
        user_id = interaction.user.id
        
        # Check user rate limit
        is_limited, wait_time = rate_limiter.is_user_rate_limited(user_id)
        if is_limited:
            if wait_time > 60:  # Long ban (spam)
                embed_title = "🚫 Temporary Ban"
                embed_desc = f"You've been temporarily banned for spam. Try again in {wait_time/60:.1f} minutes."
                embed_color = 0xff0000
            else:  # Regular rate limit
                embed_title = "⏰ Rate Limited"
                embed_desc = f"Please wait {wait_time:.0f} seconds before using this command again."
                embed_color = 0xff9900
            
            embed = discord.Embed(title=embed_title, description=embed_desc, color=embed_color)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check global rate limit
        is_global_limited, global_wait = rate_limiter.is_globally_rate_limited()
        if is_global_limited:
            embed = discord.Embed(
                title="🌐 System Busy", 
                description="System is currently handling high load. Please try again in a moment.",
                color=0xff9900
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Record the request
        rate_limiter.record_request(user_id)
        
        try:
            # Execute the original function
            return await func(self, interaction, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in rate-limited function {func.__name__}: {e}")
            # Don't count failed requests against rate limit
            if rate_limiter.user_requests[user_id]:
                rate_limiter.user_requests[user_id].pop()
            if rate_limiter.global_requests:
                rate_limiter.global_requests.pop()
            raise
    
    return wrapper

# Cleanup task
async def cleanup_rate_limiter():
    """Background task to clean up old rate limiting data"""
    while True:
        try:
            rate_limiter.cleanup_old_data()
            await asyncio.sleep(300)  # Clean up every 5 minutes
        except Exception as e:
            logger.error(f"Error in rate limiter cleanup: {e}")
            await asyncio.sleep(60)  # Retry in 1 minute 