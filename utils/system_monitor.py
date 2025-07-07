"""
System Health Monitor for Danny Bot
Monitors system performance and health for 100+ user capacity
"""

import asyncio
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiosqlite

logger = logging.getLogger(__name__)

class SystemHealthMonitor:
    """Monitor system health and performance"""
    
    def __init__(self, db_path: str = 'danny_bot.db'):
        self.db_path = db_path
        self.start_time = time.time()
        self.health_metrics = {
            'total_users': 0,
            'active_users_24h': 0,
            'total_commands': 0,
            'errors_24h': 0,
            'avg_response_time': 0.0,
            'memory_usage_mb': 0.0,
            'cpu_usage_percent': 0.0,
            'database_size_mb': 0.0,
            'uptime_hours': 0.0
        }
        self.performance_history: List[Dict] = []
        self.error_count = 0
        self.command_count = 0
        self.response_times: List[float] = []
        
    async def get_system_health(self) -> Dict:
        """Get comprehensive system health metrics"""
        try:
            # Update basic metrics
            self.health_metrics['uptime_hours'] = (time.time() - self.start_time) / 3600
            self.health_metrics['memory_usage_mb'] = psutil.virtual_memory().used / 1024 / 1024
            self.health_metrics['cpu_usage_percent'] = psutil.cpu_percent(interval=1)
            
            # Database metrics
            await self._update_database_metrics()
            
            # Performance metrics
            if self.response_times:
                self.health_metrics['avg_response_time'] = sum(self.response_times) / len(self.response_times)
                # Keep only recent response times
                if len(self.response_times) > 100:
                    self.response_times = self.response_times[-50:]
            
            self.health_metrics['total_commands'] = self.command_count
            self.health_metrics['errors_24h'] = self.error_count
            
            return self.health_metrics.copy()
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return self.health_metrics.copy()
    
    async def _update_database_metrics(self):
        """Update database-related metrics"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Database size
                cursor = await db.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = await cursor.fetchone()
                self.health_metrics['database_size_mb'] = db_size[0] / 1024 / 1024
                
                # Total users
                cursor = await db.execute("SELECT COUNT(*) FROM user_registrations")
                total_users = await cursor.fetchone()
                self.health_metrics['total_users'] = total_users[0]
                
                # Active users in last 24 hours (based on recent deals)
                yesterday = datetime.now() - timedelta(days=1)
                cursor = await db.execute("""
                    SELECT COUNT(DISTINCT user_id) FROM deals 
                    WHERE deal_date > ?
                """, (yesterday.isoformat(),))
                active_users = await cursor.fetchone()
                self.health_metrics['active_users_24h'] = active_users[0] if active_users[0] else 0
                
        except Exception as e:
            logger.error(f"Error updating database metrics: {e}")
    
    def record_command(self, response_time: float = None):
        """Record a command execution"""
        self.command_count += 1
        if response_time:
            self.response_times.append(response_time)
    
    def record_error(self):
        """Record an error occurrence"""
        self.error_count += 1
    
    async def check_system_limits(self) -> Dict[str, bool]:
        """Check if system is approaching limits"""
        health = await self.get_system_health()
        
        warnings = {
            'high_memory': health['memory_usage_mb'] > 1024,  # > 1GB
            'high_cpu': health['cpu_usage_percent'] > 80,
            'slow_responses': health['avg_response_time'] > 5.0,  # > 5 seconds
            'many_errors': health['errors_24h'] > 50,
            'large_database': health['database_size_mb'] > 100,  # > 100MB
        }
        
        return warnings
    
    async def get_performance_report(self) -> str:
        """Get a formatted performance report"""
        health = await self.get_system_health()
        warnings = await self.check_system_limits()
        
        report = f"""
🏥 **SYSTEM HEALTH REPORT**
═══════════════════════════════

📊 **Performance Metrics**
• Uptime: {health['uptime_hours']:.1f} hours
• Total Users: {health['total_users']}
• Active Users (24h): {health['active_users_24h']}
• Total Commands: {health['total_commands']}
• Avg Response Time: {health['avg_response_time']:.2f}s

💻 **System Resources**
• Memory Usage: {health['memory_usage_mb']:.1f} MB
• CPU Usage: {health['cpu_usage_percent']:.1f}%
• Database Size: {health['database_size_mb']:.2f} MB

⚠️ **System Warnings**
"""
        
        if any(warnings.values()):
            for warning, active in warnings.items():
                if active:
                    report += f"• {warning.replace('_', ' ').title()}: ⚠️ WARNING\n"
                else:
                    report += f"• {warning.replace('_', ' ').title()}: ✅ OK\n"
        else:
            report += "• All systems operating normally ✅\n"
        
        report += f"""
🎯 **Capacity Status**
• Current capacity: {health['total_users']}/100+ users
• System load: {'HIGH' if warnings['high_cpu'] or warnings['high_memory'] else 'NORMAL'}
• Error rate: {health['errors_24h']} errors/24h
"""
        
        return report
    
    async def save_performance_snapshot(self):
        """Save current performance metrics for historical tracking"""
        health = await self.get_system_health()
        health['timestamp'] = datetime.now().isoformat()
        
        self.performance_history.append(health)
        
        # Keep only last 24 snapshots (if taken hourly)
        if len(self.performance_history) > 24:
            self.performance_history = self.performance_history[-24:]
    
    async def emergency_shutdown_check(self) -> bool:
        """Check if system should emergency shutdown"""
        warnings = await self.check_system_limits()
        
        # Emergency conditions
        emergency_conditions = [
            warnings['high_memory'] and warnings['high_cpu'],  # Both high
            self.error_count > 100,  # Too many errors
            warnings['slow_responses'] and warnings['many_errors']  # Poor performance + errors
        ]
        
        if any(emergency_conditions):
            logger.critical("EMERGENCY SHUTDOWN CONDITIONS DETECTED!")
            return True
        
        return False

# Global system monitor
system_monitor = SystemHealthMonitor()

# Background monitoring task
async def monitor_system_health():
    """Background task to monitor system health"""
    while True:
        try:
            # Save performance snapshot every hour
            await system_monitor.save_performance_snapshot()
            
            # Check for emergency conditions
            should_shutdown = await system_monitor.emergency_shutdown_check()
            if should_shutdown:
                logger.critical("INITIATING EMERGENCY SHUTDOWN!")
                # Implement emergency shutdown logic here
                break
            
            # Log health status every hour
            warnings = await system_monitor.check_system_limits()
            if any(warnings.values()):
                logger.warning(f"System warnings detected: {warnings}")
            
            await asyncio.sleep(3600)  # Check every hour
            
        except Exception as e:
            logger.error(f"Error in system health monitoring: {e}")
            await asyncio.sleep(60)  # Retry in 1 minute

def performance_tracker(func):
    """Decorator to track function performance"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            response_time = time.time() - start_time
            system_monitor.record_command(response_time)
            return result
        except Exception as e:
            system_monitor.record_error()
            response_time = time.time() - start_time
            system_monitor.record_command(response_time)
            raise
    
    return wrapper 