"""
Tournament Management System
"""

import logging
from datetime import datetime, timedelta
from discord.ext import tasks
from .database import LeaderboardDatabase
import pytz

logger = logging.getLogger(__name__)

class TournamentManager:
    """Manages tournament weeks, resets, and scheduling"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = LeaderboardDatabase()
    
    async def initialize_tournaments(self):
        """Initialize tournament system for all guilds"""
        for guild in self.bot.guilds:
            await self.initialize_guild_tournament(guild.id)
    
    async def initialize_guild_tournament(self, guild_id: int):
        """Initialize tournament for a specific guild"""
        try:
            week_num = await self.db.get_current_week_number(guild_id)
            start_date = await self.db.get_week_start_date(guild_id)
            
            await self.db.initialize_tournament_week(guild_id, week_num, start_date)
            logger.info(f"Initialized tournament week {week_num} for guild {guild_id}")
            
        except Exception as e:
            logger.error(f"Error initializing tournament for guild {guild_id}: {e}")
    
    def start_background_tasks(self):
        """Start background tasks for tournament management"""
        self.daily_update.start()
        self.weekly_reset.start()
        self.periodic_leaderboard_update.start()
    
    def stop_background_tasks(self):
        """Stop background tasks"""
        if self.daily_update.is_running():
            self.daily_update.cancel()
        if self.weekly_reset.is_running():
            self.weekly_reset.cancel()
        if self.periodic_leaderboard_update.is_running():
            self.periodic_leaderboard_update.cancel()
    
    @tasks.loop(hours=24)
    async def daily_update(self):
        """Daily leaderboard snapshot for all guilds"""
        try:
            for guild in self.bot.guilds:
                try:
                    leaderboard_data = await self.db.get_leaderboard_data('week', guild.id)
                    current_week = await self.db.get_current_week_number(guild.id)
                    today = datetime.now().strftime('%Y-%m-%d')
                    
                    await self.db.save_leaderboard_snapshot(guild.id, leaderboard_data, current_week, today)
                    logger.info(f"Daily snapshot taken for guild {guild.name}")
                    
                except Exception as e:
                    logger.error(f"Error taking daily snapshot for guild {guild.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in daily update task: {e}")
    
    @tasks.loop(hours=168)  # Weekly (7 days * 24 hours)
    async def weekly_reset(self):
        """Weekly tournament reset for all guilds"""
        try:
            for guild in self.bot.guilds:
                try:
                    await self.reset_guild_tournament(guild.id)
                    logger.info(f"Weekly reset completed for guild {guild.name}")
                    
                except Exception as e:
                    logger.error(f"Error in weekly reset for guild {guild.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in weekly reset task: {e}")
    
    async def reset_guild_tournament(self, guild_id: int):
        """Reset tournament for a specific guild"""
        try:
            # Get current week and create new week
            current_week = await self.db.get_current_week_number(guild_id)
            new_week = current_week + 1
            new_start_date = datetime.now().strftime('%Y-%m-%d')
            
            # Initialize new tournament week
            await self.db.initialize_tournament_week(guild_id, new_week, new_start_date)
            
            # Archive current leaderboard
            leaderboard_data = await self.db.get_leaderboard_data('week', guild_id, current_week)
            await self.db.save_leaderboard_snapshot(guild_id, leaderboard_data, current_week, new_start_date)
            
            logger.info(f"Tournament reset: Guild {guild_id} moved from week {current_week} to {new_week}")
            
        except Exception as e:
            logger.error(f"Error resetting tournament for guild {guild_id}: {e}")
    
    @tasks.loop(hours=3)
    async def periodic_leaderboard_update(self):
        """Update public leaderboards every 3 hours from 6AM-6PM Pacific"""
        try:
            # Get current time in Pacific timezone
            pacific_tz = pytz.timezone('America/Los_Angeles')
            current_time = datetime.now(pacific_tz)
            current_hour = current_time.hour
            
            # Only update between 6AM and 6PM Pacific (6-18 hours)
            if not (6 <= current_hour <= 18):
                logger.info(f"Skipping leaderboard update - outside business hours ({current_hour}:00 Pacific)")
                return
            
            # Get leaderboard display from any guild's leaderboard manager
            leaderboard_cog = None
            for cog_name, cog in self.bot.cogs.items():
                if 'leaderboard' in cog_name.lower():
                    leaderboard_cog = cog
                    break
            
            if not leaderboard_cog or not hasattr(leaderboard_cog, 'display'):
                logger.error("Could not find leaderboard cog for periodic update")
                return
            
            # Update leaderboard for all guilds
            updated_count = 0
            for guild in self.bot.guilds:
                try:
                    await leaderboard_cog.display.update_public_leaderboard(guild.id)
                    updated_count += 1
                    logger.info(f"Updated public leaderboard for guild {guild.name}")
                except Exception as e:
                    logger.error(f"Error updating leaderboard for guild {guild.name}: {e}")
            
            logger.info(f"Periodic leaderboard update completed - {updated_count} guilds updated at {current_hour}:00 Pacific")
                    
        except Exception as e:
            logger.error(f"Error in periodic leaderboard update task: {e}")
    
    @daily_update.before_loop
    async def before_daily_update(self):
        await self.bot.wait_until_ready()
    
    @weekly_reset.before_loop  
    async def before_weekly_reset(self):
        await self.bot.wait_until_ready()
    
    @periodic_leaderboard_update.before_loop
    async def before_periodic_leaderboard_update(self):
        await self.bot.wait_until_ready()
    
    async def get_tournament_stats(self, guild_id: int) -> dict:
        """Get tournament statistics for a guild"""
        try:
            current_week = await self.db.get_current_week_number(guild_id)
            start_date = await self.db.get_week_start_date(guild_id)
            leaderboard_data = await self.db.get_leaderboard_data('week', guild_id)
            
            return {
                'current_week': current_week,
                'start_date': start_date,
                'participants': len(leaderboard_data),
                'total_deals': sum(entry.get('total_deals', 0) for entry in leaderboard_data),
                'total_points': sum(entry.get('total_points', 0) for entry in leaderboard_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting tournament stats for guild {guild_id}: {e}")
            return {} 