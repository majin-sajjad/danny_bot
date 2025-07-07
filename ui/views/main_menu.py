import discord
from discord.ext import commands
import logging
from typing import Optional
from ui.views.deal_submission import SmartDealSubmissionView
from ui.views.practice import PracticePersonalityView
from ui.views.playground import PlaygroundView

logger = logging.getLogger(__name__)

class ComprehensiveProgressView(discord.ui.View):
    """Comprehensive progress view for training zones"""
    
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view
    
    @discord.ui.button(label="👤 My Profile", style=discord.ButtonStyle.primary, emoji="👤", row=0, custom_id="progress_my_profile")
    async def my_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show user's profile"""
        try:
            from core.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            
            user = interaction.user
            preferred_name = await db_manager.get_user_preferred_name(user.id, user.display_name)
            registration = await db_manager.get_user_registration(user.id)
            
            embed = discord.Embed(
                title=f"👤 Profile: {preferred_name}",
                color=0x3498db
            )
            
            embed.add_field(
                name="📊 Basic Info",
                value=f"• **Discord:** {user.mention}\n• **Preferred Name:** {preferred_name}\n• **Member Since:** {user.joined_at.strftime('%B %d, %Y') if user.joined_at else 'Unknown'}",
                inline=False
            )
            
            if registration:
                embed.add_field(
                    name="🎯 Training Profile",
                    value=f"• **Industry/Niche:** {registration.get('niche', 'Not set')}\n• **Company:** {registration.get('company', 'Not set')}\n• **Registration Status:** ✅ Complete",
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚠️ Registration Status",
                    value="Not yet registered. Complete registration to access all features!",
                    inline=False
                )
            
            embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error showing profile: {e}")
            await interaction.response.send_message("❌ Error loading profile. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="📊 My Stats", style=discord.ButtonStyle.secondary, emoji="📊", row=0, custom_id="progress_my_stats")
    async def my_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show user's deal statistics"""
        try:
            from core.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            
            user = interaction.user
            # FIX: Add guild_id filtering to get accurate stats
            deals = await db_manager.get_user_deals(user.id, guild_id=interaction.guild.id)
            
            embed = discord.Embed(
                title=f"📊 Statistics for {user.display_name}",
                color=0x00ff88
            )
            
            # Calculate stats
            total_deals = len(deals)
            total_points = sum(deal.get('points_awarded', 0) for deal in deals)
            
            # Group by niche
            niche_stats = {}
            for deal in deals:
                niche = deal.get('niche', 'Unknown')
                if niche not in niche_stats:
                    niche_stats[niche] = {'deals': 0, 'points': 0}
                niche_stats[niche]['deals'] += 1
                niche_stats[niche]['points'] += deal.get('points_awarded', 0)
            
            embed.add_field(
                name="📈 Overall Statistics",
                value=f"• **Total Deals:** {total_deals}\n• **Total Points:** {total_points}\n• **Average Points per Deal:** {total_points / total_deals if total_deals > 0 else 0:.1f}",
                inline=False
            )
            
            if niche_stats:
                niche_text = ""
                for niche, stats in niche_stats.items():
                    niche_text += f"• **{niche.title()}:** {stats['deals']} deals, {stats['points']} points\n"
                
                embed.add_field(
                    name="🎯 By Niche",
                    value=niche_text,
                    inline=False
                )
            
            if total_deals == 0:
                embed.add_field(
                    name="🚀 Get Started",
                    value="Submit your first deal to start tracking your progress!",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error showing stats: {e}")
            await interaction.response.send_message("❌ Error loading stats. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="🏆 Leaderboard", style=discord.ButtonStyle.success, emoji="🏆", row=0, custom_id="progress_leaderboard")
    async def leaderboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show leaderboard"""
        try:
            # Get the leaderboard manager
            leaderboard_manager = interaction.client.get_cog('LeaderboardManager')
            if not leaderboard_manager:
                embed = discord.Embed(
                    title="❌ Leaderboard Unavailable",
                    description="Leaderboard system is currently offline. Please try again later.",
                    color=0xe74c3c
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Get current leaderboard data
            leaderboard_data = await leaderboard_manager.db.get_leaderboard_data("week", interaction.guild.id)
            
            if not leaderboard_data:
                embed = discord.Embed(
                    title="🏆 Weekly Leaderboard",
                    description="No deals submitted this week yet! Be the first to get on the leaderboard!",
                    color=0xffd700
                )
                
                embed.add_field(
                    name="🎯 How to Get Started",
                    value="• Submit deals in your deal-submission channel\n• Each deal type has different point values\n• Practice sessions also count towards ranking",
                    inline=False
                )
                
                embed.add_field(
                    name="🏅 Point System",
                    value="**🌐 Fiber:** 5 deals = 1 pt | Set/Close: 1 pt | Self-Gen: 2 pts\n**☀️ Solar:** Set/Close: 1 pt | Self-Gen: 2 pts\n**🌿 Landscaping:** Set/Close: 1 pt | Self-Gen: 2 pts + value bonuses",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create leaderboard embed
            embed = discord.Embed(
                title="🏆 Weekly Leaderboard",
                description="Current standings in the sales competition",
                color=0xffd700
            )
            
            # Add top performers
            leaderboard_text = ""
            for i, entry in enumerate(leaderboard_data[:10], 1):  # Top 10
                # Get current Discord display name
                display_name = await leaderboard_manager._get_current_discord_username(entry['user_id'], interaction.guild.id)
                
                # Trophy emoji for rankings
                trophy = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
                
                leaderboard_text += f"{trophy} **{display_name}**\n"
                leaderboard_text += f"   └ **{entry['total_points']}** points • {entry['total_deals']} deals\n"
                
                if entry['self_generated_deals'] > 0:
                    leaderboard_text += f"   └ Standard: {entry['standard_deals']} • Self-Gen: {entry['self_generated_deals']}\n"
                else:
                    leaderboard_text += f"   └ {entry['standard_deals']} standard deals\n"
                
                leaderboard_text += "\n"
            
            embed.add_field(
                name="🏅 Top Performers",
                value=leaderboard_text,
                inline=False
            )
            
            # Add user's current rank if they have deals
            user_rank = None
            for i, entry in enumerate(leaderboard_data, 1):
                if entry['user_id'] == interaction.user.id:
                    user_rank = i
                    break
            
            if user_rank:
                embed.add_field(
                    name="📊 Your Current Rank",
                    value=f"You are currently ranked **#{user_rank}** with **{leaderboard_data[user_rank-1]['total_points']}** points!",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🚀 Join the Competition",
                    value="Submit your first deal to get on the leaderboard!",
                    inline=False
                )
            
            # Get week info
            current_week = await leaderboard_manager.db.get_current_week_number(interaction.guild.id)
            embed.set_footer(text=f"Week {current_week} • Updated live with every deal submission")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error showing leaderboard: {e}")
            await interaction.response.send_message("❌ Error loading leaderboard. Please try again.", ephemeral=True)

class MainMenuView(discord.ui.View):
    """Main navigation menu for Danny Bot features"""
    
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view
    
    @discord.ui.button(label="💰 Submit Deal", style=discord.ButtonStyle.primary, emoji="💰", row=0, custom_id="main_menu_submit_deal")
    async def submit_deal(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show deal submission options"""
        try:
            # Use the smart deal submission system with dynamic stats
            deal_view = SmartDealSubmissionView()
            embed = await deal_view._create_stats_embed(interaction.user, interaction.guild.id, interaction)
            
            await interaction.response.send_message(embed=embed, view=deal_view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error showing deal submission: {e}")
            await interaction.response.send_message("❌ Error opening deal submission. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="🎯 Practice", style=discord.ButtonStyle.success, emoji="🎯", row=0, custom_id="main_menu_practice")
    async def practice(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show practice system"""
        try:
            embed = discord.Embed(
                title="🎯 Practice Arena",
                description="Practice your sales skills with AI customer personalities",
                color=0x9b59b6
            )
            
            embed.add_field(
                name="Available Personalities",
                value="• **🦉 Owl** - Analytical customers\n• **🐂 Bull** - Aggressive customers\n• **🐑 Sheep** - Passive customers\n• **🐅 Tiger** - Dominant customers",
                inline=False
            )
            
            embed.add_field(
                name="Multi-Niche Support",
                value="Practice with Fiber, Solar, and Landscaping scenarios",
                inline=False
            )
            
            # Use persistent view instance to avoid timeout issues
            view = interaction.client.persistent_practice_view
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error showing practice system: {e}")
            await interaction.response.send_message("❌ Error opening practice system. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="🚪 Playground", style=discord.ButtonStyle.secondary, emoji="🚪", row=0, custom_id="main_menu_playground")
    async def playground(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show playground system"""
        try:
            embed = discord.Embed(
                title="🚪 Lord of the Doors Season 3 - Playground Library",
                description="Create and practice with custom homeowner personalities",
                color=0x9b59b6
            )
            
            embed.add_field(
                name="🎭 What's Available",
                value="• **Create Homeowners** - Design custom personalities\n• **Practice Door Knocking** - Realistic practice scenarios\n• **Build Your Library** - Save your best homeowners",
                inline=False
            )
            
            embed.add_field(
                name="🌟 Features",
                value="• **AI-Enhanced Personalities** - Realistic homeowner behavior\n• **Multi-Niche Support** - Fiber, Solar, Landscaping\n• **Feedback System** - Rate and improve homeowners",
                inline=False
            )
            
            # Use persistent view instance to avoid timeout issues
            view = interaction.client.persistent_playground_view
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error showing playground system: {e}")
            await interaction.response.send_message("❌ Error opening playground system. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="📊 Leaderboard", style=discord.ButtonStyle.primary, emoji="📊", row=1, custom_id="main_menu_leaderboard")
    async def leaderboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show leaderboard"""
        try:
            # This will be enhanced when leaderboard system is modularized
            embed = discord.Embed(
                title="🏆 Danny Bot Leaderboard",
                description="Top performers and community rankings",
                color=0xffd700
            )
            
            embed.add_field(
                name="📊 Coming Soon",
                value="Full leaderboard with points, deals, and rankings is being prepared!",
                inline=False
            )
            
            embed.add_field(
                name="🎯 How to Climb",
                value="• Complete practice sessions\n• Submit real deals\n• Participate in challenges\n• Help other members",
                inline=False
            )
            
            embed.add_field(
                name="🏅 Current Features",
                value="• **Points System** - Earn points for deals and activities\n• **Monthly Rankings** - See top performers\n• **Progress Tracking** - Monitor your growth",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error showing leaderboard: {e}")
            await interaction.response.send_message("❌ Error opening leaderboard. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="👤 Profile", style=discord.ButtonStyle.secondary, emoji="👤", row=1, custom_id="main_menu_profile")
    async def profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show user profile and stats"""
        try:
            # Import here to avoid circular imports
            from commands.user_commands import UserCommands
            user_commands = UserCommands(None)  # Bot will be None but we don't use it in profile
            
            # Use the profile method from user commands
            user = interaction.user
            from core.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            
            # Get user data
            preferred_name = await db_manager.get_user_preferred_name(user.id)
            if not preferred_name:
                preferred_name = user.display_name
            
            registration = await db_manager.get_user_registration(user.id)
            
            embed = discord.Embed(
                title=f"👤 Profile: {preferred_name}",
                color=0x3498db
            )
            
            embed.add_field(
                name="📊 Basic Info",
                value=f"• **Discord:** {user.mention}\n• **Preferred Name:** {preferred_name}\n• **Member Since:** {user.joined_at.strftime('%B %d, %Y')}",
                inline=False
            )
            
            if registration:
                embed.add_field(
                    name="🎯 Training Profile",
                    value=f"• **Industry/Niche:** {registration.get('niche', 'Not set')}\n• **Experience Level:** {registration.get('experience', 'Not set')}\n• **Registration Status:** ✅ Complete",
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚠️ Registration Status",
                    value="Not yet registered. Click 'Begin Your Sales Journey' in #general to get started!",
                    inline=False
                )
            
            # Try to find their training zone
            training_zone = None
            for category in interaction.guild.categories:
                if f"Training Zone - {preferred_name}" in category.name:
                    training_zone = category
                    break
            
            if training_zone:
                embed.add_field(
                    name="🏠 Training Zone",
                    value=f"**{training_zone.name}**\nUse `!my_zone` to get a quick link",
                    inline=False
                )
            
            embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
            embed.set_footer(text="Use !my_zone to quickly access your training area")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error showing profile: {e}")
            await interaction.response.send_message("❌ Error loading profile. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="❓ Help", style=discord.ButtonStyle.success, emoji="❓", row=1, custom_id="main_menu_help")
    async def help_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show help and tutorial information"""
        try:
            embed = discord.Embed(
                title="❓ Danny Bot Help Center",
                description="Your guide to mastering sales with Danny Bot",
                color=0x3498db
            )
            
            embed.add_field(
                name="🎯 Getting Started",
                value="• Click 'Begin Your Sales Journey' in #general\n• Complete your registration\n• Choose your niche/industry\n• Start training in your personal zone!",
                inline=False
            )
            
            embed.add_field(
                name="🛠️ Available Commands",
                value="• `!ping` - Check bot status\n• `!profile` - View your profile\n• `!my_zone` - Get link to your training zone\n• `!support` - Get help from admins",
                inline=False
            )
            
            embed.add_field(
                name="🏆 Training Features",
                value="• **Practice Arena** - Role-play with AI personalities\n• **Playground** - Create custom homeowner scenarios\n• **Deal Submission** - Track your sales progress\n• **Leaderboard** - Compete with other members",
                inline=False
            )
            
            embed.add_field(
                name="💡 Pro Tips",
                value="• Practice regularly to improve your skills\n• Try different personality types and niches\n• Submit deals to climb the leaderboard\n• Ask questions in the community channels",
                inline=False
            )
            
            embed.set_footer(text="Danny Bot - Your AI Sales Training Partner")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error showing help: {e}")
            await interaction.response.send_message("❌ Error loading help. Please try again.", ephemeral=True) 

