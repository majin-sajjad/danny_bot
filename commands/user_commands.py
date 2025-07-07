import discord
from discord.ext import commands
import logging
from core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class UserCommands(commands.Cog):
    """User-accessible commands for Danny Bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db_manager = DatabaseManager()
    
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Check if the bot is responsive"""
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot latency: **{round(self.bot.latency * 1000)}ms**",
            color=0x00ff88
        )
        embed.set_footer(text="Danny Bot is active and ready!")
        await ctx.send(embed=embed)
    
    @commands.command(name='help_danny', aliases=['help'])
    async def help_command(self, ctx):
        """Show help information about Danny Bot"""
        embed = discord.Embed(
            title="🤖 Danny Bot - Your Sales Training Companion",
            description="Welcome to Danny Bot! Here's how to get started:",
            color=0x3498db
        )
        
        embed.add_field(
            name="🎯 Getting Started",
            value="• Click 'Begin Your Sales Journey' in #general\n• Complete your registration\n• Choose your niche/industry\n• Start training in your personal zone!",
            inline=False
        )
        
        embed.add_field(
            name="🛠️ Available Commands",
            value="• `!ping` - Check bot status\n• `!profile` - View your profile\n• `!leaderboard` - View top performers\n• `!my_zone` - Get link to your training zone",
            inline=False
        )
        
        embed.add_field(
            name="🏆 Training Features",
            value="• **Practice Arena** - Role-play scenarios\n• **Playground** - AI learning exercises\n• **Deal Submission** - Track your sales\n• **Progress Tracking** - Monitor growth",
            inline=False
        )
        
        embed.add_field(
            name="💡 Need Help?",
            value="Contact an admin or use `!support` for assistance",
            inline=False
        )
        
        embed.set_footer(text="Danny Bot - Powered by AI Sales Training")
        await ctx.send(embed=embed)
    
    @commands.command(name='profile')
    async def show_profile(self, ctx):
        """Show user's profile information"""
        user = ctx.author
        
        try:
            # Get user's preferred name
            preferred_name = await self.db_manager.get_user_preferred_name(user.id)
            if not preferred_name:
                preferred_name = user.display_name
            
            # Get registration info
            registration = await self.db_manager.get_user_registration(user.id)
            
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
            for category in ctx.guild.categories:
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
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing profile for {user.id}: {e}")
            await ctx.send("❌ Error retrieving your profile. Please try again later.")
    
    @commands.command(name='my_zone')
    async def my_training_zone(self, ctx):
        """Get a link to user's training zone"""
        user = ctx.author
        
        try:
            # Get user's preferred name
            preferred_name = await self.db_manager.get_user_preferred_name(user.id)
            if not preferred_name:
                preferred_name = user.display_name
            
            # Find their training zone
            training_zone = None
            practice_channel = None
            
            for category in ctx.guild.categories:
                if f"Training Zone - {preferred_name}" in category.name:
                    training_zone = category
                    # Find practice arena channel
                    for channel in category.channels:
                        if "💪practice-arena" in channel.name:
                            practice_channel = channel
                            break
                    break
            
            if training_zone and practice_channel:
                embed = discord.Embed(
                    title="🏠 Your Training Zone",
                    description=f"**{training_zone.name}**",
                    color=0x00ff88
                )
                
                embed.add_field(
                    name="🚀 Quick Access",
                    value=f"Jump to your practice arena: {practice_channel.mention}",
                    inline=False
                )
                
                embed.add_field(
                    name="📋 Available Channels",
                    value="• 💪 Practice Arena - Role-play training\n• 🛠️ Playground Library - AI exercises\n• 📊 My Progress - Track improvements\n• 💰 Deal Submission - Log your sales",
                    inline=False
                )
                
                embed.set_footer(text="Welcome back to your personal training space!")
                
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❓ Training Zone Not Found",
                    description="It looks like you don't have a training zone yet.",
                    color=0xff9900
                )
                embed.add_field(
                    name="🎯 Getting Started",
                    value="To create your training zone:\n1. Go to #general\n2. Click 'Begin Your Sales Journey'\n3. Complete the registration process",
                    inline=False
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error finding training zone for {user.id}: {e}")
            await ctx.send("❌ Error accessing your training zone. Please try again later.")
    
    @commands.command(name='support')
    async def support_request(self, ctx):
        """Request support from admins"""
        embed = discord.Embed(
            title="🆘 Support Request",
            description="Need help? Here are your options:",
            color=0x3498db
        )
        
        embed.add_field(
            name="👥 Contact Admins",
            value="Tag an admin or moderator in any channel for direct help",
            inline=False
        )
        
        embed.add_field(
            name="🔄 Common Solutions",
            value="• **Registration Issues:** Try clicking 'Begin Your Sales Journey' again\n• **Missing Training Zone:** Use `!my_zone` or contact admin\n• **Button Not Working:** Refresh Discord and try again",
            inline=False
        )
        
        embed.add_field(
            name="📞 Priority Support",
            value="For urgent issues, mention @Admin in your message",
            inline=False
        )
        
        embed.set_footer(text="We're here to help you succeed!")
        
        await ctx.send(embed=embed)
    
    # Leaderboard command removed - now handled by systems.leaderboard.manager
    # Users can use !leaderboard, !lb, !deal, !mystats from the leaderboard system
    
    @commands.command(name='status')
    async def server_status(self, ctx):
        """Show bot status and statistics"""
        try:
            guild = ctx.guild
            total_members = guild.member_count
            training_zones = len([cat for cat in guild.categories if "Training Zone" in cat.name])
            online_members = len([m for m in guild.members if m.status != discord.Status.offline])
            
            embed = discord.Embed(
                title="📊 Danny Bot Status",
                description="Current server statistics",
                color=0x3498db
            )
            
            embed.add_field(
                name="👥 Community",
                value=f"• **Total Members:** {total_members}\n• **Online Now:** {online_members}\n• **Training Zones:** {training_zones}",
                inline=True
            )
            
            embed.add_field(
                name="🤖 Bot Health",
                value=f"• **Latency:** {round(self.bot.latency * 1000)}ms\n• **Status:** 🟢 Online\n• **Uptime:** Available",
                inline=True
            )
            
            embed.add_field(
                name="🚀 Features Active",
                value="• ✅ Training Zones\n• ✅ Registration System\n• ✅ Practice Arena\n• ✅ Deal Tracking",
                inline=False
            )
            
            embed.set_footer(text="Danny Bot - Your AI Sales Training Partner")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing bot status: {e}")
            await ctx.send("❌ Error loading status. Please try again later.")

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(UserCommands(bot)) 