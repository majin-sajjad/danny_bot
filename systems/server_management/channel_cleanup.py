import discord
from discord.ext import commands, tasks
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ChannelCleanupManager:
    """Manages automatic cleanup of training zone channels"""
    
    def __init__(self, bot):
        self.bot = bot
        self.channel_activity = {}  # Track last activity per channel
        self.cleanup_interval = 30  # minutes before cleanup
        self.cleanup_task.start()  # Start the cleanup task
        
    def cog_unload(self):
        """Clean up when manager is unloaded"""
        self.cleanup_task.cancel()
        
    @tasks.loop(minutes=15)  # Check every 15 minutes
    async def cleanup_task(self):
        """Periodically clean up idle training zone channels"""
        try:
            for guild in self.bot.guilds:
                await self.cleanup_idle_channels(guild)
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
    
    @cleanup_task.before_loop
    async def before_cleanup_task(self):
        """Wait until bot is ready before starting cleanup task"""
        await self.bot.wait_until_ready()
    
    async def cleanup_idle_channels(self, guild):
        """Clean up channels that have been idle for too long"""
        now = datetime.now()
        cleanup_threshold = timedelta(minutes=self.cleanup_interval)
        
        # Channel types that should be cleaned up
        cleanup_channel_types = [
            "💪practice-arena",
            "🛠️playground-library", 
            "📊my-progress",
            "💰deal-submission"
        ]
        
        for category in guild.categories:
            if "Training Zone" in category.name:
                for channel in category.channels:
                    if isinstance(channel, discord.TextChannel):
                        # Check if this is a channel type we should clean
                        should_cleanup = any(channel_type in channel.name for channel_type in cleanup_channel_types)
                        
                        if should_cleanup:
                            # Get last activity time
                            last_activity = self.channel_activity.get(channel.id, now)
                            time_since_activity = now - last_activity
                            
                            if time_since_activity > cleanup_threshold:
                                await self.cleanup_channel_messages(channel)
    
    async def cleanup_channel_messages(self, channel):
        """Clean up old messages in a channel, preserving the welcome message"""
        try:
            # Get all messages
            messages = []
            async for message in channel.history(limit=None, oldest_first=True):
                messages.append(message)
            
            if len(messages) <= 1:
                # Only welcome message, nothing to clean
                return
            
            # Keep the first message (welcome message with buttons) and delete the rest
            messages_to_delete = messages[1:]  # Skip the first message
            
            if messages_to_delete:
                # Delete messages in batches (Discord limitation)
                while messages_to_delete:
                    batch = messages_to_delete[:100]  # Discord allows max 100 messages at once
                    messages_to_delete = messages_to_delete[100:]
                    
                    # Delete messages newer than 14 days bulk, older ones individually
                    bulk_messages = []
                    old_messages = []
                    
                    for msg in batch:
                        age = datetime.now() - msg.created_at.replace(tzinfo=None)
                        if age.days < 14:
                            bulk_messages.append(msg)
                        else:
                            old_messages.append(msg)
                    
                    # Bulk delete newer messages
                    if bulk_messages:
                        await channel.delete_messages(bulk_messages)
                    
                    # Individual delete for older messages
                    for msg in old_messages:
                        try:
                            await msg.delete()
                        except discord.NotFound:
                            pass  # Message already deleted
                        except discord.Forbidden:
                            pass  # No permission to delete
                        await asyncio.sleep(0.5)  # Rate limit protection
                
                logger.info(f"Cleaned up {len(messages_to_delete)} messages from {channel.name}")
                
                # Send a subtle cleanup notification
                cleanup_embed = discord.Embed(
                    title="🧹 Channel Cleaned",
                    description="This channel has been automatically cleaned to maintain a fresh interface.",
                    color=0x95a5a6
                )
                cleanup_embed.set_footer(text="Messages are cleaned after 30 minutes of inactivity")
                
                cleanup_msg = await channel.send(embed=cleanup_embed, delete_after=10)
                
        except Exception as e:
            logger.error(f"Error cleaning up channel {channel.name}: {e}")
    
    def track_channel_activity(self, channel_id):
        """Update the last activity time for a channel"""
        self.channel_activity[channel_id] = datetime.now()
    
    async def on_message(self, message):
        """Track channel activity when messages are sent"""
        if message.author.bot:
            return
            
        # Track activity for training zone channels
        if message.channel.category and "Training Zone" in message.channel.category.name:
            cleanup_channel_types = [
                "💪practice-arena",
                "🛠️playground-library", 
                "📊my-progress",
                "💰deal-submission"
            ]
            
            should_track = any(channel_type in message.channel.name for channel_type in cleanup_channel_types)
            if should_track:
                self.track_channel_activity(message.channel.id)
    
    async def manual_cleanup(self, channel):
        """Manually trigger cleanup for a specific channel"""
        # Check if it's a training zone channel that should be cleaned
        cleanup_channel_types = [
            "💪practice-arena",
            "🛠️playground-library", 
            "📊my-progress",
            "💰deal-submission"
        ]
        
        should_cleanup = any(channel_type in channel.name for channel_type in cleanup_channel_types)
        
        if not should_cleanup:
            return False, "This channel type doesn't support auto-cleanup."
        
        await self.cleanup_channel_messages(channel)
        return True, "Channel cleanup completed!"
    
    def set_cleanup_interval(self, minutes):
        """Set the cleanup interval in minutes"""
        if minutes < 5:
            return False, "Cleanup interval must be at least 5 minutes."
        if minutes > 1440:  # 24 hours
            return False, "Cleanup interval cannot exceed 24 hours (1440 minutes)."
            
        self.cleanup_interval = minutes
        logger.info(f"Cleanup interval changed to {minutes} minutes")
        return True, f"Cleanup interval set to {minutes} minutes."
    
    def get_cleanup_status(self):
        """Get cleanup system status information"""
        total_tracked = len(self.channel_activity)
        active_channels = 0
        now = datetime.now()
        
        for channel_id, last_activity in self.channel_activity.items():
            time_since_activity = now - last_activity
            if time_since_activity.total_seconds() < (self.cleanup_interval * 60):
                active_channels += 1
        
        return {
            'cleanup_interval': self.cleanup_interval,
            'total_tracked_channels': total_tracked,
            'active_channels': active_channels,
            'task_running': not self.cleanup_task.is_being_cancelled()
        } 