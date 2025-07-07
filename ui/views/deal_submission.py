import discord
from discord.ext import commands
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from core.database_manager import DatabaseManager
from systems.leaderboard.calculator import PointsCalculator
import json
import aiosqlite

logger = logging.getLogger(__name__)

class SmartDealSubmissionView(discord.ui.View):
    """Enhanced deal submission view with dynamic stats and consistent UI/UX"""
    
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view
        self.db_manager = DatabaseManager()
        self.client = None  # Will be set when view is used
        
    async def _get_user_stats(self, user_id: int, guild_id: int = None) -> Dict[str, Any]:
        """Get user's deal statistics for current guild only (consistent with leaderboard)"""
        try:
            # Use leaderboard database for consistent stats (verified deals only)
            leaderboard_cog = None
            # Try to get client from view if available
            client = getattr(self, 'client', None)
            if client:
                for cog_name, cog in client.cogs.items():
                    if 'leaderboard' in cog_name.lower():
                        leaderboard_cog = cog
                        break
            
            if not leaderboard_cog or not hasattr(leaderboard_cog, 'db'):
                # Fallback to core database if leaderboard unavailable
                deals = await self.db_manager.get_user_deals(user_id, guild_id=guild_id)
            else:
                # Use leaderboard database for consistent filtering (verified deals only)
                async with aiosqlite.connect(leaderboard_cog.db.db_path) as db:
                    cursor = await db.execute('''
                        SELECT deal_id, niche, deal_type, points, description, timestamp
                        FROM deals 
                        WHERE user_id = ? AND guild_id = ? AND verified = 1 AND disputed = 0
                        ORDER BY timestamp DESC
                    ''', (user_id, guild_id))
                    
                    rows = await cursor.fetchall()
                    
                    # Convert to same format as core database
                    deals = []
                    for row in rows:
                        deals.append({
                            'points_awarded': row[3],  # points -> points_awarded
                            'deal_date': row[5],       # timestamp -> deal_date
                            'niche': row[1]
                        })
            
            # Calculate stats
            total_deals = len(deals)
            total_points = sum(deal.get('points_awarded', 0) for deal in deals)
            
            # This month deals
            now = datetime.now()
            current_month = now.month
            current_year = now.year
            
            this_month_deals = []
            for deal in deals:
                deal_date = deal.get('deal_date')
                if deal_date:
                    try:
                        # Handle different date formats
                        if isinstance(deal_date, str):
                            # Try to parse ISO format
                            deal_datetime = datetime.fromisoformat(deal_date.replace('Z', '+00:00'))
                        else:
                            deal_datetime = deal_date
                        
                        if deal_datetime.month == current_month and deal_datetime.year == current_year:
                            this_month_deals.append(deal)
                    except:
                        # If date parsing fails, skip this deal for monthly calculation
                        continue
            
            # Calculate success rate
            success_rate = min(100, int((total_points / max(total_deals, 1)) * 50)) if total_deals > 0 else 0
            
            return {
                'total_deals': total_deals,
                'this_month': len(this_month_deals),
                'total_points': total_points,
                'success_rate': success_rate
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {'total_deals': 0, 'this_month': 0, 'total_points': 0, 'success_rate': 0}
    
    async def _create_stats_embed(self, user: discord.User, guild_id: int = None, interaction: discord.Interaction = None) -> discord.Embed:
        """Create dynamic stats embed with real-time data"""
        # Set client reference if provided
        if interaction:
            self.client = interaction.client
            
        stats = await self._get_user_stats(user.id, guild_id)
        
        embed = discord.Embed(
            title="💼 Deal Submission Central",
            description="Submit your deals and get instant AI feedback to improve your closing rate!",
            color=0x00ff88
        )
        
        embed.add_field(
            name="📊 Your Stats (Verified Deals)",
            value=f"**Total Deals:** {stats['total_deals']}\n**This Month:** {stats['this_month']}\n**Total Points:** {stats['total_points']}\n**Success Rate:** {stats['success_rate']}%",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Available Niches",
            value="• **🌐 Fiber** - Internet/telecom deals (appointment/closed/both)\n• **☀️ Solar** - Solar installation deals (appointment/closed/both)\n• **🌿 Landscaping** - Landscaping service deals (appointment/closed/both)",
            inline=False
        )
        
        embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
        embed.set_footer(text="Select your niche below to choose appointment/closed/both options!")
        
        return embed
    
    async def _update_leaderboard_after_deal(self, interaction: discord.Interaction):
        """Update the public leaderboard after a deal is submitted"""
        try:
            # Get the leaderboard manager from the bot
            leaderboard_cog = None
            for cog_name, cog in interaction.client.cogs.items():
                if 'leaderboard' in cog_name.lower():
                    leaderboard_cog = cog
                    break
            
            if leaderboard_cog and hasattr(leaderboard_cog, 'display'):
                await leaderboard_cog.display.update_public_leaderboard(interaction.guild.id)
                logger.info(f"Updated public leaderboard after deal submission for guild {interaction.guild.id}")
        except Exception as e:
            logger.error(f"Error updating leaderboard after deal: {e}")
    

    
    @discord.ui.button(label="🌐 Fiber Deal", style=discord.ButtonStyle.secondary, emoji="🌐", custom_id="smart_submit_fiber")
    async def fiber_deal(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show fiber deal options"""
        try:
            view = FiberDealTypeView()
            
            embed = discord.Embed(
                title="🌐 Fiber Deal Submission",
                description="Choose the type of fiber deal you want to submit:",
                color=0x3498db
            )
            
            embed.add_field(
                name="📅 Appointment Set",
                value="You scheduled an appointment with a potential fiber customer (1 pt)",
                inline=False
            )
            
            embed.add_field(
                name="💰 Deal Closed",
                value="You closed a fiber deal successfully (1 pt)",
                inline=False
            )
            
            embed.add_field(
                name="🚀 Both (Self-Generated)",
                value="You set the appointment AND closed the deal yourself (2 pts)",
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            logger.error(f"Error showing fiber deal options: {e}")
            embed = discord.Embed(title="❌ Error", description="Error loading fiber options. Please try again.", color=0xe74c3c)
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="☀️ Solar Deal", style=discord.ButtonStyle.secondary, emoji="☀️", custom_id="smart_submit_solar")
    async def solar_deal(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show solar deal options"""
        try:
            view = SolarDealTypeView()
            
            embed = discord.Embed(
                title="☀️ Solar Deal Submission",
                description="Choose the type of solar deal you want to submit:",
                color=0xf39c12
            )
            
            embed.add_field(
                name="📅 Appointment Set",
                value="You scheduled an appointment with a potential solar customer (1 pt)",
                inline=False
            )
            
            embed.add_field(
                name="💰 Deal Closed",
                value="You closed a solar deal successfully (1 pt)",
                inline=False
            )

            embed.add_field(
                name="🚀 Both (Self-Generated)",
                value="You set the appointment AND closed the deal yourself (2 pts)",
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            logger.error(f"Error showing solar deal options: {e}")
            embed = discord.Embed(title="❌ Error", description="Error loading solar options. Please try again.", color=0xe74c3c)
            await interaction.response.edit_message(embed=embed, view=self) 
    
    @discord.ui.button(label="🌿 Landscaping Deal", style=discord.ButtonStyle.secondary, emoji="🌿", custom_id="smart_submit_landscaping")
    async def landscaping_deal(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show landscaping deal options"""
        try:
            view = LandscapingDealTypeView()
            
            embed = discord.Embed(
                title="🌿 Landscaping Deal Submission",
                description="Choose the type of landscaping deal you want to submit:",
                color=0x27ae60
            )
            
            embed.add_field(
                name="📅 Appointment Set",
                value="You scheduled an appointment with a potential landscaping customer (1 pt)",
                inline=False
            )
            
            embed.add_field(
                name="💰 Deal Closed",
                value="You closed a landscaping deal successfully (1 pt + value tiers)",
                inline=False
            )
            
            embed.add_field(
                name="🚀 Both (Self-Generated)",
                value="You set the appointment AND closed the deal yourself (2+ pts)",
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            logger.error(f"Error showing landscaping deal options: {e}")
            embed = discord.Embed(title="❌ Error", description="Error loading landscaping options. Please try again.", color=0xe74c3c)
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="📊 View My Deals", style=discord.ButtonStyle.secondary, emoji="📊", custom_id="view_my_deals")
    async def view_my_deals(self, interaction: discord.Interaction, button: discord.ui.Button):
        """View user's submitted deals (consistent with leaderboard)"""
        try:
            # Set client reference for accessing cogs
            self.client = interaction.client
            
            # Get the leaderboard database to ensure consistency with leaderboard counts
            leaderboard_cog = None
            for cog_name, cog in interaction.client.cogs.items():
                if 'leaderboard' in cog_name.lower():
                    leaderboard_cog = cog
                    break
            
            if not leaderboard_cog or not hasattr(leaderboard_cog, 'db'):
                # Fallback to core database if leaderboard unavailable
                deals = await self.db_manager.get_user_deals(interaction.user.id, limit=10, guild_id=interaction.guild.id)
                deals_source = "Core Database"
            else:
                # Use leaderboard database for consistent filtering (verified deals only)
                async with aiosqlite.connect(leaderboard_cog.db.db_path) as db:
                    cursor = await db.execute('''
                        SELECT deal_id, niche, deal_type, points, description, timestamp
                        FROM deals 
                        WHERE user_id = ? AND guild_id = ? AND verified = 1 AND disputed = 0
                        ORDER BY timestamp DESC
                        LIMIT 10
                    ''', (interaction.user.id, interaction.guild.id))
                    
                    rows = await cursor.fetchall()
                    
                    # Convert to same format as core database
                    deals = []
                    for row in rows:
                        deals.append({
                            'id': row[0],           # deal_id -> id
                            'niche': row[1], 
                            'deal_type': row[2],
                            'points_awarded': row[3],  # points -> points_awarded
                            'customer_info': row[4],   # description -> customer_info
                            'deal_date': row[5]        # timestamp -> deal_date
                        })
                    deals_source = "Leaderboard Database (verified deals only)"
            
            embed = discord.Embed(
                title="📊 Your Recent Deals",
                description=f"Here are your {len(deals)} most recent **verified** deals (matching leaderboard):",
                color=0x9b59b6
            )
            
            if not deals:
                embed.add_field(
                    name="📭 No Verified Deals Yet",
                    value="You haven't submitted any verified deals yet!\n\n• Submit deals and they'll appear here after verification\n• Only verified deals count toward leaderboard\n• Upload photos to help verify your deals",
                    inline=False
                )
            else:
                for i, deal in enumerate(deals[:5], 1):
                    # FIX: Handle None values in all deal fields
                    if not deal:
                        continue
                    
                    # Safe get for deal_date
                    deal_date = deal.get('deal_date')
                    if deal_date and deal_date != 'None':
                        try:
                            parsed_date = datetime.fromisoformat(deal_date)
                            date_str = parsed_date.strftime('%m/%d/%Y')
                        except:
                            date_str = "Unknown date"
                    else:
                        date_str = "Unknown date"
                    
                    # Safe get for all other fields
                    deal_id = deal.get('id', 'Unknown')
                    niche = deal.get('niche', 'Unknown')
                    deal_type = deal.get('deal_type', 'Unknown')
                    points_awarded = deal.get('points_awarded', 0)
                    customer_info = deal.get('customer_info', 'No description')
                    
                    # Safe string operations
                    niche_title = niche.title() if niche else 'Unknown'
                    deal_type_title = deal_type.replace('_', ' ').title() if deal_type else 'Unknown'
                    info_preview = customer_info[:50] if customer_info else 'No description'
                    info_suffix = '...' if customer_info and len(customer_info) > 50 else ''
                    
                    embed.add_field(
                        name=f"✅ Deal #{deal_id} - {niche_title}",
                        value=f"**Type:** {deal_type_title}\n**Points:** {points_awarded}\n**Date:** {date_str}\n**Info:** {info_preview}{info_suffix}",
                        inline=False
                    )
                
                if len(deals) > 5:
                    embed.add_field(
                        name="📈 More Deals",
                        value=f"You have {len(deals) - 5} more verified deals in your history!",
                        inline=False
                    )
                
                embed.add_field(
                    name="ℹ️ Note",
                    value="Only **verified** deals are shown here (same as leaderboard count). Upload photos to help verify your deals!",
                    inline=False
                )
            
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            logger.error(f"Error viewing user deals: {e}")
            embed = discord.Embed(title="❌ Error", description="Error loading your deals. Please try again.", color=0xe74c3c)
            await interaction.response.edit_message(embed=embed, view=self)

# Base modal class for consistent thread creation
class BaseDealModal(discord.ui.Modal):
    """Base modal for deal submissions"""
    
    def __init__(self, title: str, deal_type: str, niche: str, points: float):
        super().__init__(title=title)
        self.deal_type = deal_type
        self.niche = niche
        self.points = points
        self.db_manager = DatabaseManager()
    
    async def update_public_leaderboard_after_deal(self, interaction: discord.Interaction):
        """Update the public leaderboard after a deal is submitted"""
        try:
            # Get the leaderboard manager from the bot
            leaderboard_cog = None
            for cog_name, cog in interaction.client.cogs.items():
                if 'leaderboard' in cog_name.lower():
                    leaderboard_cog = cog
                    break
            
            if leaderboard_cog and hasattr(leaderboard_cog, 'display'):
                await leaderboard_cog.display.update_public_leaderboard(interaction.guild.id)
                logger.info(f"Updated public leaderboard after deal submission for guild {interaction.guild.id}")
        except Exception as e:
            logger.error(f"Error updating leaderboard after deal: {e}")
    
    async def save_deal_to_both_systems(self, interaction: discord.Interaction, deal_description: str, deal_value: float = None, final_points: float = None):
        """Save deal to both Core DatabaseManager and LeaderboardDatabase systems"""
        try:
            # Use final_points if provided, otherwise use self.points
            points_to_award = final_points if final_points is not None else self.points
            
            # 1. Save to Core DatabaseManager (existing system)
            core_deal_id = await self.db_manager.save_deal(
                user_id=interaction.user.id,
                niche=self.niche,
                deal_type=self.deal_type,
                deal_value=deal_value,
                customer_info=deal_description,
                points_awarded=points_to_award,
                screenshot_url=None,
                additional_data=json.dumps({"deal_subtype": self.deal_type, "deal_value": deal_value}),
                admin_submitted=False,
                admin_user_id=None,
                guild_id=interaction.guild.id
            )
            
            # 2. Save to LeaderboardDatabase system (for leaderboard tracking)
            leaderboard_cog = None
            for cog_name, cog in interaction.client.cogs.items():
                if 'leaderboard' in cog_name.lower():
                    leaderboard_cog = cog
                    break
            
            if leaderboard_cog and hasattr(leaderboard_cog, 'db'):
                # Get current week number
                current_week = await leaderboard_cog.db.get_current_week_number(interaction.guild.id)
                
                # Map deal types to leaderboard format
                leaderboard_deal_type = self.deal_type
                if self.deal_type == "appointment_set":
                    leaderboard_deal_type = "set"
                elif self.deal_type == "deal_closed":
                    leaderboard_deal_type = "close"
                
                # Save to leaderboard database
                leaderboard_deal_id = await leaderboard_cog.db.insert_deal(
                    guild_id=interaction.guild.id,
                    user_id=interaction.user.id,
                    username=interaction.user.display_name,
                    deal_type=leaderboard_deal_type,
                    niche=self.niche,
                    points=int(points_to_award),
                    description=deal_description,
                    week_number=current_week,
                    admin_submitted=False,
                    admin_user_id=None
                )
                
                logger.info(f"Deal saved to both systems - Core ID: {core_deal_id}, Leaderboard ID: {leaderboard_deal_id}")
            
            return core_deal_id
            
        except Exception as e:
            logger.error(f"Error saving deal to both systems: {e}")
            raise
    
    async def create_deal_thread(self, interaction: discord.Interaction, deal_id: int, deal_info: str):
        """Create a thread for the submitted deal with photo submission request"""
        try:
            # Find the deal submission channel
            deal_channel = None
            for channel in interaction.guild.channels:
                if 'deal' in channel.name.lower() and 'submission' in channel.name.lower():
                    deal_channel = channel
                    break
            
            if not deal_channel:
                logger.warning("Deal submission channel not found")
                return None
            
            # Create thread
            thread_name = f"Deal #{deal_id} - {interaction.user.display_name}"
            thread = await deal_channel.create_thread(
                name=thread_name,
                type=discord.ChannelType.public_thread,
                auto_archive_duration=10080  # 7 days
            )
            
            # Send initial message in thread with deal description
            embed = discord.Embed(
                title="📸 Deal Photo Submission Required",
                description=f"Congratulations on submitting your {self.niche} deal! **Please upload a photo of your completed deal to verify it.**",
                color=0x00ff88
            )
            
            embed.add_field(
                name="📋 Deal Details",
                value=f"**Deal ID:** #{deal_id}\n**Type:** {self.deal_type.replace('_', ' ').title()}\n**Niche:** {self.niche.title()}\n**Points:** {self.points}",
                inline=False
            )
            
            # Add the deal description to the thread
            embed.add_field(
                name="📝 Deal Description",
                value=f"```{deal_info}```",
                inline=False
            )
            
            embed.add_field(
                name="📸 Photo Requirements",
                value="• Screenshot of closed deal/appointment confirmation\n• Contract signature (if applicable)\n• System confirmation screen\n• Any relevant documentation",
                inline=False
            )
            
            embed.add_field(
                name="🎯 Why Photos Matter",
                value="Photos help verify your deals and provide valuable feedback for improvement!",
                inline=False
            )
            
            embed.set_footer(text="Upload your photo in this thread to complete the submission!")
            
            await thread.send(f"🎉 {interaction.user.mention} - **SUBMIT A PHOTO OF YOUR DEAL HERE!**", embed=embed)
            
            return thread.mention
            
        except Exception as e:
            logger.error(f"Error creating deal thread: {e}")
            return None

class StandardDealModal(BaseDealModal):
    """Modal for submitting standard deals"""
    
    def __init__(self):
        super().__init__(title="📝 Submit Standard Deal", deal_type="standard", niche="general", points=1)
        
        self.description = discord.ui.TextInput(
            label="Deal Description",
            placeholder="Describe your closed deal briefly (customer info, value, etc.)",
            style=discord.TextStyle.paragraph,
            min_length=10,
            max_length=500,
            required=True
        )
        self.add_item(self.description)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Process standard deal submission"""
        try:
            # Save deal to both database systems
            deal_id = await self.save_deal_to_both_systems(
                interaction=interaction,
                deal_description=self.description.value,
                deal_value=None,
                final_points=self.points
            )
            
            # Create thread for deal
            thread_mention = await self.create_deal_thread(interaction, deal_id, self.description.value)
            
            # Update public leaderboard
            await self.update_public_leaderboard_after_deal(interaction)
            
            # Return to main view with updated stats
            view = SmartDealSubmissionView()
            embed = await view._create_stats_embed(interaction.user, interaction.guild.id, interaction)
            
            embed.add_field(
                name="✅ Deal Submitted Successfully!",
                value=f"**Deal ID:** #{deal_id}\n**Points Earned:** {self.points}\n**Thread Created:** {thread_mention or 'Check #deal-submission for your photo upload thread!'}\n\n**📸 Next Step:** Upload a photo of your deal in the thread!",
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error submitting standard deal: {e}")
            embed = discord.Embed(title="❌ Error", description="Error submitting deal. Please try again.", color=0xe74c3c)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
class SelfGeneratedDealModal(BaseDealModal):
    """Modal for submitting self-generated deals"""
    
    def __init__(self):
        super().__init__(title="🚀 Submit Self-Generated Deal", deal_type="self_generated", niche="general", points=2)
        
        self.description = discord.ui.TextInput(
            label="Deal Description",
            placeholder="Describe your self-generated deal (how you found and closed the customer)",
            style=discord.TextStyle.paragraph,
            min_length=10,
            max_length=500,
            required=True
        )
        self.add_item(self.description)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Process self-generated deal submission"""
        try:
            # Save deal to both database systems
            deal_id = await self.save_deal_to_both_systems(
                interaction=interaction,
                deal_description=self.description.value,
                deal_value=None,
                final_points=self.points
            )
            
            # Create thread for deal
            thread_mention = await self.create_deal_thread(interaction, deal_id, self.description.value)
            
            # Update public leaderboard
            await self.update_public_leaderboard_after_deal(interaction)
            
            # Return to main view with updated stats
            view = SmartDealSubmissionView()
            embed = await view._create_stats_embed(interaction.user, interaction.guild.id, interaction)
            
            embed.add_field(
                name="✅ Self-Generated Deal Submitted!",
                value=f"**Deal ID:** #{deal_id}\n**Points Earned:** {self.points}\n**Thread Created:** {thread_mention or 'Check #deal-submission for your photo upload thread!'}\n\n**📸 Next Step:** Upload a photo of your deal in the thread!",
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error submitting self-generated deal: {e}")
            embed = discord.Embed(title="❌ Error", description="Error submitting deal. Please try again.", color=0xe74c3c)
            await interaction.response.send_message(embed=embed, ephemeral=True) 

# Niche-specific deal type views
class FiberDealTypeView(discord.ui.View):
    """View for selecting fiber deal type"""
    
    def __init__(self):
        super().__init__(timeout=300)
        self.db_manager = DatabaseManager()
        self.points_calculator = PointsCalculator()
    
    @discord.ui.button(label="📅 Appointment Set", style=discord.ButtonStyle.primary, emoji="📅")
    async def appointment_set(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Submit fiber appointment set"""
        points = self.points_calculator.calculate_points("set", "fiber")
        modal = FiberDealModal("appointment_set", points)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="💰 Deal Closed", style=discord.ButtonStyle.success, emoji="💰")
    async def deal_closed(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Submit fiber deal closed"""
        points = self.points_calculator.calculate_points("close", "fiber")
        modal = FiberDealModal("deal_closed", points)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🚀 Both (Self-Generated)", style=discord.ButtonStyle.secondary, emoji="🚀")
    async def both_self_generated(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Submit self-generated fiber deal (both appointment and close)"""
        points = self.points_calculator.calculate_points("self_generated", "fiber")
        modal = FiberDealModal("self_generated", points)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🔙 Back", style=discord.ButtonStyle.danger, emoji="🔙")
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go back to main deal submission view"""
        view = SmartDealSubmissionView()
        embed = await view._create_stats_embed(interaction.user, interaction.guild.id, interaction)
        await interaction.response.edit_message(embed=embed, view=view)

class SolarDealTypeView(discord.ui.View):
    """View for selecting solar deal type"""
    
    def __init__(self):
        super().__init__(timeout=300)
        self.db_manager = DatabaseManager()
        self.points_calculator = PointsCalculator()
    
    @discord.ui.button(label="📅 Appointment Set", style=discord.ButtonStyle.primary, emoji="📅")
    async def appointment_set(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Submit solar appointment set"""
        points = self.points_calculator.calculate_points("set", "solar")
        modal = SolarDealModal("appointment_set", points)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="💰 Deal Closed", style=discord.ButtonStyle.success, emoji="💰")
    async def deal_closed(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Submit solar deal closed"""
        points = self.points_calculator.calculate_points("close", "solar")
        modal = SolarDealModal("deal_closed", points)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🚀 Both (Self-Generated)", style=discord.ButtonStyle.secondary, emoji="🚀")
    async def both_self_generated(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Submit self-generated solar deal (both appointment and close)"""
        points = self.points_calculator.calculate_points("self_generated", "solar")
        modal = SolarDealModal("self_generated", points)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🔙 Back", style=discord.ButtonStyle.danger, emoji="🔙")
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go back to main deal submission view"""
        view = SmartDealSubmissionView()
        embed = await view._create_stats_embed(interaction.user, interaction.guild.id, interaction)
        await interaction.response.edit_message(embed=embed, view=view)

class LandscapingDealTypeView(discord.ui.View):
    """View for selecting landscaping deal type"""
    
    def __init__(self):
        super().__init__(timeout=300)
        self.db_manager = DatabaseManager()
        self.points_calculator = PointsCalculator()
        
    @discord.ui.button(label="📅 Appointment Set", style=discord.ButtonStyle.primary, emoji="📅")
    async def appointment_set(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Submit landscaping appointment set"""
        points = self.points_calculator.calculate_points("set", "landscaping")
        modal = LandscapingDealModal("appointment_set", points)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="💰 Deal Closed", style=discord.ButtonStyle.success, emoji="💰")
    async def deal_closed(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Submit landscaping deal closed"""
        points = self.points_calculator.calculate_points("close", "landscaping")
        modal = LandscapingDealModal("deal_closed", points)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🚀 Both (Self-Generated)", style=discord.ButtonStyle.secondary, emoji="🚀")
    async def both_self_generated(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Submit self-generated landscaping deal (both appointment and close)"""
        points = self.points_calculator.calculate_points("self_generated", "landscaping")
        modal = LandscapingDealModal("self_generated", points)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🔙 Back", style=discord.ButtonStyle.danger, emoji="🔙")
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go back to main deal submission view"""
        view = SmartDealSubmissionView()
        embed = await view._create_stats_embed(interaction.user, interaction.guild.id, interaction)
        await interaction.response.edit_message(embed=embed, view=view)

# Niche-specific deal modals
class FiberDealModal(BaseDealModal):
    """Modal for submitting fiber deals"""
    
    def __init__(self, deal_type: str, points: float):
        super().__init__(title=f"🌐 Submit Fiber Deal - {deal_type.replace('_', ' ').title()}", 
                         deal_type=deal_type, niche="fiber", points=points)
        
        self.description = discord.ui.TextInput(
            label="Deal Description",
            placeholder="Describe your fiber deal (customer details, package sold, etc.)",
            style=discord.TextStyle.paragraph,
            min_length=10,
            max_length=500,
            required=True
        )
        self.add_item(self.description)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Process fiber deal submission"""
        try:
            # Save deal to both database systems
            deal_id = await self.save_deal_to_both_systems(
                interaction=interaction,
                deal_description=self.description.value,
                deal_value=None,
                final_points=self.points
            )
            
            # Create thread for deal
            thread_mention = await self.create_deal_thread(interaction, deal_id, self.description.value)
            
            # Return to main view with updated stats
            view = SmartDealSubmissionView()
            embed = await view._create_stats_embed(interaction.user, interaction.guild.id)
            
            embed.add_field(
                name="✅ Fiber Deal Submitted!",
                value=f"**Deal ID:** #{deal_id}\n**Type:** {self.deal_type.replace('_', ' ').title()}\n**Points Earned:** {self.points}\n**Thread Created:** {thread_mention or 'Check #deal-submission for your photo upload thread!'}\n\n**📸 Next Step:** Upload a photo of your deal in the thread!",
                inline=False
            )
            
            # Update public leaderboard
            await self.update_public_leaderboard_after_deal(interaction)
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error submitting fiber deal: {e}")
            embed = discord.Embed(title="❌ Error", description="Error submitting deal. Please try again.", color=0xe74c3c)
            await interaction.response.send_message(embed=embed, ephemeral=True)

class SolarDealModal(BaseDealModal):
    """Modal for submitting solar deals"""
    
    def __init__(self, deal_type: str, points: float):
        super().__init__(title=f"☀️ Submit Solar Deal - {deal_type.replace('_', ' ').title()}", 
                         deal_type=deal_type, niche="solar", points=points)
        
        self.description = discord.ui.TextInput(
            label="Deal Description",
            placeholder="Describe your solar deal (customer details, system size, value, etc.)",
            style=discord.TextStyle.paragraph,
            min_length=10,
            max_length=500,
            required=True
        )
        self.add_item(self.description)
        
        # Add deal value field for closed deals
        if "closed" in deal_type or "generated" in deal_type:
            self.deal_value = discord.ui.TextInput(
                label="Deal Value (Optional)",
                placeholder="Enter deal value in dollars (e.g., 25000)",
                min_length=1,
                max_length=10,
                required=False
            )
            self.add_item(self.deal_value)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Process solar deal submission"""
        try:
            # Parse deal value if provided
            deal_value = None
            if hasattr(self, 'deal_value') and self.deal_value.value:
                try:
                    deal_value = float(self.deal_value.value.replace('$', '').replace(',', ''))
                except ValueError:
                    pass
            
            # Save deal to both database systems
            deal_id = await self.save_deal_to_both_systems(
                interaction=interaction,
                deal_description=self.description.value,
                deal_value=deal_value,
                final_points=self.points
            )
            
            # Create thread for deal
            thread_mention = await self.create_deal_thread(interaction, deal_id, self.description.value)
            
            # Return to main view with updated stats
            view = SmartDealSubmissionView()
            embed = await view._create_stats_embed(interaction.user, interaction.guild.id, interaction)
            
            value_text = f"**Value:** ${deal_value:,.0f}" if deal_value else "**Value:** Not specified"
            
            embed.add_field(
                name="✅ Solar Deal Submitted!",
                value=f"**Deal ID:** #{deal_id}\n**Type:** {self.deal_type.replace('_', ' ').title()}\n**Points Earned:** {self.points}\n{value_text}\n**Thread Created:** {thread_mention or 'Check #deal-submission for your photo upload thread!'}\n\n**📸 Next Step:** Upload a photo of your deal in the thread!",
                inline=False
            )
            
            # Update public leaderboard
            await self.update_public_leaderboard_after_deal(interaction)
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error submitting solar deal: {e}")
            embed = discord.Embed(title="❌ Error", description="Error submitting deal. Please try again.", color=0xe74c3c)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
class LandscapingDealModal(BaseDealModal):
    """Modal for submitting landscaping deals"""
    
    def __init__(self, deal_type: str, base_points: float):
        super().__init__(title=f"🌿 Submit Landscaping Deal - {deal_type.replace('_', ' ').title()}", 
                         deal_type=deal_type, niche="landscaping", points=base_points)
        
        self.description = discord.ui.TextInput(
            label="Deal Description",
            placeholder="Describe your landscaping deal (service type, customer details, etc.)",
            style=discord.TextStyle.paragraph,
            min_length=10,
            max_length=500,
            required=True
        )
        self.add_item(self.description)
        
        # Add deal value field for closed deals (affects point calculation)
        if "closed" in deal_type or "generated" in deal_type:
            self.deal_value = discord.ui.TextInput(
                label="Deal Value",
                placeholder="Enter deal value in dollars (e.g., 5000) - affects bonus points!",
                min_length=1,
                max_length=10,
                required=True
            )
            self.add_item(self.deal_value)
    
    def calculate_landscaping_points(self, deal_value: float, base_points: float) -> float:
        """Calculate points based on landscaping deal value tiers"""
        if deal_value >= 10000:
            return base_points + 2  # Tier 3: $10k+ = +2 bonus points
        elif deal_value >= 5000:
            return base_points + 1  # Tier 2: $5k-$10k = +1 bonus point
        else:
            return base_points  # Tier 1: Under $5k = base points only
    
    async def on_submit(self, interaction: discord.Interaction):
        """Process landscaping deal submission"""
        try:
            # Parse deal value and calculate points
            deal_value = None
            final_points = self.points
            
            if hasattr(self, 'deal_value') and self.deal_value.value:
                try:
                    deal_value = float(self.deal_value.value.replace('$', '').replace(',', ''))
                    final_points = self.calculate_landscaping_points(deal_value, self.points)
                except ValueError:
                    await interaction.response.send_message("❌ Please enter a valid deal value in dollars.", ephemeral=True)
                    return
            
            # Save deal to both database systems
            deal_id = await self.save_deal_to_both_systems(
                interaction=interaction,
                deal_description=self.description.value,
                deal_value=deal_value,
                final_points=final_points
            )
            
            # Create thread for deal
            thread_mention = await self.create_deal_thread(interaction, deal_id, self.description.value)
            
            # Return to main view with updated stats
            view = SmartDealSubmissionView()
            embed = await view._create_stats_embed(interaction.user, interaction.guild.id, interaction)
            
            value_text = f"**Value:** ${deal_value:,.0f}" if deal_value else "**Value:** Not specified"
            value_tier = self._get_value_tier(deal_value) if deal_value else "Standard"
            
            embed.add_field(
                name="✅ Landscaping Deal Submitted!",
                value=f"**Deal ID:** #{deal_id}\n**Type:** {self.deal_type.replace('_', ' ').title()}\n**Points Earned:** {final_points}\n{value_text}\n**Value Tier:** {value_tier}\n**Thread Created:** {thread_mention or 'Check #deal-submission for your photo upload thread!'}\n\n**📸 Next Step:** Upload a photo of your deal in the thread!",
                inline=False
            )
            
            # Update public leaderboard
            await self.update_public_leaderboard_after_deal(interaction)
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error submitting landscaping deal: {e}")
            embed = discord.Embed(title="❌ Error", description="Error submitting deal. Please try again.", color=0xe74c3c)
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    def _get_value_tier(self, deal_value: float) -> str:
        """Get value tier name for deal"""
        if deal_value >= 10000:
            return "Tier 3"
        elif deal_value >= 5000:
            return "Tier 2"
        else:
            return "Tier 1"

# Admin deal submission function for integration with admin commands
async def submit_admin_deal(bot, target_user: discord.User, niche: str, deal_type: str, 
                           deal_info: str, deal_value: float = None, admin_user: discord.User = None):
    """Function to be called by admin commands for deal submission"""
    try:
        db_manager = DatabaseManager()
        
        # Calculate points based on niche and type
        if niche == "fiber":
            points = 0.5 if deal_type in ["appointment_set", "deal_closed"] else 1.0
        elif niche == "solar":
            points = 1.0 if deal_type in ["appointment_set", "deal_closed"] else 2.0
        elif niche == "landscaping":
            base_points = 1.0 if deal_type in ["appointment_set", "deal_closed"] else 2.0
            if deal_value and deal_type in ["deal_closed", "self_generated"]:
                if deal_value >= 10000:
                    points = base_points + 2
                elif deal_value >= 5000:
                    points = base_points + 1
                else:
                    points = base_points
            else:
                points = base_points
        else:  # general/standard
            points = 1.0 if deal_type == "standard" else 2.0
        
        # Save deal to database
        deal_id = await db_manager.save_deal(
            user_id=target_user.id,
            niche=niche,
            deal_type=deal_type,
            deal_value=deal_value,
            customer_info=deal_info,
            points_awarded=points,
            screenshot_url=None,
            additional_data=json.dumps({"admin_submitted": True}),
            admin_submitted=True,
            admin_user_id=admin_user.id if admin_user else None,
            guild_id=0  # Admin deals don't have guild context in this function
        )
        
        # Find deal submission channel and create thread
        for guild in bot.guilds:
            for channel in guild.channels:
                if 'deal' in channel.name.lower() and 'submission' in channel.name.lower():
                    try:
                        # Create thread
                        thread_name = f"Deal #{deal_id} - {target_user.display_name} (Admin)"
                        thread = await channel.create_thread(
                            name=thread_name,
                            type=discord.ChannelType.public_thread,
                            auto_archive_duration=10080  # 7 days
                        )
                        
                        # Send initial message in thread
                        embed = discord.Embed(
                            title="📸 Admin-Submitted Deal - Photo Required",
                            description=f"An admin has submitted a deal for {target_user.mention}. **Please upload a photo to verify this deal.**",
                            color=0xf39c12
                        )
                        
                        embed.add_field(
                            name="📋 Deal Details",
                            value=f"**Deal ID:** #{deal_id}\n**Type:** {deal_type.replace('_', ' ').title()}\n**Niche:** {niche.title()}\n**Points:** {points}\n**Admin:** {admin_user.mention if admin_user else 'System'}",
                            inline=False
                        )
                        
                        embed.add_field(
                            name="📸 Photo Requirements",
                            value="• Screenshot of closed deal/appointment confirmation\n• Contract signature (if applicable)\n• System confirmation screen\n• Any relevant documentation",
                            inline=False
                        )
                        
                        await thread.send(f"🎉 {target_user.mention} - **ADMIN DEAL SUBMITTED - PHOTO REQUIRED!**", embed=embed)
                        break
                    except Exception as e:
                        logger.error(f"Error creating admin deal thread: {e}")
        
        return deal_id, points
        
    except Exception as e:
        logger.error(f"Error in admin deal submission: {e}")
        return None, 0

# Backward compatibility aliases for old view names
DealSubmissionView = SmartDealSubmissionView
FiberDealView = FiberDealTypeView
SolarDealView = SolarDealTypeView
LandscapingDealView = LandscapingDealTypeView 