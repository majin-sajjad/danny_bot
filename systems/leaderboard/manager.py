"""
Main Leaderboard Manager
"""

import discord
from discord.ext import commands
import logging
from typing import List, Dict, Optional
from models import LeaderboardEntry
from .database import LeaderboardDatabase
from .tournament import TournamentManager
from .calculator import PointsCalculator
from .display import LeaderboardDisplay

logger = logging.getLogger(__name__)

class LeaderboardManager(commands.Cog):
    """Main coordinator for the leaderboard system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = LeaderboardDatabase()
        self.tournament = TournamentManager(bot)
        self.calculator = PointsCalculator()
        self.display = LeaderboardDisplay(bot)
        
    async def cog_load(self):
        """Called when the cog is loaded"""
        await self.db.setup_database()
        await self.tournament.initialize_tournaments()
        self.tournament.start_background_tasks()
        logger.info("Leaderboard system loaded successfully")
    
    async def cog_unload(self):
        """Called when the cog is unloaded"""
        self.tournament.stop_background_tasks()
        logger.info("Leaderboard system unloaded")
    
    # ============================================
    # DEAL SUBMISSION COMMANDS
    # ============================================
    
    # NOTE: !deal command removed - use deal submission UI buttons instead
    # Full functionality is now available through the deal submission UI buttons
    # Users should use the "📝 Submit Deal" button in their deal-submission channel
    pass
    
    @commands.command(name='leaderboard', aliases=['lb'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def show_leaderboard(self, ctx, timeframe: str = "week"):
        """Show the current leaderboard"""
        try:
            await self.display.show_leaderboard(ctx, timeframe)
        except Exception as e:
            logger.error(f"Error showing leaderboard: {e}")
            await ctx.send("❌ Error displaying leaderboard.")
    
    @commands.command(name='mystats')
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def show_user_stats(self, ctx):
        """Show user's personal statistics"""
        try:
            await self.display.show_user_stats(ctx, ctx.author.id)
        except Exception as e:
            logger.error(f"Error showing user stats: {e}")
            await ctx.send("❌ Error displaying your statistics.")
    
    # ============================================
    # ADMIN COMMANDS
    # ============================================
    
    @commands.command(name='admin_add_deal')
    @commands.has_permissions(administrator=True)
    async def admin_add_deal(self, ctx, user_mention: str, deal_type: str, *, description: str):
        """Admin command to add a deal for another user"""
        try:
            # Parse user mention
            user_id = int(user_mention.strip('<@!>'))
            user = ctx.guild.get_member(user_id)
            
            if not user:
                await ctx.send("❌ User not found.")
                return
            
            # Get user's niche
            user_niche = await self._get_user_niche(user_id)
            if not user_niche:
                user_niche = 'solar'
            
            # Calculate points
            points = self.calculator.calculate_points(deal_type, user_niche)
            
            # Get current week
            current_week = await self.db.get_current_week_number(ctx.guild.id)
            
            # Insert deal with admin flag
            deal_id = await self.db.insert_deal(
                guild_id=ctx.guild.id,
                user_id=user_id,
                username=user.display_name,
                deal_type=deal_type,
                niche=user_niche,
                points=points,
                description=description,
                week_number=current_week,
                admin_submitted=True,
                admin_user_id=ctx.author.id
            )
            
            await ctx.send(f"✅ Deal added for {user.display_name}: {points} points")
            
            # Update public leaderboard
            await self.display.update_public_leaderboard(ctx.guild.id)
            
        except Exception as e:
            logger.error(f"Error adding admin deal: {e}")
            await ctx.send("❌ Error adding deal.")
    
    @commands.command(name='tournament_stats')
    @commands.has_permissions(administrator=True)
    async def show_tournament_stats(self, ctx):
        """Show tournament statistics"""
        try:
            stats = await self.tournament.get_tournament_stats(ctx.guild.id)
            
            embed = discord.Embed(
                title="🏆 Tournament Statistics",
                color=0xffd700
            )
            
            embed.add_field(
                name="📊 Current Week",
                value=f"Week {stats['current_week']} (Started: {stats['start_date']})",
                inline=False
            )
            
            embed.add_field(
                name="👥 Participation",
                value=f"**Participants:** {stats['participants']}\n**Total Deals:** {stats['total_deals']}\n**Total Points:** {stats['total_points']}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing tournament stats: {e}")
            await ctx.send("❌ Error retrieving tournament statistics.")
    
    @commands.command(name='reset_tournament')
    @commands.has_permissions(administrator=True)
    async def reset_tournament(self, ctx):
        """Manually reset the tournament for this guild"""
        try:
            await self.tournament.reset_guild_tournament(ctx.guild.id)
            await ctx.send("✅ Tournament reset successfully!")
            
        except Exception as e:
            logger.error(f"Error resetting tournament: {e}")
            await ctx.send("❌ Error resetting tournament.")
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    async def _get_user_niche(self, user_id: int) -> Optional[str]:
        """Get user's niche from registration"""
        try:
            # This would connect to the user registration system
            # For now, return default
            return 'solar'
        except Exception as e:
            logger.error(f"Error getting user niche: {e}")
            return 'solar'
    
    async def _get_current_discord_username(self, user_id: int, guild_id: int) -> str:
        """Get current Discord display name for a user"""
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return "Unknown User"
            
            member = guild.get_member(user_id)
            return member.display_name if member else "Former Member"
            
        except Exception:
            return "Unknown User"


async def setup(bot):
    """Setup function for the leaderboard manager"""
    await bot.add_cog(LeaderboardManager(bot)) 