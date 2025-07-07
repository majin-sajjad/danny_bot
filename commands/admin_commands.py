"""
Admin Commands for Danny Bot
"""

import discord
from discord.ext import commands
import logging
from typing import Optional
from core.database_manager import DatabaseManager
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class AdminCommands(commands.Cog):
    """Admin commands for server management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db_manager = DatabaseManager()
    
    def is_admin():
        """Check if user has admin permissions"""
        async def predicate(ctx):
            return ctx.author.guild_permissions.administrator
        return commands.check(predicate)
    
    # ============================================
    # DEAL MANAGEMENT COMMANDS
    # ============================================
    
    @commands.command(name='admin_deal_info')
    @is_admin()
    async def deal_info(self, ctx, deal_id: int):
        """Get detailed information about a specific deal"""
        try:
            # Get deal from Core DB
            deals = await self.db_manager.get_user_deals(user_id=None)  # Get all deals
            core_deal = None
            for deal in deals:
                if deal['id'] == deal_id:
                    core_deal = deal
                    break
            
            if not core_deal:
                await ctx.send(f"❌ Deal #{deal_id} not found.")
                return
            
            # Get deal from Leaderboard DB
            leaderboard_cog = self.bot.get_cog('LeaderboardManager')
            leaderboard_deal = None
            if leaderboard_cog:
                # Query leaderboard database for this deal
                async with leaderboard_cog.db.db_path and aiosqlite.connect(leaderboard_cog.db.db_path) as db:
                    cursor = await db.execute('SELECT * FROM deals WHERE deal_id = ?', (deal_id,))
                    lb_record = await cursor.fetchone()
                    if lb_record:
                        columns = [description[0] for description in cursor.description]
                        leaderboard_deal = dict(zip(columns, lb_record))
            
            # Get user info
            user = self.bot.get_user(core_deal['user_id'])
            username = user.display_name if user else f"User {core_deal['user_id']}"
            
            embed = discord.Embed(
                title=f"🔍 Deal #{deal_id} Details",
                color=0x3498db
            )
            
            embed.add_field(
                name="👤 User Information",
                value=f"**User:** {username}\n**ID:** {core_deal['user_id']}\n**Guild:** {core_deal.get('guild_id', 'Unknown')}",
                inline=False
            )
            
            embed.add_field(
                name="💼 Deal Details",
                value=f"**Type:** {core_deal['deal_type']}\n**Niche:** {core_deal['niche']}\n**Points:** {core_deal['points_awarded']}\n**Value:** ${core_deal.get('deal_value', 0):,.2f}",
                inline=True
            )
            
            embed.add_field(
                name="📅 Timestamps",
                value=f"**Submitted:** {core_deal['deal_date']}\n**Admin Submitted:** {'Yes' if core_deal.get('admin_submitted') else 'No'}",
                inline=True
            )
            
            embed.add_field(
                name="📝 Description",
                value=f"```{core_deal['customer_info'][:500]}{'...' if len(core_deal['customer_info']) > 500 else ''}```",
                inline=False
            )
            
            # Show dispute options
            embed.add_field(
                name="⚖️ Admin Actions",
                value=f"• `!admin_dispute {deal_id}` - Mark as disputed\n• `!admin_modify_points {deal_id} <points>` - Change points\n• `!admin_approve {deal_id}` - Approve deal\n• `!admin_reject {deal_id}` - Reject deal",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting deal info: {e}")
            await ctx.send(f"❌ Error retrieving deal information: {e}")
    
    @commands.command(name='admin_dispute')
    @is_admin()
    async def dispute_deal(self, ctx, deal_id: int, *, reason: str = None):
        """Mark a deal as disputed"""
        try:
            # Update both database systems
            await self._update_deal_in_both_systems(
                deal_id=deal_id,
                guild_id=ctx.guild.id,
                updates={'disputed': True},
                admin_reason=reason or "Disputed by admin"
            )
            
            embed = discord.Embed(
                title="⚖️ Deal Disputed",
                description=f"Deal #{deal_id} has been marked as disputed.",
                color=0xe74c3c
            )
            
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            
            embed.add_field(
                name="Next Steps",
                value=f"• `!admin_approve {deal_id}` - Approve and restore points\n• `!admin_reject {deal_id}` - Reject and remove points\n• `!admin_modify_points {deal_id} <points>` - Adjust points",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
            # Update leaderboards
            await self._refresh_all_leaderboards(ctx.guild.id)
            
        except Exception as e:
            logger.error(f"Error disputing deal: {e}")
            await ctx.send(f"❌ Error disputing deal: {e}")
    
    @commands.command(name='admin_approve')
    @is_admin()
    async def approve_deal(self, ctx, deal_id: int, *, reason: str = None):
        """Approve a disputed deal and restore points"""
        try:
            await self._update_deal_in_both_systems(
                deal_id=deal_id,
                guild_id=ctx.guild.id,
                updates={'disputed': False, 'verified': True},
                admin_reason=reason or "Approved by admin"
            )
            
            embed = discord.Embed(
                title="✅ Deal Approved",
                description=f"Deal #{deal_id} has been approved and points restored.",
                color=0x27ae60
            )
            
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
            
            # Update leaderboards
            await self._refresh_all_leaderboards(ctx.guild.id)
            
        except Exception as e:
            logger.error(f"Error approving deal: {e}")
            await ctx.send(f"❌ Error approving deal: {e}")
    
    @commands.command(name='admin_reject')
    @is_admin()
    async def reject_deal(self, ctx, deal_id: int, *, reason: str = None):
        """Reject a deal and remove points"""
        try:
            await self._update_deal_in_both_systems(
                deal_id=deal_id,
                guild_id=ctx.guild.id,
                updates={'disputed': True, 'verified': False, 'points': 0},
                admin_reason=reason or "Rejected by admin"
            )
            
            embed = discord.Embed(
                title="❌ Deal Rejected",
                description=f"Deal #{deal_id} has been rejected and points removed.",
                color=0xe74c3c
            )
            
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
            
            # Update leaderboards
            await self._refresh_all_leaderboards(ctx.guild.id)
            
        except Exception as e:
            logger.error(f"Error rejecting deal: {e}")
            await ctx.send(f"❌ Error rejecting deal: {e}")
    
    @commands.command(name='admin_modify_points')
    @is_admin()
    async def modify_deal_points(self, ctx, deal_id: int, new_points: float, *, reason: str = None):
        """Modify the points awarded for a deal"""
        try:
            await self._update_deal_in_both_systems(
                deal_id=deal_id,
                guild_id=ctx.guild.id,
                updates={'points': int(new_points)},
                admin_reason=reason or f"Points modified to {new_points} by admin"
            )
            
            embed = discord.Embed(
                title="📊 Points Modified",
                description=f"Deal #{deal_id} points updated to {new_points}.",
                color=0xf39c12
            )
            
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
            
            # Update leaderboards
            await self._refresh_all_leaderboards(ctx.guild.id)
            
        except Exception as e:
            logger.error(f"Error modifying deal points: {e}")
            await ctx.send(f"❌ Error modifying deal points: {e}")
    
    @commands.command(name='admin_list_deals')
    @is_admin()
    async def list_recent_deals(self, ctx, user: Optional[discord.Member] = None, limit: int = 10):
        """List recent deals for review"""
        try:
            if limit > 50:
                limit = 50
            
            # Get deals from database
            if user:
                deals = await self.db_manager.get_user_deals(user.id, limit=limit)
                title = f"📋 Recent Deals for {user.display_name}"
            else:
                # Get all deals - we need to modify get_user_deals or create new method
                deals = await self._get_guild_deals(ctx.guild.id, limit=limit)
                title = f"📋 Recent Deals in {ctx.guild.name}"
            
            if not deals:
                await ctx.send("No deals found.")
                return
            
            embed = discord.Embed(title=title, color=0x3498db)
            
            for deal in deals[:10]:  # Show max 10 in embed
                user_obj = self.bot.get_user(deal.get('user_id', 0))
                username = user_obj.display_name if user_obj else f"User {deal.get('user_id', 'Unknown')}"
                
                status = "✅" if deal.get('verified', True) else "❌"
                if deal.get('disputed', False):
                    status = "⚖️"
                
                embed.add_field(
                    name=f"{status} Deal #{deal['id']} - {username}",
                    value=f"**{deal['niche'].title()} {deal['deal_type']}** - {deal['points_awarded']} pts\n{deal.get('customer_info', 'No description')[:100]}{'...' if len(deal.get('customer_info', '')) > 100 else ''}",
                    inline=False
                )
            
            if len(deals) > 10:
                embed.set_footer(text=f"Showing 10 of {len(deals)} deals. Use !admin_deal_info <id> for details.")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error listing deals: {e}")
            await ctx.send(f"❌ Error listing deals: {e}")
    
    # ============================================
    # LEADERBOARD MANAGEMENT COMMANDS
    # ============================================
    
    @commands.command(name='admin_refresh_leaderboard')
    @is_admin()
    async def refresh_leaderboard(self, ctx):
        """Manually refresh all leaderboard systems"""
        try:
            await self._refresh_all_leaderboards(ctx.guild.id)
            
            embed = discord.Embed(
                title="🔄 Leaderboards Refreshed",
                description="All leaderboard systems have been updated.",
                color=0x27ae60
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error refreshing leaderboards: {e}")
            await ctx.send(f"❌ Error refreshing leaderboards: {e}")
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    async def _update_deal_in_both_systems(self, deal_id: int, guild_id: int, updates: dict, admin_reason: str = None):
        """Update a deal in both Core and Leaderboard database systems"""
        import aiosqlite
        
        # Update Core Database
        async with aiosqlite.connect(self.db_manager.db_path) as db:
            # Build update query
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key == 'points':
                    # Update points_awarded in core DB
                    set_clauses.append("points_awarded = ?")
                elif key == 'verified':
                    # Core DB doesn't have verified, skip
                    continue
                elif key == 'disputed':
                    # Core DB doesn't have disputed, skip  
                    continue
                else:
                    set_clauses.append(f"{key} = ?")
                values.append(value)
            
            if set_clauses:
                query = f"UPDATE deals SET {', '.join(set_clauses)} WHERE deal_id = ? AND guild_id = ?"
                values.extend([deal_id, guild_id])
                await db.execute(query, values)
                await db.commit()
        
        # Update Leaderboard Database
        leaderboard_cog = self.bot.get_cog('LeaderboardManager')
        if leaderboard_cog:
            async with aiosqlite.connect(leaderboard_cog.db.db_path) as db:
                # Build update query for leaderboard DB
                set_clauses = []
                values = []
                
                for key, value in updates.items():
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
                
                if set_clauses:
                    query = f"UPDATE deals SET {', '.join(set_clauses)} WHERE deal_id = ? AND guild_id = ?"
                    values.extend([deal_id, guild_id])
                    await db.execute(query, values)
                    await db.commit()
    
    async def _get_guild_deals(self, guild_id: int, limit: int = 50):
        """Get all deals for a specific guild"""
        import aiosqlite
        
        async with aiosqlite.connect(self.db_manager.db_path) as db:
            query = '''
                SELECT deal_id as id, user_id, niche, deal_type, deal_value, customer_info, 
                       deal_date, points_awarded, admin_submitted, admin_user_id, guild_id
                FROM deals 
                WHERE guild_id = ?
                ORDER BY deal_id DESC
                LIMIT ?
            '''
            
            cursor = await db.execute(query, (guild_id, limit))
            records = await cursor.fetchall()
            
            deals = []
            for record in records:
                deals.append({
                    'id': record[0],
                    'user_id': record[1],
                    'niche': record[2],
                    'deal_type': record[3],
                    'deal_value': record[4],
                    'customer_info': record[5],
                    'deal_date': record[6],
                    'points_awarded': record[7],
                    'admin_submitted': record[8],
                    'admin_user_id': record[9],
                    'guild_id': record[10]
                })
            
            return deals
    
    async def _refresh_all_leaderboards(self, guild_id: int):
        """Refresh all leaderboard systems after deal changes"""
        try:
            # Refresh public leaderboard
            leaderboard_cog = self.bot.get_cog('LeaderboardManager')
            if leaderboard_cog and hasattr(leaderboard_cog, 'display'):
                await leaderboard_cog.display.update_public_leaderboard(guild_id)
                logger.info(f"Refreshed public leaderboard for guild {guild_id}")
            
            # Refresh training zone deal submission stats
            training_cog = self.bot.get_cog('TrainingZoneManager')
            if training_cog:
                # Find all training zones and refresh deal submission channels
                guild = self.bot.get_guild(guild_id)
                if guild:
                    for category in guild.categories:
                        if "training zone" in category.name.lower():
                            for channel in category.channels:
                                if "deal-submission" in channel.name.lower():
                                    # Get the user for this training zone
                                    for member in guild.members:
                                        if member.display_name.lower() in category.name.lower():
                                            await training_cog.send_deal_submission_welcome(channel, member, {})
                                            break
            
        except Exception as e:
            logger.error(f"Error refreshing leaderboards: {e}")

# ============================================
# SERVER MANAGEMENT COMMANDS
# ============================================

    @commands.command(name='admin_refresh_server')
    @is_admin()
    async def refresh_server(self, ctx):
        """Refresh all server components"""
        try:
            embed = discord.Embed(
                title="🔄 Server Refresh Started",
                description="Refreshing all server components...",
                color=0xf39c12
            )
            message = await ctx.send(embed=embed)
            
            # Refresh training zones
            training_cog = self.bot.get_cog('TrainingZoneManager')
            if training_cog:
                await training_cog.auto_refresh_all_training_zones(ctx.guild)
            
            # Refresh infrastructure
            infrastructure_cog = self.bot.get_cog('ServerInfrastructure')
            if infrastructure_cog:
                await infrastructure_cog.setup_community_channels(ctx.guild)
                await infrastructure_cog.setup_welcome_channel(ctx.guild)
            
            # Refresh leaderboards
            await self._refresh_all_leaderboards(ctx.guild.id)
            
            embed.title = "✅ Server Refresh Complete"
            embed.description = "All server components have been refreshed successfully!"
            embed.color = 0x27ae60
            
            await message.edit(embed=embed)
            
        except Exception as e:
            logger.error(f"Error refreshing server: {e}")
            await ctx.send(f"❌ Error refreshing server: {e}")

async def setup(bot):
    await bot.add_cog(AdminCommands(bot)) 