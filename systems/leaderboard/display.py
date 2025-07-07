"""
Leaderboard Display System
"""

import discord
import logging
from typing import List, Dict, Optional
from models import LeaderboardEntry
from .database import LeaderboardDatabase

logger = logging.getLogger(__name__)

class LeaderboardDisplay:
    """Handles formatting and displaying leaderboards"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = LeaderboardDatabase()
    
    async def show_leaderboard(self, ctx, timeframe: str = "week"):
        """Display leaderboard for the specified timeframe"""
        try:
            # Validate timeframe
            if timeframe not in ['week', 'today']:
                timeframe = 'week'
            
            # Get leaderboard data
            leaderboard_data = await self.db.get_leaderboard_data(timeframe, ctx.guild.id)
            
            if not leaderboard_data:
                embed = discord.Embed(
                    title="🏆 Leaderboard",
                    description="No deals logged yet! Be the first to submit a deal.",
                    color=0xffd700
                )
                await ctx.send(embed=embed)
                return
            
            # Convert to LeaderboardEntry objects
            leaderboard = []
            for i, entry in enumerate(leaderboard_data, 1):
                # Get current Discord display name
                display_name = await self._get_current_discord_username(entry['user_id'], ctx.guild.id)
                
                leaderboard.append(LeaderboardEntry(
                    user_id=entry['user_id'],
                    username=display_name,
                    total_points=entry['total_points'],
                    standard_deals=entry['standard_deals'],
                    self_generated_deals=entry['self_generated_deals'],
                    total_deals=entry['total_deals'],
                    rank=i
                ))
            
            # Create and send embed
            embed = self._create_leaderboard_embed(leaderboard, timeframe, ctx.guild.id)
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing leaderboard: {e}")
            raise
    
    async def show_user_stats(self, ctx, user_id: int):
        """Display detailed user statistics"""
        try:
            stats = await self.db.get_user_stats(user_id, ctx.guild.id)
            
            if not stats:
                await ctx.send("❌ No statistics found. Submit your first deal to get started!")
                return
            
            # Get user info
            user = ctx.guild.get_member(user_id)
            display_name = user.display_name if user else "Unknown User"
            
            embed = discord.Embed(
                title=f"📊 Statistics for {display_name}",
                color=0x3498db
            )
            
            # Process statistics
            all_time_stats = self._process_user_stats(stats['all_time'])
            week_stats = self._process_user_stats(stats['current_week'])
            
            # All-time stats
            embed.add_field(
                name="🏆 All-Time Performance",
                value=f"**Total Points:** {all_time_stats['total_points']}\n"
                      f"**Total Deals:** {all_time_stats['total_deals']}\n"
                      f"**Setter Deals:** {all_time_stats['setter_deals']}\n"
                      f"**Closer Deals:** {all_time_stats['closer_deals']}\n"
                      f"**Self-Gen Deals:** {all_time_stats['self_gen_deals']}",
                inline=True
            )
            
            # Current week stats
            embed.add_field(
                name=f"📅 Week {stats['week_number']} Performance",
                value=f"**Points:** {week_stats['total_points']}\n"
                      f"**Deals:** {week_stats['total_deals']}\n"
                      f"**Setter:** {week_stats['setter_deals']}\n"
                      f"**Closer:** {week_stats['closer_deals']}\n"
                      f"**Self-Gen:** {week_stats['self_gen_deals']}",
                inline=True
            )
            
            # Niche breakdown
            if all_time_stats['niche_breakdown']:
                niche_text = ""
                for niche, niche_stats in all_time_stats['niche_breakdown'].items():
                    emoji = self._get_niche_emoji(niche)
                    niche_text += f"{emoji} **{niche.title()}:** {niche_stats['points']} pts ({niche_stats['deals']} deals)\n"
                
                embed.add_field(
                    name="🎯 Niche Breakdown",
                    value=niche_text,
                    inline=False
                )
            
            embed.set_footer(text=f"Keep up the great work! • Week {stats['week_number']}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing user stats: {e}")
            raise
    
    async def update_public_leaderboard(self, guild_id: int):
        """Update the public leaderboard channel with automatic refresh"""
        try:
            # Find public leaderboard channel
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return
            
            public_channel = None
            for channel in guild.text_channels:
                if "public-leaderboard" in channel.name.lower() or "leaderboard" in channel.name.lower():
                    public_channel = channel
                    break
            
            if not public_channel:
                logger.info(f"No public leaderboard channel found in guild {guild_id}")
                return
            
            # Clear old messages for clean display
            await public_channel.purge(limit=10)
            
            # Get current leaderboard data
            leaderboard_data = await self.db.get_leaderboard_data("week", guild_id)
            
            if not leaderboard_data:
                # Send empty leaderboard message
                embed = discord.Embed(
                    title="🏆 Weekly Leaderboard",
                    description="**No deals submitted this week yet!**\n\nBe the first to get on the leaderboard by submitting a deal in your training zone!",
                    color=0xffd700
                )
                
                embed.add_field(
                    name="🎯 How to Get Started",
                    value="• Go to your **🔒 [Your Name]'s Training Zone**\n• Use the **📝 Submit Deal** button in your deal-submission channel\n• Watch your rank climb as you submit more deals!",
                    inline=False
                )
                
                embed.add_field(
                    name="🏅 Point System",
                    value="**🌐 Fiber:** 5 deals = 1 pt | Set/Close: 1 pt | Self-Gen: 2 pts\n**☀️ Solar:** Set/Close: 1 pt | Self-Gen: 2 pts\n**🌿 Landscaping:** Set/Close: 1 pt | Self-Gen: 2 pts + value bonuses",
                    inline=False
                )
                
                # Get week info
                current_week = await self.db.get_current_week_number(guild_id)
                embed.set_footer(text=f"Week {current_week} • Updates automatically with every deal submission")
                
                await public_channel.send(embed=embed)
                logger.info(f"Posted empty leaderboard for guild {guild_id}")
                return
            
            # Convert to LeaderboardEntry objects
            leaderboard = []
            for i, entry in enumerate(leaderboard_data[:15], 1):  # Top 15 for public display
                display_name = await self._get_current_discord_username(entry['user_id'], guild_id)
                
                leaderboard.append(LeaderboardEntry(
                    user_id=entry['user_id'],
                    username=display_name,
                    total_points=entry['total_points'],
                    standard_deals=entry['standard_deals'],
                    self_generated_deals=entry['self_generated_deals'],
                    total_deals=entry['total_deals'],
                    rank=i
                ))
            
            # Create enhanced public leaderboard embed
            embed = self._create_enhanced_public_leaderboard_embed(leaderboard, guild_id)
            
            # Post new leaderboard
            await public_channel.send(embed=embed)
            
            logger.info(f"Updated public leaderboard for guild {guild_id} with {len(leaderboard)} entries")
            
        except Exception as e:
            logger.error(f"Error updating public leaderboard: {e}")
    
    async def auto_refresh_public_leaderboard(self, guild_id: int):
        """Auto-refresh public leaderboard (called by infrastructure system)"""
        try:
            await self.update_public_leaderboard(guild_id)
            logger.info(f"Auto-refreshed public leaderboard for guild {guild_id}")
        except Exception as e:
            logger.error(f"Error auto-refreshing public leaderboard: {e}")
    
    def _create_leaderboard_embed(self, leaderboard: List[LeaderboardEntry], timeframe: str, guild_id: int) -> discord.Embed:
        """Create leaderboard embed"""
        title = f"🏆 {'Weekly' if timeframe == 'week' else 'Daily'} Leaderboard"
        
        embed = discord.Embed(
            title=title,
            description="Current standings in the sales competition",
            color=0xffd700
        )
        
        # Add top performers
        leaderboard_text = ""
        for entry in leaderboard[:10]:  # Top 10
            trophy = self._get_trophy_emoji(entry.rank)
            
            leaderboard_text += f"{trophy} **{entry.username}**\n"
            leaderboard_text += f"   └ **{entry.total_points}** points • {entry.total_deals} deals\n"
            
            if entry.self_generated_deals > 0:
                leaderboard_text += f"   └ Standard: {entry.standard_deals} • Self-Gen: {entry.self_generated_deals}\n"
            else:
                leaderboard_text += f"   └ {entry.standard_deals} standard deals\n"
            
            leaderboard_text += "\n"
        
        embed.description = leaderboard_text
        
        # Add summary stats
        total_deals = sum(entry.total_deals for entry in leaderboard)
        total_points = sum(entry.total_points for entry in leaderboard)
        
        embed.set_footer(text=f"{len(leaderboard)} participants • {total_deals} deals • {total_points} points")
        
        return embed
    
    def _create_public_leaderboard_embed(self, leaderboard: List[LeaderboardEntry], guild_id: int) -> discord.Embed:
        """Create public leaderboard embed for auto-posting"""
        embed = discord.Embed(
            title="🏆 Live Sales Leaderboard - This Week",
            description="Updated automatically after each deal submission",
            color=0xffd700
        )
        
        # Add top performers
        leaderboard_text = ""
        for entry in leaderboard:
            trophy = self._get_trophy_emoji(entry.rank)
            
            leaderboard_text += f"{trophy} **{entry.username}**\n"
            leaderboard_text += f"   └ **{entry.total_points}** points • {entry.total_deals} deals\n"
            
            if entry.self_generated_deals > 0:
                leaderboard_text += f"   └ Standard: {entry.standard_deals} • Self-Gen: {entry.self_generated_deals}\n"
            else:
                leaderboard_text += f"   └ {entry.standard_deals} standard deals\n"
            
            leaderboard_text += "\n"
        
        embed.description = leaderboard_text
        
        # Add footer with current week info
        embed.timestamp = discord.utils.utcnow()
        
        return embed
    
    def _create_enhanced_public_leaderboard_embed(self, leaderboard: List[LeaderboardEntry], guild_id: int) -> discord.Embed:
        """Create enhanced public leaderboard embed with better formatting"""
        embed = discord.Embed(
            title="🏆 Lord of The Doors - Weekly Leaderboard",
            description="**Live rankings updated with every deal submission**",
            color=0xffd700
        )
        
        # Always show user rankings first, regardless of count
        rankings_text = ""
        for entry in leaderboard[:10]:  # Show top 10
            if entry.rank == 1:
                trophy = "🥇"
            elif entry.rank == 2:
                trophy = "🥈"
            elif entry.rank == 3:
                trophy = "🥉"
            else:
                trophy = f"**{entry.rank}.**"
            
            rankings_text += f"{trophy} **{entry.username}** - {entry.total_points} pts ({entry.total_deals} deals)\n"
        
        embed.add_field(
            name="📊 Current Rankings",
            value=rankings_text,
            inline=False
        )
        
        # Show more if there are additional competitors
        if len(leaderboard) > 10:
            more_count = len(leaderboard) - 10
            embed.add_field(
                name="📈 More Competitors",
                value=f"... and {more_count} more competitors fighting for the top!",
                inline=False
            )
        
        # Competition stats
        total_deals = sum(entry.total_deals for entry in leaderboard)
        total_points = sum(entry.total_points for entry in leaderboard)
        
        embed.add_field(
            name="📈 This Week's Activity",
            value=f"• **{len(leaderboard)}** active competitors\n• **{total_deals}** total deals submitted\n• **{total_points}** total points earned",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Join the Competition",
            value="Submit deals in your training zone to climb the ranks and become the next **Lord of The Doors**!",
            inline=True
        )
        
        # Get week info and set footer
        embed.set_footer(text="Updates automatically • Lord of The Doors Season 3")
        embed.timestamp = discord.utils.utcnow()
        
        return embed
    
    def _process_user_stats(self, stats_data) -> Dict:
        """Process raw user statistics into categorized format"""
        totals = {
            'total_points': 0,
            'total_deals': 0,
            'setter_deals': 0,
            'closer_deals': 0,
            'self_gen_deals': 0,
            'niche_breakdown': {}
        }
        
        for niche, deal_type, deal_count, total_points in stats_data:
            totals['total_points'] += total_points
            totals['total_deals'] += deal_count
            
            # Categorize deal type
            category = self._categorize_deal_type(deal_type)
            totals[f'{category}_deals'] += deal_count
            
            # Niche breakdown
            if niche not in totals['niche_breakdown']:
                totals['niche_breakdown'][niche] = {
                    'points': 0, 'deals': 0, 'setter': 0, 'closer': 0, 'self_gen': 0
                }
            
            totals['niche_breakdown'][niche]['points'] += total_points
            totals['niche_breakdown'][niche]['deals'] += deal_count
            totals['niche_breakdown'][niche][category] += deal_count
        
        return totals
    
    def _categorize_deal_type(self, deal_type: str) -> str:
        """Categorize deal type for statistics"""
        deal_type = deal_type.lower()
        
        setter_types = ['set', 'single', 'multiple']
        closer_types = ['close']
        self_gen_types = ['self_generated', 'self']
        
        if deal_type in setter_types:
            return 'setter'
        elif deal_type in closer_types:
            return 'closer'
        elif deal_type in self_gen_types:
            return 'self_gen'
        else:
            return 'closer' if deal_type == 'standard' else 'self_gen'
    
    def _get_trophy_emoji(self, rank: int) -> str:
        """Get trophy emoji for rank"""
        if rank == 1:
            return "🥇"
        elif rank == 2:
            return "🥈"
        elif rank == 3:
            return "🥉"
        else:
            return f"**{rank}.**"
    
    def _get_niche_emoji(self, niche: str) -> str:
        """Get emoji for niche"""
        emojis = {
            'solar': '☀️',
            'fiber': '🌐',
            'landscaping': '🌿'
        }
        return emojis.get(niche.lower(), '💼')
    
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