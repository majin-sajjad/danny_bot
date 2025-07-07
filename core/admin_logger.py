"""
Admin logging system for Danny Bot.
Handles all administrative logging to dedicated admin channels.
"""

import discord
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AdminLogger:
    """Handles all administrative logging for the bot."""
    
    def __init__(self, bot):
        self.bot = bot
        self.admin_channels = {}
        
    async def initialize_admin_channels(self, guild):
        """Find and cache admin channels for logging"""
        try:
            # Find admin category
            admin_category = discord.utils.get(guild.categories, name="🔧 ADMIN")
            if not admin_category:
                logger.warning("Admin category not found - admin logging disabled")
                return
            
            # Cache admin channels
            for channel in admin_category.channels:
                if "bot-commands" in channel.name:
                    self.admin_channels['commands'] = channel
                elif "bot-logs" in channel.name:
                    self.admin_channels['logs'] = channel
                elif "user-management" in channel.name:
                    self.admin_channels['users'] = channel
            
            logger.info(f"Admin channels initialized: {list(self.admin_channels.keys())}")
            
            # Send startup notification
            await self.log_bot_event("🤖 **Danny Bot Started**", 
                                   f"Bot connected successfully with admin monitoring active.\n"
                                   f"**Guilds:** {len(self.bot.guilds)}\n"
                                   f"**Admin Channels:** {len(self.admin_channels)} active", 
                                   "logs")
        except Exception as e:
            logger.error(f"Failed to initialize admin channels: {e}")
    
    async def log_bot_event(self, title, description, channel_type="logs"):
        """Log general bot events to bot-logs"""
        await self._send_admin_log(title, description, channel_type, 0x3498db)
    
    async def log_user_event(self, title, description, user=None, channel_type="users"):
        """Log user-related events to user-management"""
        if user:
            description = f"**User:** {user.display_name} ({user.mention})\n{description}"
        await self._send_admin_log(title, description, channel_type, 0x00ff88)
    
    async def log_registration(self, user, registration_data):
        """Log new user registrations with details"""
        first_name, last_name, phone, email, company = registration_data
        
        embed = discord.Embed(
            title="📝 New User Registration",
            description=f"**{first_name} {last_name}** has completed registration",
            color=0x00ff88
        )
        embed.add_field(
            name="📱 Contact Info",
            value=f"**Phone:** {phone}\n**Email:** {email or 'Not provided'}\n**Company:** {company or 'Not provided'}",
            inline=False
        )
        embed.add_field(
            name="🔗 Discord Info",
            value=f"**User:** {user.mention}\n**ID:** {user.id}\n**Joined:** {user.joined_at.strftime('%Y-%m-%d') if user.joined_at else 'Unknown'}",
            inline=False
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Registration logged at {datetime.now().strftime('%H:%M:%S')}")
        
        await self._send_admin_embed(embed, "users")
    
    async def log_practice_completion(self, user, session_data):
        """Log practice session completions with scores"""
        embed = discord.Embed(
            title="🎯 Practice Session Completed",
            description=f"**{user.display_name}** finished a practice session",
            color=0x3498db
        )
        
        # Add session details
        if session_data.get('personality'):
            embed.add_field(
                name="🎭 Session Details",
                value=f"**Personality:** {session_data['personality'].capitalize()}\n**Duration:** {session_data.get('duration', 'Unknown')}\n**Exchanges:** {session_data.get('conversation_count', 0)}",
                inline=True
            )
        
        # Add score breakdown
        if session_data.get('overall_score'):
            score_color = "🟢" if session_data['overall_score'] >= 70 else "🟡" if session_data['overall_score'] >= 50 else "🔴"
            embed.add_field(
                name="📊 Performance",
                value=f"**Score:** {score_color} {session_data['overall_score']}/100\n**Grade:** {session_data.get('grade', 'N/A')}\n**User:** {user.mention}",
                inline=True
            )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Session completed at {datetime.now().strftime('%H:%M:%S')}")
        
        await self._send_admin_embed(embed, "logs")
    
    async def log_error(self, error_type, description, user=None):
        """Log errors and issues to bot-logs"""
        embed = discord.Embed(
            title=f"⚠️ {error_type}",
            description=description,
            color=0xe74c3c
        )
        if user:
            embed.add_field(
                name="👤 User Info",
                value=f"**User:** {user.mention}\n**ID:** {user.id}",
                inline=False
            )
        embed.set_footer(text=f"Error logged at {datetime.now().strftime('%H:%M:%S')}")
        
        await self._send_admin_embed(embed, "logs")
    
    async def log_user_join(self, member):
        """Log when new users join"""
        embed = discord.Embed(
            title="👋 New Member Joined",
            description=f"**{member.display_name}** joined the server",
            color=0x00ff88
        )
        embed.add_field(
            name="📊 Member Info",
            value=f"**Account Created:** {member.created_at.strftime('%Y-%m-%d')}\n**Total Members:** {member.guild.member_count}",
            inline=False
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Joined at {datetime.now().strftime('%H:%M:%S')}")
        
        await self._send_admin_embed(embed, "users")
    
    async def log_member_join(self, member):
        """Log when a member joins - alias for log_user_join"""
        await self.log_user_join(member)
    
    async def log_member_leave(self, member):
        """Log when a member leaves - alias for log_user_leave"""
        await self.log_user_leave(member)
    
    async def log_user_leave(self, member, registration_data=None):
        """Log when users leave (especially registered ones)"""
        embed = discord.Embed(
            title="👋 Member Left Server",
            description=f"**{member.display_name}** left the server",
            color=0xffa500
        )
        
        if registration_data:
            first_name, last_name, reg_date = registration_data
            embed.add_field(
                name="📝 Was Registered",
                value=f"**Name:** {first_name} {last_name}\n**Registered:** {reg_date}\n**Status:** Registration data preserved",
                inline=False
            )
            embed.color = 0xff6b6b  # Red for registered user leaving
        
        embed.add_field(
            name="📊 Member Info",
            value=f"**User ID:** {member.id}\n**Remaining Members:** {member.guild.member_count}",
            inline=False
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Left at {datetime.now().strftime('%H:%M:%S')}")
        
        await self._send_admin_embed(embed, "users")
    
    async def log_training_zone_created(self, user, category):
        """Log when user training zones are created"""
        await self.log_user_event(
            "🏗️ Training Zone Created",
            f"Private training zone created: {category.mention}\n**Channels:** {len(category.channels)}\n**Status:** Ready for training",
            user
        )
    
    async def _send_admin_log(self, title, description, channel_type, color):
        """Send a simple log message to admin channel"""
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=f"Logged at {datetime.now().strftime('%H:%M:%S')}")
        await self._send_admin_embed(embed, channel_type)
    
    async def _send_admin_embed(self, embed, channel_type):
        """Send embed to specified admin channel"""
        try:
            channel = self.admin_channels.get(channel_type)
            if channel:
                await channel.send(embed=embed)
            else:
                logger.warning(f"Admin channel '{channel_type}' not found for logging")
        except Exception as e:
            logger.error(f"Failed to send admin log to {channel_type}: {e}") 